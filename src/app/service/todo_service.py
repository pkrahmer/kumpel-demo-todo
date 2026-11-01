"""The todo use cases: create, read, list, rename, complete, reopen and delete."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from app.domain.model import Todo
from app.domain.repository import TodoRepository

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Return the current time, timezone-aware in UTC."""
    return datetime.now(UTC)


class TodoService:
    """Runs the todo use cases against a repository, stamping new todos with its clock."""

    def __init__(self, repository: TodoRepository, clock: Clock = utc_now) -> None:
        """Use `repository` for storage and `clock` for creation times."""
        self._repository = repository
        self._clock = clock

    def create(self, title: str) -> Todo:
        """Store and return a new open todo; raise `InvalidTitle` for a title the domain refuses."""
        todo = Todo.new(title, now=self._clock())
        self._repository.add(todo)
        return todo

    def get(self, todo_id: UUID) -> Todo:
        """Return the todo with `todo_id`; raise `TodoNotFound` if there is none."""
        return self._repository.get(todo_id)

    def list(self, *, done: bool | None = None) -> list[Todo]:
        """Return the todos in creation order, only those whose done flag is `done` unless None."""
        todos = self._repository.list_all()
        if done is None:
            return todos
        return [todo for todo in todos if todo.done is done]

    def rename(self, todo_id: UUID, title: str) -> Todo:
        """Give the todo a new title and return it; raise `InvalidTitle` or `TodoNotFound`."""
        return self._save(self.get(todo_id).with_title(title))

    def complete(self, todo_id: UUID) -> Todo:
        """Mark the todo done and return it; a completed todo stays done."""
        return self._save(self.get(todo_id).with_done(True))

    def reopen(self, todo_id: UUID) -> Todo:
        """Mark the todo open and return it; an open todo stays open."""
        return self._save(self.get(todo_id).with_done(False))

    def delete(self, todo_id: UUID) -> None:
        """Remove the todo; raise `TodoNotFound` if there is none."""
        self._repository.delete(todo_id)

    def _save(self, todo: Todo) -> Todo:
        self._repository.update(todo)
        return todo
