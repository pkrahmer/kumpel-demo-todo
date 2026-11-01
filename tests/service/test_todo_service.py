"""Tests of the todo use cases, run against the in-memory repository."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domain.errors import InvalidTitle, TodoNotFound
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import Clock, TodoService, utc_now
from tests.fakes import T0

UNKNOWN_ID = UUID(int=404)


def _fixed_clock() -> datetime:
    return T0


def _ticking_clock() -> Clock:
    ticks = 0

    def clock() -> datetime:
        nonlocal ticks
        ticks += 1
        return T0 + timedelta(minutes=ticks)

    return clock


@pytest.fixture
def service() -> TodoService:
    return TodoService(InMemoryTodoRepository(), clock=_fixed_clock)


@pytest.fixture
def ticking_service() -> TodoService:
    return TodoService(InMemoryTodoRepository(), clock=_ticking_clock())


def _assert_now_in_utc(moment: datetime) -> None:
    assert moment.tzinfo is not None
    assert moment.utcoffset() == timedelta(0)
    assert abs(datetime.now(UTC) - moment) <= timedelta(seconds=1)


def test_create_strips_the_title_and_stamps_the_clock_time(service: TodoService) -> None:
    todo = service.create("  Buy milk ")

    assert todo.title == "Buy milk"
    assert todo.done is False
    assert todo.created_at == T0
    assert service.get(todo.id) == todo


def test_create_with_a_blank_title_is_rejected_and_stores_nothing(service: TodoService) -> None:
    with pytest.raises(InvalidTitle):
        service.create("   ")

    assert service.list() == []


def test_get_with_an_unknown_id_raises_not_found(service: TodoService) -> None:
    with pytest.raises(TodoNotFound) as raised:
        service.get(UNKNOWN_ID)

    assert raised.value.todo_id == UNKNOWN_ID


def test_list_returns_every_todo_in_creation_order(ticking_service: TodoService) -> None:
    created = [ticking_service.create(title) for title in ("First", "Second", "Third")]

    assert ticking_service.list() == created


@pytest.mark.parametrize(
    ("done", "expected_titles"),
    [
        (True, ["Done one", "Done two"]),
        (False, ["Open one", "Open two"]),
        (None, ["Done one", "Open one", "Done two", "Open two"]),
    ],
)
def test_list_filters_by_the_done_flag_in_creation_order(
    ticking_service: TodoService, done: bool | None, expected_titles: list[str]
) -> None:
    for title in ("Done one", "Open one", "Done two", "Open two"):
        todo = ticking_service.create(title)
        if title.startswith("Done"):
            ticking_service.complete(todo.id)

    assert [todo.title for todo in ticking_service.list(done=done)] == expected_titles


def test_rename_changes_only_the_title(service: TodoService) -> None:
    original = service.complete(service.create("Buy milk").id)

    renamed = service.rename(original.id, "  Buy oat milk ")

    assert renamed.title == "Buy oat milk"
    assert renamed.id == original.id
    assert renamed.done == original.done
    assert renamed.created_at == original.created_at
    assert service.get(original.id) == renamed


def test_rename_with_a_blank_title_is_rejected_and_keeps_the_old_title(
    service: TodoService,
) -> None:
    todo = service.create("Buy milk")

    with pytest.raises(InvalidTitle):
        service.rename(todo.id, "   ")

    assert service.get(todo.id).title == "Buy milk"


def test_complete_marks_the_todo_done(service: TodoService) -> None:
    todo = service.create("Buy milk")

    completed = service.complete(todo.id)

    assert completed.done is True
    assert service.get(todo.id).done is True


def test_complete_on_a_completed_todo_keeps_it_done(service: TodoService) -> None:
    todo = service.create("Buy milk")
    service.complete(todo.id)

    again = service.complete(todo.id)

    assert again.id == todo.id
    assert again.done is True


def test_reopen_marks_the_todo_open(service: TodoService) -> None:
    todo = service.create("Buy milk")
    service.complete(todo.id)

    reopened = service.reopen(todo.id)

    assert reopened.done is False
    assert service.get(todo.id).done is False


def test_reopen_on_an_open_todo_keeps_it_open(service: TodoService) -> None:
    todo = service.create("Buy milk")

    again = service.reopen(todo.id)

    assert again.id == todo.id
    assert again.done is False


def test_delete_removes_the_todo(service: TodoService) -> None:
    todo = service.create("Buy milk")

    service.delete(todo.id)

    with pytest.raises(TodoNotFound):
        service.get(todo.id)


@pytest.mark.parametrize(
    "operation",
    [
        lambda service, todo_id: service.rename(todo_id, "Buy milk"),
        lambda service, todo_id: service.complete(todo_id),
        lambda service, todo_id: service.reopen(todo_id),
        lambda service, todo_id: service.delete(todo_id),
    ],
    ids=["rename", "complete", "reopen", "delete"],
)
def test_changing_an_unknown_todo_raises_not_found(
    service: TodoService, operation: Callable[[TodoService, UUID], object]
) -> None:
    with pytest.raises(TodoNotFound) as raised:
        operation(service, UNKNOWN_ID)

    assert raised.value.todo_id == UNKNOWN_ID


def test_utc_now_is_the_current_time_in_utc() -> None:
    _assert_now_in_utc(utc_now())


def test_service_without_a_clock_stamps_the_current_utc_time() -> None:
    todo = TodoService(InMemoryTodoRepository()).create("Buy milk")

    _assert_now_in_utc(todo.created_at)
