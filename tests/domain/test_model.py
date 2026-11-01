from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone, tzinfo
from uuid import UUID

import pytest

from app.domain.errors import InvalidTitle
from app.domain.model import Todo
from tests.fakes import T0


def _from_constructor(title: str) -> Todo:
    return Todo(id=UUID(int=1), title=title, done=False, created_at=T0)


def _from_new(title: str) -> Todo:
    return Todo.new(title, now=T0)


def _from_with_title(title: str) -> Todo:
    return Todo(id=UUID(int=1), title="Original", done=False, created_at=T0).with_title(title)


TITLE_BUILDERS: list[Callable[[str], Todo]] = [_from_constructor, _from_new, _from_with_title]
BUILDER_IDS = ["constructor", "new", "with_title"]


def _created_at_from_constructor(created_at: datetime) -> Todo:
    return Todo(id=UUID(int=1), title="Buy milk", done=False, created_at=created_at)


def _created_at_from_new(created_at: datetime) -> Todo:
    return Todo.new("Buy milk", now=created_at)


CREATED_AT_BUILDERS: list[Callable[[datetime], Todo]] = [
    _created_at_from_constructor,
    _created_at_from_new,
]
CREATED_AT_BUILDER_IDS = ["constructor", "new"]


class _NoOffset(tzinfo):
    def utcoffset(self, _dt: datetime | None, /) -> timedelta | None:
        return None

    def dst(self, _dt: datetime | None, /) -> timedelta | None:
        return None

    def tzname(self, _dt: datetime | None, /) -> str | None:
        return None


@pytest.fixture
def todo() -> Todo:
    return Todo(id=UUID(int=1), title="Buy milk", done=False, created_at=T0)


def test_new_builds_an_open_todo_with_a_uuid4_id() -> None:
    created = Todo.new("Buy milk", now=T0)

    assert created.title == "Buy milk"
    assert created.done is False
    assert created.created_at == T0
    assert created.id.version == 4


def test_new_gives_each_todo_a_different_id() -> None:
    assert Todo.new("Buy milk", now=T0).id != Todo.new("Buy milk", now=T0).id


@pytest.mark.parametrize("build", TITLE_BUILDERS, ids=BUILDER_IDS)
def test_title_is_stripped_of_surrounding_whitespace(build: Callable[[str], Todo]) -> None:
    assert build("  Buy milk \n").title == "Buy milk"


@pytest.mark.parametrize("build", TITLE_BUILDERS, ids=BUILDER_IDS)
@pytest.mark.parametrize("title", ["", "   ", "\n\t"], ids=["empty", "spaces", "newline-tab"])
def test_blank_title_is_rejected(build: Callable[[str], Todo], title: str) -> None:
    with pytest.raises(InvalidTitle) as excinfo:
        build(title)

    assert str(excinfo.value) == "title must not be blank"


@pytest.mark.parametrize("build", TITLE_BUILDERS, ids=BUILDER_IDS)
@pytest.mark.parametrize(
    ("title", "accepted"),
    [
        ("x", True),
        ("  x \n", True),
        ("x" * 200, True),
        ("  " + "x" * 200 + "\t", True),
        ("x" * 201, False),
        (" " + "x" * 201 + " ", False),
    ],
    ids=["1", "1-padded", "200", "200-padded", "201", "201-padded"],
)
def test_title_length_is_limited_to_200_characters(
    build: Callable[[str], Todo], title: str, accepted: bool
) -> None:
    if accepted:
        assert build(title).title == title.strip()
    else:
        with pytest.raises(InvalidTitle) as excinfo:
            build(title)
        assert str(excinfo.value) == "title must be at most 200 characters"


@pytest.mark.parametrize("build", CREATED_AT_BUILDERS, ids=CREATED_AT_BUILDER_IDS)
def test_created_at_is_converted_to_utc(build: Callable[[datetime], Todo]) -> None:
    local = datetime(2026, 10, 4, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    created_at = build(local).created_at

    assert created_at == local
    assert created_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize("build", CREATED_AT_BUILDERS, ids=CREATED_AT_BUILDER_IDS)
@pytest.mark.parametrize(
    "created_at",
    [datetime(2026, 10, 4, 12, 0), datetime(2026, 10, 4, 12, 0, tzinfo=_NoOffset())],
    ids=["no-tzinfo", "tzinfo-without-offset"],
)
def test_naive_created_at_is_rejected(
    build: Callable[[datetime], Todo], created_at: datetime
) -> None:
    with pytest.raises(ValueError) as excinfo:
        build(created_at)

    assert not isinstance(excinfo.value, InvalidTitle)


def test_with_title_returns_a_new_todo_and_keeps_the_original(todo: Todo) -> None:
    renamed = todo.with_title("Buy oat milk")

    assert renamed.title == "Buy oat milk"
    assert renamed.id == todo.id
    assert renamed.done == todo.done
    assert renamed.created_at == todo.created_at
    assert todo.title == "Buy milk"


def test_with_done_returns_a_new_todo_and_keeps_the_original(todo: Todo) -> None:
    finished = todo.with_done(True)

    assert finished.done is True
    assert finished.id == todo.id
    assert finished.title == todo.title
    assert finished.created_at == todo.created_at
    assert todo.done is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", UUID(int=2)),
        ("title", "Other"),
        ("done", True),
        ("created_at", T0 + timedelta(hours=1)),
    ],
)
def test_todo_fields_cannot_be_assigned(todo: Todo, field: str, value: object) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(todo, field, value)
