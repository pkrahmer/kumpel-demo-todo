"""Tests that the concrete repository is chosen in the composition root only."""

from tests.imports import SRC_DIR, imported_modules

API_DIR = SRC_DIR / "app" / "api"


def _imports_repository(module: str) -> bool:
    return module == "app.repository" or module.startswith("app.repository.")


def test_only_main_imports_the_repository_layer() -> None:
    sources = sorted(API_DIR.rglob("*.py"))
    assert sources

    offending = {
        f"{path.name}: {module}"
        for path in sources
        if path != API_DIR / "main.py"
        for module in imported_modules(path)
        if _imports_repository(module)
    }

    assert offending == set()
