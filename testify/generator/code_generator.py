import json
import posixpath
import re
from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from testify.llm.schemas import GeneratedTest, PageObject, TestStep


class CodeGenerator:
    def __init__(self, template_dir: Path | None = None) -> None:
        built_in_template_dir = Path(__file__).parent / "templates"
        loaders = []

        if template_dir is not None:
            loaders.append(FileSystemLoader(str(template_dir)))

        loaders.append(FileSystemLoader(str(built_in_template_dir)))

        self._env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._env.filters["ts_string"] = _ts_string

    def generate(self, test: GeneratedTest) -> dict[str, str]:
        """Render a GeneratedTest into relative file paths and code strings."""
        framework = test.framework.lower()
        if framework not in {"playwright", "cypress"}:
            raise ValueError(f"Unsupported test framework: {test.framework}")

        pages = [_build_page_context(page, test.filename) for page in test.page_objects or []]
        selector_lookup = _selector_lookup(pages)
        context = {
            "test": test,
            "pages": pages,
            "playwright_step": lambda step: _playwright_step(step, selector_lookup),
            "cypress_step": _cypress_step,
            "playwright_assertion": _playwright_assertion,
            "cypress_assertion": _cypress_assertion,
        }

        files = {
            test.filename: self._render_template(f"{framework}_spec.jinja2", context),
        }

        for page in pages:
            files[page["file_path"]] = self._render_template(
                f"{framework}_page.jinja2",
                {"page": page},
            )

        return files

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        return self._env.get_template(template_name).render(**context).strip() + "\n"


def _build_page_context(page_object: PageObject, spec_filename: str) -> dict[str, Any]:
    base_name = _page_base_name(page_object.name)
    file_path = f"pages/{base_name}.page.ts"
    selectors = [
        {
            "property_name": _identifier(name),
            "original_name": name,
            "value": _data_testid_selector(selector),
        }
        for name, selector in page_object.selectors.items()
    ]

    return {
        "class_name": page_object.name,
        "variable_name": _lower_camel(page_object.name),
        "file_path": file_path,
        "import_path": _import_path(spec_filename, file_path),
        "route": f"/{base_name}",
        "selectors": selectors,
    }


def _selector_lookup(pages: list[dict[str, Any]]) -> dict[str, str]:
    lookup = {}
    for page in pages:
        for selector in page["selectors"]:
            lookup[selector["value"]] = f"{page['variable_name']}.{selector['property_name']}"
    return lookup


def _import_path(from_file: str, to_file: str) -> str:
    from_dir = posixpath.dirname(from_file) or "."
    target = posixpath.splitext(to_file)[0]
    relative = posixpath.relpath(target, start=from_dir)
    if not relative.startswith("."):
        return f"./{relative}"
    return relative


def _playwright_step(step: TestStep, selector_lookup: dict[str, str]) -> str:
    action = step.action.lower()

    if action == "navigate":
        return f"await page.goto({_ts_string(step.value or '/')});"

    target = _playwright_target(step, selector_lookup)
    if step.value:
        return f"await {target}.fill({_ts_string(step.value)});"
    if "click" in action:
        return f"await {target}.click();"
    if step.assertion:
        return _playwright_assertion(step.assertion)

    return f"await {target}.click();"


def _playwright_target(step: TestStep, selector_lookup: dict[str, str]) -> str:
    selector = _data_testid_selector(step.selector or _slug(step.action))
    if selector in selector_lookup:
        return selector_lookup[selector]
    return f"page.locator({_ts_string(selector)})"


def _cypress_step(step: TestStep) -> str:
    action = step.action.lower()

    if action == "navigate":
        return f"cy.visit({_ts_string(step.value or '/')});"

    selector = _data_testid_selector(step.selector or _slug(step.action))
    if step.value:
        return f"cy.get({_ts_string(selector)}).type({_ts_string(step.value)});"
    if "click" in action:
        return f"cy.get({_ts_string(selector)}).click();"
    if step.assertion:
        return _cypress_assertion(step.assertion)

    return f"cy.get({_ts_string(selector)}).click();"


def _playwright_assertion(assertion: str) -> str:
    cleaned = assertion.strip()
    if cleaned.startswith(("await expect(", "expect(", "await page.", "page.")):
        return _with_semicolon(cleaned)
    return f"await expect(page.locator('body')).toContainText({_ts_string(cleaned)});"


def _cypress_assertion(assertion: str) -> str:
    cleaned = assertion.strip()
    if cleaned.startswith("cy."):
        return _with_semicolon(cleaned)
    return f"cy.get('body').should('contain', {_ts_string(cleaned)});"


def _with_semicolon(code: str) -> str:
    return code if code.endswith(";") else f"{code};"


def _data_testid_selector(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("["):
        return cleaned
    if cleaned.startswith("data-testid="):
        return f"[{cleaned}]"
    return f'[data-testid="{_slug(cleaned)}"]'


def _page_base_name(class_name: str) -> str:
    without_suffix = re.sub(r"Page$", "", class_name)
    return _slug(without_suffix)


def _lower_camel(value: str) -> str:
    identifier = _identifier(value)
    return identifier[:1].lower() + identifier[1:]


def _identifier(value: str) -> str:
    parts = _words(value)
    if not parts:
        return "element"

    identifier = parts[0].lower() + "".join(part.capitalize() for part in parts[1:])
    if identifier[0].isdigit():
        return f"element{identifier}"
    return identifier


def _slug(value: str) -> str:
    words = _words(value)
    return "-".join(word.lower() for word in words) or "element"


def _words(value: str) -> list[str]:
    return re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[0-9]+", value)


def _ts_string(value: str) -> str:
    return json.dumps(value)
