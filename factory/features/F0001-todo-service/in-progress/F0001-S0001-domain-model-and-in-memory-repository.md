---
stage: docs
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 1
comments_read: []
handed_over: null
claim:
  instance: demo
  stage: docs
  started_at: '2026-11-01T13:13:59.101584Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T13:01:49.342562Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T13:01:49.346971Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T13:02:10.225896Z'
  stage: intake
  run: c1b302391eaa4ed39515aff007089fe9
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T13:02:30.334167Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-01T13:04:08.030921Z'
  stage: tests
  run: 30f8ad3e34354420b18d1d7bbb462993
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-01T13:04:28.068713Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-01T13:05:13.776627Z'
  stage: doing
  run: 65781f125fa648e18275ed42ef59da9a
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-01T13:05:33.843089Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:06:27.905550Z'
  stage: review
  run: dc6560f9fc354963b7e684a74b798725
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-01T13:06:48.022898Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-01T13:07:05.124240Z'
  stage: doing
  run: b39d1f6e1720497d87d3033bb6475117
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-01T13:07:24.822158Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-01T13:07:53.600810Z'
  stage: tests
  run: 33cac5f4fa9f4940a531cbbdf9492f2e
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-01T13:08:13.886993Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-01T13:08:40.341599Z'
  stage: doing
  run: ce68180064ea43a489f973bdcaa87131
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-01T13:09:00.105153Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:09:48.846331Z'
  stage: review
  run: 7c16c4783bd04b74a333fc88c3d46a27
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-01T13:10:08.805422Z'
  stage: doing
- number: 19
  speaker: coder
  kind: result
  at: '2026-11-01T13:10:24.321965Z'
  stage: doing
  run: fd93d9fe4aac4568a89942d71932fcaf
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-01T13:10:44.363401Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-01T13:11:42.245376Z'
  stage: tests
  run: 33d9e90606624dffbf01e794850c8db8
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-01T13:12:02.581630Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-01T13:12:36.452732Z'
  stage: doing
  run: b9f700d3ce314d019cdee34e7147c2a1
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-01T13:12:56.362827Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:13:38.780451Z'
  stage: review
  run: fcb49518dd0d4666aafa7dfbdf0ba364
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-01T13:13:59.101584Z'
  stage: docs
---

# Domain model and in-memory repository

## Description

Create the domain layer of the to-do service: the `Todo` entity with its title rule and UTC timestamps, the domain errors, and the repository protocol; and the first repository behind that protocol, in memory, so that the service layer can be built and tested against it next. No service, no API, no SQLite yet.

## Interface

`src/app/domain/model.py`

```python
MAX_TITLE_LENGTH = 200

@dataclass(frozen=True, slots=True)
class Todo:
    id: UUID
    title: str
    done: bool
    created_at: datetime

    @classmethod
    def new(cls, title: str, *, now: datetime) -> "Todo": ...
    def with_title(self, title: str) -> "Todo": ...
    def with_done(self, done: bool) -> "Todo": ...
```

The rules hold however a todo is built (the constructor, `new`, `with_title`, `with_done`); each has a criterion below:

- the title is stripped of surrounding whitespace, then must be 1 to `MAX_TITLE_LENGTH` characters, else `InvalidTitle`;
- `created_at` must be timezone-aware and is converted to UTC; a naive one raises `ValueError`;
- `new` gives a fresh `uuid4` id and `done=False`;
- `with_title` and `with_done` return a new todo and leave the original as it was.

`src/app/domain/errors.py`

```python
class TodoError(Exception): ...

class InvalidTitle(TodoError): ...

class TodoNotFound(TodoError):
    todo_id: UUID
    def __init__(self, todo_id: UUID) -> None: ...

class DuplicateTodo(TodoError):
    todo_id: UUID
    def __init__(self, todo_id: UUID) -> None: ...
```

`src/app/domain/repository.py`

```python
class TodoRepository(Protocol):
    def add(self, todo: Todo) -> None: ...
    def get(self, todo_id: UUID) -> Todo: ...
    def list_all(self) -> list[Todo]: ...
    def update(self, todo: Todo) -> None: ...
    def delete(self, todo_id: UUID) -> None: ...
```

`src/app/repository/memory.py`

```python
class InMemoryTodoRepository:   # satisfies TodoRepository structurally, no inheritance
    def __init__(self) -> None: ...
```

