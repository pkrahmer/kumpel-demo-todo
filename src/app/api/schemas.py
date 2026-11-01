"""The request and response bodies of the todo endpoints."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.domain.model import Todo


class TodoCreate(BaseModel):
    # No length or blank rule here: the domain owns the title rule and its messages.
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

    @model_validator(mode="after")
    def _sets_a_field(self) -> Self:
        if self.title is None and self.done is None:
            raise ValueError("set at least one of title and done")
        return self


class TodoRead(BaseModel):
    id: UUID
    title: str
    done: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, todo: Todo) -> "TodoRead":
        return cls(id=todo.id, title=todo.title, done=todo.done, created_at=todo.created_at)
