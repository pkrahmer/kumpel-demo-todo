from tests.imports import SRC_DIR, imported_modules

DOMAIN_DIR = SRC_DIR / "app" / "domain"
FORBIDDEN_FRAMEWORKS = {"fastapi", "pydantic", "sqlalchemy"}


def _is_forbidden(module: str) -> bool:
    top = module.split(".", maxsplit=1)[0]
    if top in FORBIDDEN_FRAMEWORKS:
        return True
    in_domain = module == "app.domain" or module.startswith("app.domain.")
    return top == "app" and module != "app" and not in_domain


def test_domain_imports_no_framework_and_no_other_app_layer() -> None:
    sources = sorted(DOMAIN_DIR.rglob("*.py"))
    assert sources

    offending = {
        f"{path.name}: {module}"
        for path in sources
        for module in imported_modules(path)
        if _is_forbidden(module)
    }

    assert offending == set()