Tests: `tests/domain/test_model.py`, `tests/domain/test_errors.py`, `tests/domain/test_imports.py`, and the repository behaviour as one contract suite in `tests/repository/test_contract.py`, run through a `repository` fixture that is parametrized over a module-level list of repository factories, each a `Callable[[Path], TodoRepository]` that the fixture calls with the test's `tmp_path`; here the list holds one factory, which returns `InMemoryTodoRepository()`. A later repository, also one that keeps a file under `tmp_path`, joins the suite by adding its factory to that list and its class to a second module-level list, of repository classes, with no other change to the file but a move of a shared test helper under the standing leave of `CLAUDE.md`. Fixed ids are built with `UUID(int=n)`.

## Acceptance criteria

1. `Todo.new("Buy milk", now=t)` with a timezone-aware `t` returns a todo titled `"Buy milk"`, not done, with `created_at == t` and an id whose UUID version is 4.
2. Two calls of `Todo.new` with the same arguments return todos with different ids.
3. The title is stripped of surrounding whitespace, whether the todo comes from `Todo(...)`, `Todo.new` or `with_title`: `"  Buy milk \n"` becomes `"Buy milk"`. Three rows of one parametrized test.
4. An empty or whitespace-only title (`""`, `"   "`, `"\n\t"`) raises `InvalidTitle` whose message is `title must not be blank`, from `Todo(...)`, `Todo.new` and `with_title` alike.
5. The length rule on both sides, as rows of one parametrized test, from `Todo(...)`, `Todo.new` and `with_title` alike: a title of 1 character and one of exactly 200 characters are accepted, also when surrounded by whitespace; a title of 201 characters after stripping raises `InvalidTitle` whose message is `title must be at most 200 characters`.
6. A `created_at` with a non-UTC offset is converted to UTC: `datetime(2026, 10, 4, 14, 0, tzinfo=timezone(timedelta(hours=2)))` is stored as a datetime equal to it whose `utcoffset()` is zero, from `Todo(...)` and `Todo.new` alike.
7. A naive `created_at` (no `tzinfo`) raises `ValueError`, not `InvalidTitle`, from `Todo(...)` and `Todo.new` alike.
8. `with_title` returns a new todo with the new title and the same id, done flag and `created_at`; the original keeps its title.
9. `with_done` returns a new todo with the new done flag and the same id, title and `created_at`; the original keeps its done flag.
10. Assigning to a field of a todo raises `dataclasses.FrozenInstanceError` (`setattr` with the field's name in a variable).
11. `TodoNotFound(todo_id)` carries the id as `todo_id`, and its message is `todo <todo_id> not found`, the UUID in its hyphenated form.
12. `DuplicateTodo(todo_id)` carries the id as `todo_id`, and its message is `todo <todo_id> already exists`.
13. `InvalidTitle`, `TodoNotFound` and `DuplicateTodo` are subclasses of `TodoError`.
14. `add` then `get` returns a todo equal to the one added.
15. `add` with an id that is already stored raises `DuplicateTodo` carrying that id, and `get` still returns the todo stored first.
16. `get`, `update` and `delete` with an unknown id each raise `TodoNotFound` carrying that id (three rows of one parametrized test); after the failed `update`, `list_all()` is still empty.
17. `list_all` on an empty repository returns `[]`.
18. `list_all` returns the todos ordered by `created_at`, oldest first, whatever order they were added in.
19. Todos with equal `created_at` are ordered by id ascending (ids built with `UUID(int=n)` make it observable).
20. `update` replaces the stored todo that has the same id; `get` afterwards returns the new version.
21. `delete` removes the todo; `get` afterwards raises `TodoNotFound`.
22. No repository class inherits the protocol: `InMemoryTodoRepository` is not a subclass of `TodoRepository` (`TodoRepository` is not in its `__mro__`; `issubclass` refuses a protocol that is not `runtime_checkable`), as a row of one parametrized test in `tests/repository/test_contract.py` over the module-level list of repository classes (here one class); and the contract suite's `repository` fixture is annotated as returning `TodoRepository`, so `make check` (mypy) proves each repository satisfies the protocol.
23. No module in `app.domain` imports `fastapi`, `pydantic`, `sqlalchemy`, or an `app` module outside `app.domain` (a test that parses the imports of every module under `src/app/domain` and names only these forbidden ones).
24. A `created_at` whose `tzinfo` gives no offset (its `utcoffset()` returns `None`) is naive too and raises `ValueError`, not `InvalidTitle`, from `Todo(...)` and `Todo.new` alike: rows of the parametrized test of criterion 7, beside the `created_at` without `tzinfo`.
25. `make check` stays green.
26. docs: `docs/project-guide.md` explains the layers (which may import which, and that service and repository never import each other) and the domain model (the `Todo` fields, the title rule, UTC timestamps, the three errors, the repository protocol and its ordering); the README's *Where to look next* links it.

## Smoke test

```bash
uv run python -c "
from datetime import UTC, datetime, timedelta
from app.domain.model import Todo
from app.repository.memory import InMemoryTodoRepository
repo = InMemoryTodoRepository()
t0 = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
a = Todo.new('  Buy milk ', now=t0)
b = Todo.new('Write the next story', now=t0 + timedelta(minutes=1))
repo.add(b); repo.add(a)
repo.update(a.with_done(True))
for t in repo.list_all(): print(t.done, repr(t.title), t.created_at.isoformat())
"
```

Expect: two lines, `True 'Buy milk' 2026-10-04T12:00:00+00:00` then `False 'Write the next story' 2026-10-04T12:01:00+00:00`: creation order although `b` was added first, the title stripped.

```bash
uv run python -c "
from datetime import UTC, datetime
from app.domain.errors import InvalidTitle
from app.domain.model import Todo
for title in ('   ', 'x' * 201):
    try:
        Todo.new(title, now=datetime.now(UTC))
    except InvalidTitle as e:
        print(type(e).__name__, '-', e)
"
```

Expect: two lines, `InvalidTitle - title must not be blank`, then `InvalidTitle - title must be at most 200 characters`.

## Journal

1. 2026-11-01 human: created.
2. factory: started intake as demo.
3. intake: accepted
   Interface: names concrete modules and signatures (`app/domain/model.py`, `errors.py`, `repository.py`, `app/repository/memory.py`) and the test files. The protocol and error signatures are complete, and the test layout (a contract suite with factory and class lists) is specific enough to build.
   Criteria: each is testable by one test function. Every Interface rule has a criterion for both sides. Strip is criterion 3. Blank is 4, with its message. Length is 5, at 1, 200 and 201 characters, with its message. UTC conversion is 6 and the naive `ValueError` is 7. `new` giving a uuid4 id and `done=False` is 1, and distinct ids are 2. `with_title` and `with_done` returning a new todo and leaving the original untouched are 8 and 9. Frozen is 10. Error messages and attributes are 11 and 12, and the hierarchy is 13. Repository add/get, duplicate, unknown id on three operations, empty list, ordering and tie-break, update, delete are 14 to 21. No inheritance is 22, and domain import purity is 23.
   Smoke test: both commands are runnable `uv run python -c` snippets that don't use pytest, so the pytest `-q` addopts rule doesn't apply. Each `Expect:` line gives exact output lines that can be checked against the output.
   Architecture: domain is framework-free, the repository implements the protocol structurally, and nothing imports from service or api. This matches CLAUDE.md's layering.
   Scope: this is S0001 of F0001. There is no service, API or SQLite, and nothing from the feature's Out of scope. It matches feature decisions 1 to 4 and 15.
4. factory: started tests as demo.
5. tester: Wrote the tests for criteria 1–23. All of them are red on purpose because the modules under test don't exist yet. `make lint` is green. I skipped the type check, as this stage says to.

   Criterion → test:
   - criterion 1: tests/domain/test_model.py::test_new_builds_an_open_todo_with_a_uuid4_id
   - criterion 2: tests/domain/test_model.py::test_new_gives_each_todo_a_different_id
   - criterion 3: tests/domain/test_model.py::test_title_is_stripped_of_surrounding_whitespace (rows: constructor, new, with_title)
   - criterion 4: tests/domain/test_model.py::test_blank_title_is_rejected ("", "   ", "\n\t" × constructor, new, with_title)
   - criterion 5: tests/domain/test_model.py::test_title_length_is_limited_to_200_characters (1, 1 padded, 200, 200 padded accepted; 201, 201 padded rejected with the message; × the three ways of building)
   - criterion 6: tests/domain/test_model.py::test_created_at_is_converted_to_utc (constructor, new)
   - criterion 7: tests/domain/test_model.py::test_naive_created_at_is_rejected (constructor, new)
   - criterion 8: tests/domain/test_model.py::test_with_title_returns_a_new_todo_and_keeps_the_original
   - criterion 9: tests/domain/test_model.py::test_with_done_returns_a_new_todo_and_keeps_the_original
   - criterion 10: tests/domain/test_model.py::test_todo_fields_cannot_be_assigned (one row per field, setattr with the name in a variable)
   - criterion 11: tests/domain/test_errors.py::test_todo_not_found_carries_the_id_and_names_it
   - criterion 12: tests/domain/test_errors.py::test_duplicate_todo_carries_the_id_and_names_it
   - criterion 13: tests/domain/test_errors.py::test_domain_errors_are_todo_errors
   - criterion 14: tests/repository/test_contract.py::test_added_todo_can_be_read_back
   - criterion 15: tests/repository/test_contract.py::test_adding_a_stored_id_is_rejected
   - criterion 16: tests/repository/test_contract.py::test_unknown_id_is_not_found (rows get, update, delete). It checks `list_all() == []` in every row; for get and delete that holds trivially.
   - criterion 17: tests/repository/test_contract.py::test_empty_repository_lists_nothing
   - criterion 18: tests/repository/test_contract.py::test_todos_are_listed_oldest_first
   - criterion 19: tests/repository/test_contract.py::test_todos_created_together_are_listed_by_id
   - criterion 20: tests/repository/test_contract.py::test_update_replaces_the_stored_todo
   - criterion 21: tests/repository/test_contract.py::test_deleted_todo_is_gone
   - criterion 22: tests/repository/test_contract.py::test_repository_does_not_inherit_the_protocol (over `REPOSITORY_CLASSES`). The `repository` fixture is annotated `-> TodoRepository` and parametrized over `REPOSITORY_FACTORIES: list[Callable[[Path], TodoRepository]]`; it calls each factory with `tmp_path`.
   - criterion 23: tests/domain/test_imports.py::test_domain_imports_no_framework_and_no_other_app_layer. It parses every `.py` file under src/app/domain with `ast`, resolves relative imports, and names only fastapi, pydantic, sqlalchemy and `app` modules outside `app.domain` as forbidden. It also asserts that there is at least one domain module.
   - criteria 24 and 25 (`make check`, docs) have no tests; they belong to the coder and documenter stages.

   Files created: tests/domain/__init__.py, tests/domain/test_model.py, tests/domain/test_errors.py, tests/domain/test_imports.py, tests/repository/__init__.py, tests/repository/test_contract.py.

   `make test` output: 1 failed, 3 errors.
   - Modules the test runner could not import: `app.domain.errors`, `app.domain.model`, `app.domain.repository`, `app.repository.memory`. This caused the ImportErrors at collection in test_errors.py, test_model.py and test_contract.py.
   - The failure is test_imports.py: src/app/domain does not exist yet, so the check that at least one domain module exists fails.

   Rejected: a shared conftest helper for building todos. The domain and repository modules each keep a small local builder, and no earlier test module holds a copy, so no helper was moved. Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: 1 failed, 3 errors in 0.78s
6. factory: started doing as demo.
7. coder: Built the domain layer and the in-memory repository. All 59 tests pass, and `make check` is green with 100 % coverage.

   Paths:
   - src/app/domain/__init__.py
   - src/app/domain/errors.py: `TodoError`, `InvalidTitle`, `TodoNotFound`, `DuplicateTodo`. The last two set `todo_id` and the message from the hyphenated UUID.
   - src/app/domain/model.py: `MAX_TITLE_LENGTH` and `Todo`, a frozen slotted dataclass. Private helpers `_valid_title` and `_as_utc` hold the rules.
   - src/app/domain/repository.py: the `TodoRepository` protocol. Its docstrings state the errors and the ordering.
   - src/app/repository/__init__.py
   - src/app/repository/memory.py: `InMemoryTodoRepository`. It keeps a dict keyed by id, has no base class, and sorts `list_all` by `(created_at, id)`. A private `_require` raises `TodoNotFound`.

   Main choice: `Todo.__post_init__` normalises and checks the title and `created_at`, using `object.__setattr__` because the class is frozen. `with_title` and `with_done` use `dataclasses.replace`. So every way of building a todo (the constructor, `new`, `with_*`) goes through one check, as the Interface requires. Rejected: checking in `new` and `with_title` only. Plain `Todo(...)` would then bypass the rules, which criteria 3–7 forbid. Also rejected: a separate validated `TodoTitle` value type. The Interface fixes `title: str`.

   Refactor pass: I read the diff and found nothing to change.

   Description: the journal did not change the meaning of the task, so `## Description` is untouched.

   Noticed, not touched:
   - `docs/` does not exist yet. Criterion 25 (`docs/project-guide.md`, the README link) is the documenter's.
   - No route or schema exists yet, so I did not run `make openapi`.

   `check`: check: green
   `duplicates`: duplicates: 0 similar code, 15 dead code, in .reports/
8. factory: started review as demo.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. There was no generated file or lock file in the diff to leave out.

   Group 1, acceptance criteria: passes.
   - Criteria 1–23 each have a test that checks what the criterion says.
   - The length limit is tested on both sides (1, 200 and 201 characters, each also with padding), and from all three ways of building a todo.
   - The failing sides are tested: blank title, 201 characters and naive `created_at`.
   - Criterion 16 checks the empty list after the failed `update`.
   - Criterion 22 runs over `REPOSITORY_CLASSES`, and the fixture is annotated `-> TodoRepository`.
   - The coder's `make check` was green (journal entry 7).

   Groups 2 and 3, architecture and security: pass.
   - `app.domain` imports only `app.domain` and the standard library.
   - `app.repository.memory` imports only `app.domain` and has no base class.
   - There are no suppression markers, no secrets and no string-built shell or SQL.

   Group 4, quality: one finding.
   1. `tests/domain/test_model.py:655-662` and `:672-679`: `test_created_at_is_converted_to_utc` and `test_naive_created_at_is_rejected` each have their own identical list of builder lambdas (constructor, new). That is a second copy of the same setup in one module, and `CLAUDE.md` says shared setup is defined once. Fix: define the two builders once at module level, like `TITLE_BUILDERS`/`BUILDER_IDS` (for example `CREATED_AT_BUILDERS` with ids `["constructor", "new"]`), and parametrize both tests over it. This is the tester's change: no test is renamed and no check changes.

   Group 5 was not reached because the review stops at group 4. Nothing there stood out:
   - The journal explains the `__post_init__` choice and what was rejected.
   - The Description matches what was built.
   - The docs criterion (25) still describes what the reader needs to know.

   Considered and not raised:
   - `_as_utc` checks both `tzinfo is None` and `utcoffset() is None`. The first test is redundant but correct, and it reads clearly.
   - `T0` and a small todo builder appear in both `test_model.py` and `test_contract.py`. The tester rejected a shared helper on purpose, and no earlier test module holds a copy.

   Earlier tests: none. Every test file in the diff is new (status `A`).
10. factory: started doing as demo.
11. coder: Round 1: the review's only finding (entry 9, group 4) is about the tests, so I changed no code and am handing it to the tester.

    Change for the tester, in `tests/domain/test_model.py`: `test_created_at_is_converted_to_utc` (line 94) and `test_naive_created_at_is_rejected` (line 111) each have their own identical list of builder lambdas (constructor and new). Define that list once at module level, next to `TITLE_BUILDERS` and `BUILDER_IDS` (for example `CREATED_AT_BUILDERS` with ids `["constructor", "new"]`), and parametrize both tests over it. Neither test is renamed and neither checks anything different.

    Built: nothing new this round. The code from entry 7 stands: `src/app/domain/{errors,model,repository}.py` and `src/app/repository/memory.py`.

    Main choice: send the work item back with `tests` instead of asking a question. The finding changes only the setup inside one new test module the tester wrote for this story, the reviewer called it the tester's change, and the coder never edits tests. Rejected: editing the test myself, which the role forbids.

    Description: the journal did not change the meaning of the task, so `## Description` is untouched.

    Noticed, not touched: as in entry 7, `docs/` does not exist yet; criterion 25 belongs to the documenter. I did not run `make check` this round because nothing in the source changed; it was green in entry 7.
12. factory: started tests as demo.
13. tester: Round 1: made the test change named in the coder's entry 11, which passes on the reviewer's finding from entry 9, group 4. It touches only `tests/domain/test_model.py`, a module I wrote for this story. No other file changed.

    Change: `test_created_at_is_converted_to_utc` and `test_naive_created_at_is_rejected` each had their own copy of the same two builder lambdas. I replaced both copies with one module-level list, next to `TITLE_BUILDERS`/`BUILDER_IDS`:
    - two named builders, `_created_at_from_constructor` and `_created_at_from_new`, matching the style of the title builders;
    - `CREATED_AT_BUILDERS: list[Callable[[datetime], Todo]]`;
    - `CREATED_AT_BUILDER_IDS = ["constructor", "new"]`.

    Both tests are now parametrized over that list. Neither test is renamed, the row ids are unchanged (constructor, new), and each test checks the same thing as before. I used named functions rather than a list of lambdas to match the existing title builders.

    The criterion → test mapping from entry 5 still holds:
    - criterion 6: tests/domain/test_model.py::test_created_at_is_converted_to_utc
    - criterion 7: tests/domain/test_model.py::test_naive_created_at_is_rejected

    Files created: none. File changed: tests/domain/test_model.py.

    Modules the test runner could not import: none. The code from entry 7 exists, and `make test` passed all 59 tests (coverage 100 %). `make lint` is green.

    Open: nothing.

    `lint`: lint: green (0.0 s)
    `test`: test: green (1.5 s)
14. factory: started doing as demo.
15. coder: Round 1, after the tester's change: I changed no code. The review's only finding (entry 9, group 4) was about a duplicated list of builders in `tests/domain/test_model.py`. The tester fixed it in entry 13 by adding one module-level `CREATED_AT_BUILDERS`, and nothing about the finding is left for the coder.

    Built: nothing new this round. The code from entry 7 is unchanged:
    - src/app/domain/__init__.py
    - src/app/domain/errors.py
    - src/app/domain/model.py
    - src/app/domain/repository.py
    - src/app/repository/__init__.py
    - src/app/repository/memory.py

    Check: I ran `make check` on the current tree. It is green: 59 tests pass and coverage is 100 %.

    Main choice: send the work item on to review without touching the source, because the finding was in the tests only. Rejected: another refactor pass over the source. The reviewer found nothing in the code, and a change now would go beyond the findings, which this round may not do.

    Description: the journal did not change the meaning of the task, so `## Description` is untouched.

    Noticed, not touched: `docs/` does not exist yet. Criterion 25 (`docs/project-guide.md` and the README link) belongs to the documenter.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 similar code, 15 dead code, in .reports/
16. factory: started review as demo.
17. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`, which has no generated or lock files to leave out, checked against the work item.

    Group 1, acceptance criteria. I checked criteria 1–23 and every rule in the Interface against the tests:
    - Strip, blank and length are each tested from the constructor, `new` and `with_title`. Length is tested at 1, 200 and 201, each also with padding.
    - The UTC conversion is tested, and so is the naive `ValueError` with no `tzinfo`.
    - The error messages and ids, the hierarchy, the repository contract including the empty list after a failed `update`, the order and its id tie-break, the absence of inheritance and the domain import purity all have tests.
    - The coder's `make check` was green (entries 7 and 15).

    I found one gap. The code has a behaviour that no criterion names, and I added a criterion for it:

    1. criterion 24 added: it needs its test. `src/app/domain/model.py:52` (`_as_utc`) also rejects a `created_at` that has a `tzinfo` whose `utcoffset()` returns `None`.
       - This check is not redundant, as entry 9 called it. Without it, `astimezone` would treat that datetime as local time and convert it silently.
       - Criterion 7 and `tests/domain/test_model.py::test_naive_created_at_is_rejected` only cover a missing `tzinfo`, so deleting `or moment.utcoffset() is None` leaves every test green.
       - Fix (the tester's): add rows to that test's parametrization, built with a `tzinfo` subclass whose `utcoffset` returns `None`, from the constructor and `new`, next to the existing no-`tzinfo` rows.
       - No change under `src/` is needed.
       - The old criteria 24 (`make check`) and 25 (docs) are now 25 and 26.

    I stopped at group 1. Groups 2 and 3 looked clean on the way:
    - `app.domain` imports only `app.domain` and the standard library.
    - `app.repository.memory` imports only `app.domain` and has no base class.
    - There are no suppression markers, no secrets and no string-built shell or SQL.

    Earlier tests: none. Every test file in the diff is new (status `A`).

    Notes:
    - `tests/domain/test_model.py:11` and `tests/repository/test_contract.py:13` both define the same `T0`.
    - `tests/repository/test_contract.py:30` (`_todo`) and `tests/domain/test_model.py:14,45` (`_from_constructor`, the `todo` fixture) build the same kind of todo. A shared module under `tests/` could hold these.
18. factory: started doing as demo.
19. coder: Round 2: I changed no code. Criterion 24, which the reviewer added in entry 17, only needs its test, so I'm sending the work item back to the tester.

    **Criterion for the tester:** criterion 24. A `created_at` whose `tzinfo` gives no offset (`utcoffset()` returns `None`) counts as naive and raises `ValueError`, not `InvalidTitle`, from both `Todo(...)` and `Todo.new`.
    - Add these as rows of `tests/domain/test_model.py::test_naive_created_at_is_rejected`, beside the existing rows that have no `tzinfo`. Build them with a `tzinfo` subclass whose `utcoffset` returns `None`.
    - I checked the test: it has no such rows yet.
    - The code already behaves this way: `src/app/domain/model.py:51` (`_as_utc`) checks both `moment.tzinfo is None` and `moment.utcoffset() is None`.

    **Built:** nothing new this round. The code from entry 7 stands: `src/app/domain/{__init__,errors,model,repository}.py` and `src/app/repository/{__init__,memory}.py`.

    **Main choice:** end with `tests` and leave the source alone. The finding asks only for a test of behaviour that already exists, and the coder never edits tests. Rejected: asking the human a question. The reviewer's added criterion is clear, and it changes no Interface.

    **Description:** entry 17 added criterion 24 and renumbered the closing two criteria to 25 and 26; the reviewer has already written that into the Description. The meaning of the task is otherwise unchanged, so I didn't touch `## Description`.

    **Noticed, not touched:**
    - The reviewer noted that `T0` is defined in both `tests/domain/test_model.py` and `tests/repository/test_contract.py`, and that each file has a similar todo builder. Under the standing leave, the tester may move them into a shared module under `tests/`. The reviewer didn't raise this as a finding, so I'm not asking for it.
    - `docs/` still doesn't exist; criterion 26 belongs to the documenter.
    - I didn't run `make check` this round because no source changed. It was green in entry 15.
20. factory: started tests as demo.
21. tester: Round 2: I wrote the test for criterion 24. The reviewer added that criterion in entry 17, and the coder's entry 19 sent it back to me. It touches only `tests/domain/test_model.py`, a module I wrote for this story. No other file changed.

    Change:
    - I added a module-level test `tzinfo`, `_NoOffset`. Its `utcoffset` returns `None`. It also implements `dst` and `tzname`, both returning `None`, because typeshed marks those two abstract and mypy would otherwise refuse to build the class.
    - `test_naive_created_at_is_rejected` now has a second parametrization, `created_at`, next to the existing `build` one (constructor, new). It has two rows:
      - `no-tzinfo`: the earlier datetime, unchanged (criterion 7).
      - `tzinfo-without-offset`: `datetime(2026, 10, 4, 12, 0, tzinfo=_NoOffset())` (criterion 24).
    - The test keeps its name and still checks `ValueError`, not `InvalidTitle`.

    Mapping:
    - criterion 7: tests/domain/test_model.py::test_naive_created_at_is_rejected (rows `no-tzinfo` × constructor, new)
    - criterion 24: tests/domain/test_model.py::test_naive_created_at_is_rejected (rows `tzinfo-without-offset` × constructor, new)
    - The rest of the mapping from entry 5 still holds. The closing two criteria, now 25 and 26, have no tests.

    Files created: none. File changed: tests/domain/test_model.py.

    Modules the test runner could not import: none. The code exists, so the new rows pass now (61 passed) instead of failing first. If `or moment.utcoffset() is None` were removed from `_as_utc`, `astimezone` would treat the datetime as local time and not raise, so the new rows would fail.

    `make lint` is green. I also ran `mypy --strict` on this one file, outside the stage's steps, to catch the abstract-class error above. With the extra methods the only errors left were `import-untyped` for `app.domain`, which come from checking the file outside the project's mypy setup. The coder's `make check` is the real type check.

    Rejected:
    - Moving `T0` and the todo builders into a shared module under the standing leave. The reviewer gave it as a note, not a finding, and this run is only the approved change.

    Open: nothing.

    `lint`: lint: green (0.0 s)
    `test`: test: green (1.5 s)
22. factory: started doing as demo.
23. coder: Round 2, after the tester's change: I changed no code. The only finding in this round was the reviewer's criterion 24 (entry 17). The tester covered it in entry 21 with the `tzinfo-without-offset` rows in `tests/domain/test_model.py::test_naive_created_at_is_rejected`, so nothing is left for the coder to do.

    Built: nothing new this round. The code from entry 7 is unchanged:
    - `src/app/domain/__init__.py`
    - `src/app/domain/errors.py`
    - `src/app/domain/model.py`
    - `src/app/domain/repository.py`
    - `src/app/repository/__init__.py`
    - `src/app/repository/memory.py`

    The check in `_as_utc` (`src/app/domain/model.py`), `moment.tzinfo is None or moment.utcoffset() is None`, already raises `ValueError` for the new rows.

    Check: I ran `make check` on the current tree and it is green: 61 tests pass and coverage is 100 %. mypy accepts the test's `_NoOffset` tzinfo under `--strict`.

    Main choice: send the work item on to review without touching the source. The finding only needed a test, and that test now exists. Rejected: another refactor pass over the source. That would go beyond this round's findings, and the reviewer found nothing in the code.

    Description: entry 17 added criterion 24 and renumbered the closing two to 25 and 26, and the Description already shows this. The meaning of the task is otherwise unchanged, so I left `## Description` alone.

    Noticed, not touched:
    - `T0` is defined twice, and there are similar todo builders in `tests/domain/test_model.py` and `tests/repository/test_contract.py`. These are the reviewer's notes from entry 17, not findings. Moving them would be the tester's job under the standing leave.
    - `docs/` does not exist yet. Criterion 26 belongs to the documenter.
    - No route or schema exists yet, so I did not run `make openapi`.

    `check`: check: green
    `duplicates`: duplicates: 0 similar code, 15 dead code, in .reports/
24. factory: started review as demo.
25. reviewer: Round 2 review of `git diff main...HEAD -- . ':!factory'` against the work item. The diff has no generated files or lock files to leave out. I read the full source and every test file; I did not run `make check`, as the stage says.

    no findings

    Group 1, acceptance criteria: passes. I went through criteria 1–24 and every rule in the Interface against the tests.
    - The title rule is tested from the constructor, `new` and `with_title`:
      - strip (criterion 3);
      - blank, with its message (criterion 4);
      - length at 1, 200 and 201 characters, each also padded, with the message (criterion 5).
      The limit is tested on both sides as rows of one parametrized test.
    - UTC conversion (criterion 6) and the naive `ValueError` (criteria 7 and 24) are tested from the constructor and `new`. Criterion 24 is now covered: `tests/domain/test_model.py:122-134` has a `tzinfo-without-offset` row, built with `_NoOffset` whose `utcoffset` returns `None`. Without the `utcoffset() is None` clause in `src/app/domain/model.py:51` that row would fail, because `astimezone` would treat the datetime as local time.
    - Also covered:
      - `with_title` and `with_done` return new todos and keep the original (criteria 8–9);
      - the dataclass is frozen (criterion 10);
      - the error ids, messages and hierarchy (criteria 11–13);
      - the repository contract (criteria 14–21): duplicate, unknown id as three rows with the empty list after a failed `update`, ordering, tie-break by id;
      - no inheritance, over `REPOSITORY_CLASSES`, with the fixture typed `-> TodoRepository` (criterion 22);
      - domain import purity, naming only the forbidden imports (criterion 23).
    - The coder's `make check` after the last change was green (journal entry 23).

    Group 2, architecture: passes.
    - `app.domain` imports only the standard library and `app.domain`.
    - `app.repository.memory` imports only `app.domain` and has no base class.
    - `app.service` and `app.api` do not exist yet.

    Group 3, security: passes. There are no secrets, no suppression markers and no shell or SQL built from strings.

    Group 4, quality: passes.
    - The domain has the module, class and function docstrings that `CLAUDE.md` asks for; `app.repository` has its module docstrings.
    - The one comment (`model.py:24`) explains why `object.__setattr__` is used.
    - Considered and not raised: `moment.tzinfo is None` in `_as_utc` is implied by `utcoffset() is None`. It is redundant but harmless and reads clearly.

    Group 5, work item hygiene: passes.
    - The journal explains the main choice (`__post_init__` as the single place where the rules are checked) and what was rejected (checking only in `new` and `with_title`; a `TodoTitle` value type).
    - The Description matches what was built.
    - Criterion 26 (docs) still describes what a reader needs to know after this story.

    Earlier tests: none. Every test file in the diff is new (status `A`).

    Notes:
    - `tests/domain/test_model.py:11` and `tests/repository/test_contract.py:13` both define the same `T0`. A shared module under `tests/` could hold it.
    - `tests/domain/test_model.py`: these build the same todo:
      - `_from_constructor` (line 14);
      - `_created_at_from_constructor` (line 30);
      - the `todo` fixture (line 56);
      - `tests/repository/test_contract.py:30` (`_todo`).
      One shared builder with keyword defaults would cover all of them.
26. factory: started docs as demo.
