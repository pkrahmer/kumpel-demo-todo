"""The errors the domain raises when a rule about todos is broken."""

from uuid import UUID


class TodoError(Exception):
    """Base of every error the domain raises about todos."""


class InvalidTitle(TodoError):
    """A title is blank or longer than the domain allows."""


class TodoNotFound(TodoError):
    """No todo with the given id is stored."""

    def __init__(self, todo_id: UUID) -> None:
        """Name the id that was looked for."""
        super().__init__(f"todo {todo_id} not found")
        self.todo_id = todo_id


class DuplicateTodo(TodoError):
    """A todo with the given id is already stored."""

    def __init__(self, todo_id: UUID) -> None:
        """Name the id that is already taken."""
        super().__init__(f"todo {todo_id} already exists")
        self.todo_id = todo_id
