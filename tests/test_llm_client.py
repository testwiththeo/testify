import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import vcr

import testify.llm.client as client_module
from testify.llm import (
    GeneratedTest,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMClient,
    LLMConfig,
    LLMGenerationError,
)
from testify.parser import ScenarioInput

CASSETTE_DIR = Path(__file__).parent / "cassettes"


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return _openai_response(response)


class FakeOpenAIClient:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeTimeoutError(Exception):
    pass


class FakeAuthError(Exception):
    pass


class FakeBadRequestError(Exception):
    pass


def test_successful_generation_returns_valid_generated_test() -> None:
    fake_client = FakeOpenAIClient([_valid_generated_test_json()])
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=lambda _: None,
    )
    scenario = ScenarioInput(text="User logs in", source="argument")

    with vcr.use_cassette(str(CASSETTE_DIR / "llm_success.yaml"), record_mode="none"):
        generated = client.generate_test(scenario, "playwright")

    assert isinstance(generated, GeneratedTest)
    assert generated.filename == "login.spec.ts"
    assert generated.framework == "playwright"
    assert generated.scenarios[0].steps[0].selector == '[data-testid="email"]'
    request = fake_client.completions.calls[0]
    assert request["model"] == "gpt-4o-mini"
    assert request["temperature"] == 0.2
    assert "User logs in" in request["messages"][1]["content"]


def test_retry_on_timeout(monkeypatch) -> None:
    monkeypatch.setattr(client_module, "APITimeoutError", FakeTimeoutError)
    fake_client = FakeOpenAIClient([FakeTimeoutError("timeout"), _valid_generated_test_json()])
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=lambda _: None,
    )

    generated = client.generate_test(
        ScenarioInput(text="User logs in", source="argument"), "playwright"
    )

    assert generated.filename == "login.spec.ts"
    assert len(fake_client.completions.calls) == 2


def test_retry_on_invalid_json() -> None:
    fake_client = FakeOpenAIClient(["not-json", _valid_generated_test_json()])
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=lambda _: None,
    )

    generated = client.generate_test(
        ScenarioInput(text="User logs in", source="argument"), "playwright"
    )

    assert generated.filename == "login.spec.ts"
    assert len(fake_client.completions.calls) == 2


def test_invalid_json_raises_after_retries() -> None:
    fake_client = FakeOpenAIClient(["not-json", "still-not-json", "bad", "bad-again"])
    sleeps = []
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=sleeps.append,
    )

    with pytest.raises(LLMGenerationError, match="failed after 4 attempts"):
        client.generate_test(ScenarioInput(text="User logs in", source="argument"), "playwright")

    assert len(fake_client.completions.calls) == 4
    assert sleeps == [2.0, 4.0, 8.0]


def test_auth_error_is_not_retried(monkeypatch) -> None:
    monkeypatch.setattr(client_module, "AuthenticationError", FakeAuthError)
    fake_client = FakeOpenAIClient([FakeAuthError("bad key"), _valid_generated_test_json()])
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=lambda _: None,
    )

    with pytest.raises(LLMAuthenticationError, match="TESTIFY_LLM_API_KEY"):
        client.generate_test(ScenarioInput(text="User logs in", source="argument"), "playwright")

    assert len(fake_client.completions.calls) == 1


def test_bad_request_error_is_not_retried(monkeypatch) -> None:
    monkeypatch.setattr(client_module, "BadRequestError", FakeBadRequestError)
    fake_client = FakeOpenAIClient(
        [FakeBadRequestError("bad request"), _valid_generated_test_json()]
    )
    client = LLMClient(
        config=LLMConfig(api_key="test-key"),
        openai_client=fake_client,
        sleep=lambda _: None,
    )

    with pytest.raises(LLMBadRequestError, match="rejected"):
        client.generate_test(ScenarioInput(text="User logs in", source="argument"), "playwright")

    assert len(fake_client.completions.calls) == 1


def test_config_loads_from_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("TESTIFY_LLM_PROVIDER", "openai")
    monkeypatch.setenv("TESTIFY_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("TESTIFY_LLM_API_KEY", "testify-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    config = LLMConfig.from_env()

    assert config.provider == "openai"
    assert config.model == "gpt-4o"
    assert config.api_key == "testify-key"


def test_config_falls_back_to_openai_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TESTIFY_LLM_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    config = LLMConfig.from_env()

    assert config.api_key == "openai-key"


def _openai_response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def _valid_generated_test_json() -> str:
    return json.dumps(
        {
            "filename": "login.spec.ts",
            "framework": "playwright",
            "language": "typescript",
            "describe_block": "Authentication",
            "imports": ["import { test, expect } from '@playwright/test';"],
            "scenarios": [
                {
                    "name": "User logs in",
                    "description": "User logs in with valid credentials",
                    "steps": [
                        {
                            "action": "fill email",
                            "selector": '[data-testid="email"]',
                            "value": "valid_user",
                        }
                    ],
                    "assertions": ["Dashboard is visible"],
                    "page": "Login",
                    "test_data": {"email": "valid_user"},
                }
            ],
            "page_objects": [
                {
                    "name": "LoginPage",
                    "selectors": {"email": '[data-testid="email"]'},
                }
            ],
        }
    )
