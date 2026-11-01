"""Tests of the committed OpenAPI schema of the composed app."""

import json
from pathlib import Path

from app.api.main import app

OPENAPI_JSON = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def test_committed_openapi_schema_is_up_to_date() -> None:
    assert json.loads(OPENAPI_JSON.read_text(encoding="utf-8")) == app.openapi()


def test_schema_names_the_todo_paths_with_the_todos_tag() -> None:
    paths = app.openapi()["paths"]

    for path in ("/todos", "/todos/{todo_id}"):
        assert path in paths
        operations = paths[path].values()
        assert operations
        assert all("todos" in operation["tags"] for operation in operations)
