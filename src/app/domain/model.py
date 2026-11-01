"""The todo entity and the rules that hold for every todo."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.errors import InvalidTitle

MAX_TITLE_LENGTH = 200


@dataclass(frozen=True, slots=True)
class Todo:
    """A single to-do item; its title is stripped and its creation time is in UTC."""

    id: UUID
    title: str
    done: bool
    created_at: datetime

    def __post_init__(self) -> None:
        """Normalise the title and the creation time, refusing values the rules forbid."""
        # The dataclass is frozen, so normalised values are set past its own __setattr__.
        object.__setattr__(self, "title", _valid_title(self.title))
        object.__setattr__(self, "created_at", _as_utc(self.created_at))

    @classmethod
    def new(cls, title: str, *, now: datetime) -> "Todo":
        """Create an open todo with a fresh random id, created at `now`."""
        return cls(id=uuid4(), title=title, done=False, created_at=now)

    def with_title(self, title: str) -> "Todo":
        """Return a copy of this todo with another title."""
        return replace(self, title=title)

    def with_done(self, done: bool) -> "Todo":
        """Return a copy of this todo with another done flag."""
        return replace(self, done=done)


def _valid_title(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        raise InvalidTitle("title must not be blank")
    if len(stripped) > MAX_TITLE_LENGTH:
        raise InvalidTitle(f"title must be at most {MAX_TITLE_LENGTH} characters")
    return stripped


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware")
    return moment.astimezone(UTC)
