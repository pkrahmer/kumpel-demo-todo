"""Tests of the todo endpoints, through the test client against `create_app`."""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import TodoService
from tests.fakes import ticking_clock

UNKNOWN_ID = UUID(int=404)
TODO_KEYS = {"id", "title", "done", "created_at"}


@pytest.fixture
def service() -> TodoService:
    return TodoService(InMemoryTodoRepository(), clock=ticking_clock())


@pytest.fixture
def client(service: TodoService) -> TestClient:
    return TestClient(create_app(service))


def _create(client: TestClient, title: str) -> str:
    response = client.post("/todos", json={"title": title})
    assert response.status_code == 201
    todo_id: str = response.json()["id"]
    return todo_id


def _assert_only_detail(body: object) -> str:
    assert isinstance(body, dict)
    assert set(body) == {"detail"}
    detail = body["detail"]
    assert isinstance(detail, str)
    return detail


def test_create_returns_the_new_open_todo(client: TestClient) -> None:
    response = client.post("/todos", json={"title": "Buy milk"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == TODO_KEYS
    UUID(body["id"])
    assert body["title"] == "Buy milk"
    assert body["done"] is False
    created_at: str = body["created_at"]
    assert created_at.endswith(("Z", "+00:00"))
    assert datetime.fromisoformat(created_at).utcoffset() == timedelta(0)


def test_create_strips_the_title(client: TestClient) -> None:
    response = client.post("/todos", json={"title": "  Buy milk "})

    assert response.status_code == 201
    assert response.json()["title"] == "Buy milk"


def test_create_with_a_blank_title_is_rejected(client: TestClient) -> None:
    response = client.post("/todos", json={"title": "   "})

    assert response.status_code == 422
    assert response.json() == {"detail": "title must not be blank"}


@pytest.mark.parametrize(
    ("length", "status", "body"),
    [
        (200, 201, None),
        (201, 422, {"detail": "title must be at most 200 characters"}),
    ],
)
def test_create_enforces_the_title_length_limit(
    client: TestClient, length: int, status: int, body: dict[str, str] | None
) -> None:
    response = client.post("/todos", json={"title": "x" * length})

    assert response.status_code == status
    if body is not None:
        assert response.json() == body


def test_create_without_a_title_names_the_missing_field(client: TestClient) -> None:
    response = client.post("/todos", json={})

    assert response.status_code == 422
    assert response.json() == {"detail": "body.title: Field required"}


def test_list_returns_every_todo_in_creation_order(client: TestClient) -> None:
    ids = [_create(client, title) for title in ("first", "second", "third")]

    response = client.get("/todos")

    assert response.status_code == 200
    assert [todo["id"] for todo in response.json()] == ids


@pytest.mark.parametrize(
    ("done", "expected_titles"),
    [
        ("true", ["done one", "done two"]),
        ("false", ["open one", "open two"]),
    ],
)
def test_list_filters_by_done(client: TestClient, done: str, expected_titles: list[str]) -> None:
    for title in ("open one", "done one", "open two", "done two"):
        todo_id = _create(client, title)
        if title.startswith("done"):
            assert client.patch(f"/todos/{todo_id}", json={"done": True}).status_code == 200

    response = client.get("/todos", params={"done": done})

    assert response.status_code == 200
    assert [todo["title"] for todo in response.json()] == expected_titles


def test_list_with_an_invalid_done_filter_is_rejected(client: TestClient) -> None:
    response = client.get("/todos", params={"done": "maybe"})

    assert response.status_code == 422
    assert _assert_only_detail(response.json()).startswith("query.done: ")


def test_get_returns_the_known_todo(client: TestClient) -> None:
    created = client.post("/todos", json={"title": "Buy milk"}).json()

    response = client.get(f"/todos/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


@pytest.mark.parametrize(
    ("method", "body"),
    [("GET", None), ("PATCH", {"done": True}), ("DELETE", None)],
)
def test_an_id_that_is_not_a_uuid_is_rejected(
    client: TestClient, method: str, body: dict[str, bool] | None
) -> None:
    response = client.request(method, "/todos/not-a-uuid", json=body)

    assert response.status_code == 422
    assert _assert_only_detail(response.json()).startswith("path.todo_id: ")


def test_patch_done_completes_and_reopens_the_todo(client: TestClient) -> None:
    todo_id = _create(client, "Buy milk")

    completed = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert completed.status_code == 200
    assert completed.json()["done"] is True

    reopened = client.patch(f"/todos/{todo_id}", json={"done": False})
    assert reopened.status_code == 200
    assert reopened.json()["done"] is False


def test_patch_title_renames_the_todo_and_keeps_the_rest(client: TestClient) -> None:
    before = client.post("/todos", json={"title": "Old title"}).json()

    response = client.patch(f"/todos/{before['id']}", json={"title": " New title "})

    assert response.status_code == 200
    assert response.json() == {**before, "title": "New title"}


@pytest.mark.parametrize(
    "body",
    [{}, {"title": None}, {"done": None}, {"title": None, "done": None}],
)
def test_patch_that_sets_no_field_is_rejected_and_changes_nothing(
    client: TestClient, body: dict[str, None]
) -> None:
    todo_id = _create(client, "Buy milk")
    before = client.get(f"/todos/{todo_id}").json()

    response = client.patch(f"/todos/{todo_id}", json=body)

    assert response.status_code == 422
    _assert_only_detail(response.json())
    assert client.get(f"/todos/{todo_id}").json() == before


def test_patch_with_a_blank_title_changes_nothing(client: TestClient) -> None:
    todo_id = _create(client, "Old title")

    response = client.patch(f"/todos/{todo_id}", json={"title": "   ", "done": True})

    assert response.status_code == 422
    assert response.json() == {"detail": "title must not be blank"}
    after = client.get(f"/todos/{todo_id}").json()
    assert after["title"] == "Old title"
    assert after["done"] is False


def test_patch_title_and_done_applies_both(client: TestClient) -> None:
    before = client.post("/todos", json={"title": "Old title"}).json()
    expected = {**before, "title": "New title", "done": True}

    response = client.patch(f"/todos/{before['id']}", json={"title": " New title ", "done": True})

    assert response.status_code == 200
    assert response.json() == expected
    assert client.get(f"/todos/{before['id']}").json() == expected


@pytest.mark.parametrize(
    ("body", "changes"),
    [
        ({"title": None, "done": True}, {"done": True}),
        ({"title": " New title ", "done": None}, {"title": "New title", "done": False}),
    ],
)
def test_patch_ignores_a_null_field_beside_a_set_one(
    client: TestClient, body: dict[str, object], changes: dict[str, object]
) -> None:
    before = client.post("/todos", json={"title": "Old title"}).json()
    expected = {**before, **changes}

    response = client.patch(f"/todos/{before['id']}", json=body)

    assert response.status_code == 200
    assert response.json() == expected
    assert client.get(f"/todos/{before['id']}").json() == expected


def test_delete_removes_the_todo(client: TestClient) -> None:
    todo_id = _create(client, "Buy milk")

    response = client.delete(f"/todos/{todo_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/todos/{todo_id}").status_code == 404


@pytest.mark.parametrize(
    ("method", "body"),
    [("GET", None), ("PATCH", {"done": True}), ("DELETE", None)],
)
def test_an_unknown_id_is_not_found(
    client: TestClient, method: str, body: dict[str, bool] | None
) -> None:
    response = client.request(method, f"/todos/{UNKNOWN_ID}", json=body)

    assert response.status_code == 404
    assert response.json() == {"detail": f"todo {UNKNOWN_ID} not found"}


def test_routes_use_the_service_given_to_create_app(
    client: TestClient, service: TodoService
) -> None:
    todo = service.create("Buy milk")

    response = client.get("/todos")

    assert [item["id"] for item in response.json()] == [str(todo.id)]


def test_the_api_is_called_todo_service(service: TodoService) -> None:
    assert create_app(service).openapi()["info"]["title"] == "Todo service"


def test_each_app_lists_only_the_todos_of_its_own_service() -> None:
    first_service = TodoService(InMemoryTodoRepository(), clock=ticking_clock())
    second_service = TodoService(InMemoryTodoRepository(), clock=ticking_clock())
    first_todo = first_service.create("first")
    second_todo = second_service.create("second")

    first_body = TestClient(create_app(first_service)).get("/todos").json()
    second_body = TestClient(create_app(second_service)).get("/todos").json()

    assert [item["id"] for item in first_body] == [str(first_todo.id)]
    assert [item["id"] for item in second_body] == [str(second_todo.id)]


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/todos", {"title": "   "}),
        ("POST", "/todos", {}),
        ("GET", "/todos?done=maybe", None),
        ("GET", "/todos/not-a-uuid", None),
        ("PATCH", "/todos/not-a-uuid", {"done": True}),
        ("DELETE", "/todos/not-a-uuid", None),
        ("GET", f"/todos/{UNKNOWN_ID}", None),
        ("PATCH", f"/todos/{UNKNOWN_ID}", {"done": True}),
        ("DELETE", f"/todos/{UNKNOWN_ID}", None),
    ],
)
def test_every_error_body_has_detail_as_its_only_key(
    client: TestClient, method: str, path: str, body: dict[str, object] | None
) -> None:
    response = client.request(method, path, json=body)

    assert response.status_code >= 400
    _assert_only_detail(response.json())
