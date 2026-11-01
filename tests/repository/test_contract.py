from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from app.domain.errors import DuplicateTodo, TodoNotFound
from app.domain.model import Todo
from app.domain.repository import TodoRepository
from app.repository.memory import InMemoryTodoRepository

T0 = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


def _in_memory(_tmp_path: Path) -> TodoRepository:
    return InMemoryTodoRepository()


REPOSITORY_FACTORIES: list[Callable[[Path], TodoRepository]] = [_in_memory]
REPOSITORY_CLASSES: list[type[object]] = [InMemoryTodoRepository]


@pytest.fixture(params=REPOSITORY_FACTORIES, ids=lambda factory: factory.__name__)
def repository(request: pytest.FixtureRequest, tmp_path: Path) -> TodoRepository:
    factory: Callable[[Path], TodoRepository] = request.param
    return factory(tmp_path)


def _todo(n: int, *, title: str = "Buy milk", minutes: int = 0) -> Todo:
    return Todo(id=UUID(int=n), title=title, done=False, created_at=T0 + timedelta(minutes=minutes))


def test_added_todo_can_be_read_back(repository: TodoRepository) -> None:
    todo = _todo(1)

    repository.add(todo)

    assert repository.get(todo.id) == todo


def test_adding_a_stored_id_is_rejected(repository: TodoRepository) -> None:
    first = _todo(1, title="First")
    repository.add(first)

    with pytest.raises(DuplicateTodo) as excinfo:
        repository.add(_todo(1, title="Second"))

    assert excinfo.value.todo_id == first.id
    assert repository.get(first.id) == first


@pytest.mark.parametrize(
    "operation",
    [
        lambda repository: repository.get(UUID(int=9)),
        lambda repository: repository.update(_todo(9)),
        lambda repository: repository.delete(UUID(int=9)),
    ],
    ids=["get", "update", "delete"],
)
def test_unknown_id_is_not_found(
    repository: TodoRepository, operation: Callable[[TodoRepository], object]
) -> None:
    with pytest.raises(TodoNotFound) as excinfo:
        operation(repository)

    assert excinfo.value.todo_id == UUID(int=9)
    assert repository.list_all() == []


def test_empty_repository_lists_nothing(repository: TodoRepository) -> None:
    assert repository.list_all() == []


def test_todos_are_listed_oldest_first(repository: TodoRepository) -> None:
    oldest, middle, newest = _todo(3, minutes=0), _todo(1, minutes=5), _todo(2, minutes=10)
    for todo in (middle, newest, oldest):
        repository.add(todo)

    assert repository.list_all() == [oldest, middle, newest]


def test_todos_created_together_are_listed_by_id(repository: TodoRepository) -> None:
    first, second, third = _todo(1), _todo(2), _todo(3)
    for todo in (third, first, second):
        repository.add(todo)

    assert repository.list_all() == [first, second, third]


def test_update_replaces_the_stored_todo(repository: TodoRepository) -> None:
    todo = _todo(1)
    repository.add(todo)
    changed = todo.with_title("Buy oat milk").with_done(True)

    repository.update(changed)

    assert repository.get(todo.id) == changed


def test_deleted_todo_is_gone(repository: TodoRepository) -> None:
    todo = _todo(1)
    repository.add(todo)

    repository.delete(todo.id)

    with pytest.raises(TodoNotFound):
        repository.get(todo.id)


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES, ids=lambda cls: cls.__name__)
def test_repository_does_not_inherit_the_protocol(repository_class: type[object]) -> None:
    assert TodoRepository not in repository_class.__mro__
