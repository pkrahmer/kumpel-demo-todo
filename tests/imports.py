"""Reads the modules a source file of the `app` package imports."""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def imported_modules(path: Path) -> set[str]:
    """Return every module the file imports, relative imports resolved, with each imported name."""
    package_parts = list(path.relative_to(SRC_DIR).parent.parts)
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
