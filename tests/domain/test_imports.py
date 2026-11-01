import ast
from pathlib import Path

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "src" / "app" / "domain"
FORBIDDEN_FRAMEWORKS = {"fastapi", "pydantic", "sqlalchemy"}


def _imported_modules(path: Path) -> set[str]:
    package_parts = ["app", "domain", *path.relative_to(DOMAIN_DIR).parent.parts]
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                prefix = ".".join(package_parts[: len(package_parts) - node.level + 1])
                base_module = f"{prefix}.{node.module}" if node.module else prefix
            else:
                base_module = node.module or ""
            modules.add(base_module)
            modules.update(f"{base_module}.{alias.name}" for alias in node.names)
    return modules


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
        for module in _imported_modules(path)
        if _is_forbidden(module)
    }

    assert offending == set()
