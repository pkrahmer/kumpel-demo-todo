# Project guide

For agents and contributors who change the code. The rules every change follows are in `CLAUDE.md`; this file explains the shape of the code and why.

Only the domain, the in-memory repository, the service and the HTTP API exist so far. The API is described in `docs/api.md`; its code is in `src/app/api/` (`schemas`, `routes`, `errors`, `dependencies`, `app`, and `main` as the composition root).

## Layers

One package, `app`, under `src/`:

| Layer | May import | Role |
| --- | --- | --- |
| `app.api` | `app.service`, `app.domain` | Translates HTTP to service calls and maps domain errors to status codes. Chooses the concrete repository (wiring happens in `app.api.main` only). |
| `app.service` | `app.domain` | The use cases. Depends on the repository protocol only. |
| `app.repository` | `app.domain` | Concrete repositories. |
| `app.domain` | nothing outside itself | Entities, errors and the repository protocol. |

`app.service` and `app.repository` never import each other: the service talks to the protocol, and a repository satisfies it structurally, without inheriting from it. `app.domain` imports no framework (`fastapi`, `pydantic`, `sqlalchemy`) and does no I/O.

`make layers` (import-linter) enforces the order. That the domain is framework-free is checked by `tests/domain/test_imports.py`.

## Domain model

### `Todo` (`app/domain/model.py`)

A frozen dataclass with four fields:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `UUID` | |
| `title` | `str` | Stripped, 1 to `MAX_TITLE_LENGTH` (200) characters. |
| `done` | `bool` | |
| `created_at` | `datetime` | Always UTC. |

The rules are checked in `__post_init__`, so they hold however a todo is built: the constructor, `Todo.new`, `with_title` or `with_done`.

- **Title.** Surrounding whitespace is stripped first. A blank result raises `InvalidTitle("title must not be blank")`; more than 200 characters after stripping raises `InvalidTitle("title must be at most 200 characters")`.
- **Timestamps.** `created_at` must be timezone-aware and is converted to UTC (the same instant, offset zero). A naive datetime, or one whose `tzinfo` reports no offset, raises `ValueError`, not `InvalidTitle`.
- **`Todo.new(title, *, now)`** creates an open todo (`done=False`) with a fresh `uuid4` id. The caller passes the time, so the domain never reads the clock.
- **`with_title` and `with_done`** return a new todo and leave the original unchanged. Assigning to a field raises `dataclasses.FrozenInstanceError`.

### Errors (`app/domain/errors.py`)

All derive from `TodoError`.

| Error | Raised when | Message |
| --- | --- | --- |
| `InvalidTitle` | The title is blank or too long. | See above. |
| `TodoNotFound` | No todo has the id. | `todo <id> not found` |
| `DuplicateTodo` | A todo with the id is already stored. | `todo <id> already exists` |

`TodoNotFound` and `DuplicateTodo` carry the id as `todo_id`.

### Repository protocol (`app/domain/repository.py`)

`TodoRepository` has five methods:

- `add(todo)`: stores a new todo; `DuplicateTodo` if the id is taken (the first todo stays).
- `get(todo_id)`: returns the todo; `TodoNotFound` if there is none.
- `list_all()`: returns every todo ordered by `created_at`, oldest first, whatever order they were added in. Todos with equal `created_at` are ordered by id ascending.
- `update(todo)`: replaces the stored todo with the same id; `TodoNotFound` if there is none, and nothing is stored.
- `delete(todo_id)`: removes the todo; `TodoNotFound` if there is none.

`InMemoryTodoRepository` (`app/repository/memory.py`) keeps todos in a dictionary, for tests and development.

### Testing a repository

`tests/repository/test_contract.py` is one contract suite for every repository. A new repository joins it by adding its factory (a `Callable[[Path], TodoRepository]`) to the module's list of factories and its class to the list of classes.

## Service (`app/service/todo_service.py`)

`TodoService(repository, clock=utc_now)` holds the use cases. It reaches storage only through the `TodoRepository` protocol and imports nothing from `app.repository` or `app.api`; `make layers` enforces this.

| Method | Does |
| --- | --- |
| `create(title)` | Builds an open todo with `Todo.new`, stamped with the clock, stores it and returns it. |
| `get(todo_id)` | Returns the todo. |
| `list(*, done=None)` | Returns the todos in creation order (the repository's order). `done=True` keeps the completed ones, `done=False` the open ones, `None` all. |
| `rename(todo_id, title)` | Returns the todo with a new title; id, done flag and `created_at` stay. |
| `complete(todo_id)` / `reopen(todo_id)` | Return the todo with `done` true or false. Repeating either is not an error. |
| `delete(todo_id)` | Removes the todo. |

What the service owns:

- **The clock.** `Clock` is `Callable[[], datetime]`. The default, `utc_now()`, returns the current time as a timezone-aware UTC datetime. Tests pass a fixed clock, or one that ticks, so that times and order are observable. Only `create` reads the clock.
- **The done filter.** `list` calls `list_all()` and filters in memory, so the repository protocol has no filter parameter. A later SQL repository therefore loads every row before the filter applies; that is acceptable for a single user.
- **Errors.** The title rule stays in the domain. `InvalidTitle` and `TodoNotFound` pass through unchanged, and a failed `create` or `rename` stores nothing.

`rename`, `complete` and `reopen` read the todo with `get`, make the changed copy with `with_title` or `with_done`, and store it with `update`.

Tests (`tests/service/test_todo_service.py`) use `InMemoryTodoRepository`. `T0`, a fixed UTC time, is shared from `tests/fakes.py`.
