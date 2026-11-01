"""The todo endpoints, translating HTTP to service calls."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import Service
from app.api.schemas import TodoCreate, TodoRead, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_todo(body: TodoCreate, service: Service) -> TodoRead:
    return TodoRead.from_domain(service.create(body.title))


@router.get("")
def list_todos(service: Service, done: bool | None = None) -> list[TodoRead]:
    return [TodoRead.from_domain(todo) for todo in service.list(done=done)]


@router.get("/{todo_id}")
def get_todo(todo_id: UUID, service: Service) -> TodoRead:
    return TodoRead.from_domain(service.get(todo_id))


@router.patch("/{todo_id}")
def update_todo(todo_id: UUID, body: TodoUpdate, service: Service) -> TodoRead:
    # The title goes first, so that a title the domain refuses leaves the done flag untouched.
    todo = service.get(todo_id)
    if body.title is not None:
        todo = service.rename(todo_id, body.title)
    if body.done is True:
        todo = service.complete(todo_id)
    elif body.done is False:
        todo = service.reopen(todo_id)
    return TodoRead.from_domain(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: UUID, service: Service) -> None:
    service.delete(todo_id)
