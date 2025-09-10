from testify.generator.code_generator import CodeGenerator
from testify.llm.schemas import GeneratedTest, PageObject
from testify.llm.schemas import TestScenario as ScenarioModel
from testify.llm.schemas import TestStep as StepModel


def test_generate_playwright_spec() -> None:
    files = CodeGenerator().generate(_generated_test("playwright", "login.spec.ts"))

    code = files["login.spec.ts"]
    assert "import { test, expect } from '@playwright/test';" in code
    assert 'test.describe("Authentication"' in code
    assert 'test("User logs in"' in code
    assert "async ({ page })" in code
    assert 'page.locator("[data-testid=\\"email\\"]")' in code
    assert "await expect(page.locator('body')).toContainText(\"Dashboard is visible\");" in code


def test_generate_cypress_spec() -> None:
    files = CodeGenerator().generate(_generated_test("cypress", "login.cy.ts"))

    code = files["login.cy.ts"]
    assert 'describe("Authentication"' in code
    assert 'it("User logs in"' in code
    assert "cy.visit('/');" in code
    assert 'cy.get("[data-testid=\\"email\\"]")' in code
    assert '.type("valid_user")' in code
    assert "cy.get('body').should('contain', \"Dashboard is visible\");" in code


def test_generate_with_page_objects() -> None:
    test = _generated_test("playwright", "tests/login.spec.ts")
    test.page_objects = [
        PageObject(
            name="LoginPage",
            selectors={"email": '[data-testid="email"]', "submit button": '[data-testid="submit"]'},
        )
    ]

    files = CodeGenerator().generate(test)

    assert "tests/login.spec.ts" in files
    assert "pages/login.page.ts" in files
    assert "import { LoginPage } from '../pages/login.page';" in files["tests/login.spec.ts"]
    assert "const loginPage = new LoginPage(page);" in files["tests/login.spec.ts"]
    assert "export class LoginPage" in files["pages/login.page.ts"]
    assert "readonly email" in files["pages/login.page.ts"]
    assert 'page.locator("[data-testid=\\"email\\"]")' in files["pages/login.page.ts"]


def test_page_object_import_path_for_root_spec() -> None:
    test = _generated_test("playwright", "login.spec.ts")
    test.page_objects = [PageObject(name="LoginPage", selectors={"email": '[data-testid="email"]'})]

    files = CodeGenerator().generate(test)

    assert "import { LoginPage } from './pages/login.page';" in files["login.spec.ts"]


def test_custom_template_overrides_built_in(tmp_path) -> None:
    template = tmp_path / "playwright_spec.jinja2"
    template.write_text("custom {{ test.filename }}", encoding="utf-8")

    files = CodeGenerator(template_dir=tmp_path).generate(
        _generated_test("playwright", "login.spec.ts")
    )

    assert files["login.spec.ts"] == "custom login.spec.ts\n"


def _generated_test(framework: str, filename: str) -> GeneratedTest:
    return GeneratedTest(
        filename=filename,
        framework=framework,
        language="typescript",
        describe_block="Authentication",
        imports=[],
        scenarios=[
            ScenarioModel(
                name="User logs in",
                description="User logs in with valid credentials",
                steps=[
                    StepModel(action="navigate", value="/login"),
                    StepModel(
                        action="fill email",
                        selector='[data-testid="email"]',
                        value="valid_user",
                    ),
                    StepModel(action="click", selector='[data-testid="submit"]'),
                ],
                assertions=["Dashboard is visible"],
                page="Login",
                test_data={"email": "valid_user"},
            )
        ],
    )
