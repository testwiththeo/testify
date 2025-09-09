from pydantic import BaseModel


class TestStep(BaseModel):
    action: str
    selector: str | None = None
    value: str | None = None
    assertion: str | None = None


class TestScenario(BaseModel):
    name: str
    description: str
    steps: list[TestStep]
    assertions: list[str]
    page: str | None = None
    test_data: dict[str, str] | None = None


class PageObject(BaseModel):
    name: str
    selectors: dict[str, str]


class GeneratedTest(BaseModel):
    filename: str
    framework: str
    language: str = "typescript"
    describe_block: str
    scenarios: list[TestScenario]
    imports: list[str]
    page_objects: list[PageObject] | None = None
