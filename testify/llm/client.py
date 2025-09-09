import json
import time
from typing import Any

from openai import APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, OpenAI
from pydantic import ValidationError
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from testify.llm.config import LLMConfig
from testify.llm.schemas import GeneratedTest
from testify.parser import ScenarioInput


class LLMClientError(RuntimeError):
    """Base error for LLM client failures."""


class LLMAuthenticationError(LLMClientError):
    """Raised when the LLM provider rejects credentials."""


class LLMBadRequestError(LLMClientError):
    """Raised when the LLM provider rejects the request payload."""


class LLMGenerationError(LLMClientError):
    """Raised when generation fails after retries."""


class InvalidLLMResponseError(LLMClientError):
    """Raised when an LLM response cannot be parsed into the schema."""


class LLMClient:
    def __init__(
        self,
        config: LLMConfig | None = None,
        openai_client: Any | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self.config = config or LLMConfig.from_env()
        self._openai_client = openai_client
        self._sleep = sleep

    def generate_test(self, scenario: ScenarioInput, framework: str) -> GeneratedTest:
        """Generate structured test data for one scenario."""
        if self.config.provider != "openai":
            raise LLMClientError(f"Unsupported LLM provider: {self.config.provider}")

        try:
            retryer = Retrying(
                retry=retry_if_exception(_is_retryable_error),
                wait=wait_exponential(multiplier=2, min=2, max=8),
                stop=stop_after_attempt(self.config.max_retries + 1),
                sleep=self._sleep,
                reraise=True,
            )
            return retryer(self._request_and_parse, scenario, framework)
        except Exception as exc:
            if _is_auth_error(exc):
                raise LLMAuthenticationError(
                    "LLM authentication failed. Set TESTIFY_LLM_API_KEY or OPENAI_API_KEY."
                ) from exc
            if _is_bad_request_error(exc):
                raise LLMBadRequestError(f"LLM request was rejected: {exc}") from exc
            if _is_retryable_error(exc):
                raise LLMGenerationError(
                    f"LLM generation failed after {self.config.max_retries + 1} attempts: {exc}"
                ) from exc
            raise LLMClientError(f"LLM request failed: {exc}") from exc

    def _request_and_parse(self, scenario: ScenarioInput, framework: str) -> GeneratedTest:
        response = self._get_openai_client().chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt(framework)},
                {"role": "user", "content": self._build_user_prompt(scenario, framework)},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )

        try:
            content = response.choices[0].message.content
            if content is None:
                raise InvalidLLMResponseError("LLM returned an empty response.")
            return GeneratedTest.model_validate_json(content)
        except (IndexError, AttributeError, json.JSONDecodeError, ValidationError) as exc:
            message = f"LLM returned invalid JSON for {scenario.text!r}."
            raise InvalidLLMResponseError(message) from exc

    def _get_openai_client(self) -> Any:
        if self._openai_client is not None:
            return self._openai_client

        if not self.config.api_key:
            raise LLMAuthenticationError(
                "OpenAI API key is required. Set TESTIFY_LLM_API_KEY or OPENAI_API_KEY."
            )

        self._openai_client = OpenAI(api_key=self.config.api_key, timeout=self.config.timeout)
        return self._openai_client

    def _build_system_prompt(self, framework: str) -> str:
        return (
            f"You are an expert QA engineer who writes clean, idiomatic {framework} tests. "
            "Given an acceptance criterion, generate a complete test with proper assertions. "
            "Return ONLY valid JSON matching the provided schema. No explanations, no markdown."
        )

    def _build_user_prompt(self, scenario: ScenarioInput, framework: str) -> str:
        schema = json.dumps(GeneratedTest.model_json_schema(), indent=2)
        return (
            f"Framework: {framework}\n"
            f"Acceptance Criterion: {scenario.text}\n\n"
            "Generate test code with:\n"
            "1. A descriptive test name\n"
            "2. Step-by-step actions with selectors\n"
            "3. Clear assertions\n"
            "4. Page objects if a page/screen is mentioned\n\n"
            'Use data-testid selectors like: [data-testid="element-name"]\n\n'
            f"JSON schema:\n{schema}"
        )


def _is_retryable_error(exc: BaseException) -> bool:
    return isinstance(exc, InvalidLLMResponseError) or _is_optional_instance(
        exc, APITimeoutError, APIConnectionError
    )


def _is_auth_error(exc: BaseException) -> bool:
    return _is_optional_instance(exc, AuthenticationError)


def _is_bad_request_error(exc: BaseException) -> bool:
    return _is_optional_instance(exc, BadRequestError)


def _is_optional_instance(exc: BaseException, *classes: Any) -> bool:
    return any(error_class is not None and isinstance(exc, error_class) for error_class in classes)
