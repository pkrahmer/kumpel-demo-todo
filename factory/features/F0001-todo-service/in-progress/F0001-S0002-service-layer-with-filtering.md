---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 2
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T13:18:43.285095Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T13:18:43.289282Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T13:19:00.449815Z'
  stage: intake
  run: c0d87f0da7bf45e2beb8c4b0ac0e2bbf
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T13:19:20.317843Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-01T13:20:06.820667Z'
  stage: tests
  run: 3de18135c9394c568f5a7dc3251054af
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-01T13:20:26.790833Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-01T13:21:03.714405Z'
  stage: doing
  run: 8e27ef350ad64a018f3e9a7f31e86c7a
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-01T13:21:23.557414Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:22:06.088293Z'
  stage: review
  run: 50bce27fe1604c29add0a14836806878
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-01T13:22:25.842711Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-01T13:22:44.159252Z'
  stage: doing
  run: 1b8de9c1a8904fdf8bd66caed71dc10b
---

# Service layer with filtering

## Description

Add the use-case layer on top of the domain: a `TodoService` that creates, reads, lists (all, or filtered by the done flag), renames, completes, reopens and deletes todos through the `TodoRepository` protocol. The service owns the clock, injectable for tests; the title rule stays in the domain and its errors pass through unchanged. No API yet.

## Interface

`src/app/service/todo_service.py`

```python
Clock = Callable[[], datetime]

def utc_now() -> datetime: ...

class TodoService:
    def __init__(self, repository: TodoRepository, clock: Clock = utc_now) -> None: ...
    def create(self, title: str) -> Todo: ...
    def get(self, todo_id: UUID) -> Todo: ...
    def list(self, *, done: bool | None = None) -> list[Todo]: ...
    def rename(self, todo_id: UUID, title: str) -> Todo: ...
    def complete(self, todo_id: UUID) -> Todo: ...
    def reopen(self, todo_id: UUID) -> Todo: ...
    def delete(self, todo_id: UUID) -> None: ...
```

- `create` stamps `created_at` with the clock; `list(done=None)` means no filter; every list is in the repository's order (creation order).
- Domain errors (`InvalidTitle`, `TodoNotFound`) propagate unchanged.
- `app.service` sees storage only through `TodoRepository`; import-linter (`make check`) already refuses an import of `app.repository` there. Tests use `InMemoryTodoRepository` as the concrete repository; a test may import it.

Tests: `tests/service/test_todo_service.py`, with a clock that returns a fixed time, or one that ticks a minute per call where the order must be observable.

## Acceptance criteria

1. `create("  Buy milk ")` returns a todo titled `Buy milk`, not done, whose `created_at` is the value the injected clock returned; `get` with its id returns an equal todo.
2. `create` with a blank title raises `InvalidTitle`, and `list()` is still empty afterwards.
3. `get` with an unknown id raises `TodoNotFound` carrying that id.
4. `list()` returns every todo, in creation order (a clock that ticks makes the order observable).
5. The done filter, as rows of one parametrized test over two completed and two open todos created alternately: `list(done=True)` returns only the completed todos, `list(done=False)` only the open ones, and `list(done=None)` all four, each in creation order.
6. `rename` returns the todo with the new title, stripped, and the same id, done flag and `created_at`; `get` returns the renamed todo afterwards.
7. `rename` with a blank title raises `InvalidTitle`, and `get` still returns the todo with its old title.
8. `complete` returns the todo with `done` true, and `get` returns it completed afterwards.
9. `complete` on a completed todo returns it, still done, without an error.
10. `reopen` returns the todo with `done` false, and `get` returns it open afterwards.
11. `reopen` on an open todo returns it, still open, without an error.
12. `delete` removes the todo: `get` afterwards raises `TodoNotFound`.
13. `rename`, `complete`, `reopen` and `delete` with an unknown id each raise `TodoNotFound` carrying that id: four rows of one parametrized test.
14. `utc_now()` returns a timezone-aware datetime with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
15. A `TodoService` built without a clock stamps with `utc_now`: a todo created through `TodoService(repository)` has a timezone-aware `created_at` with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
16. `make check` stays green.
17. docs: `docs/project-guide.md` describes the service layer: what `TodoService` owns (the use cases, the clock, the done filter) and that it reaches storage only through the repository protocol.

## Smoke test

```bash
uv run python -c "
from datetime import UTC, datetime
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import TodoService
svc = TodoService(InMemoryTodoRepository(), clock=lambda: datetime(2026, 10, 4, 12, 0, tzinfo=UTC))
a = svc.create('  Buy milk ')
b = svc.create('Write the next story')
svc.complete(a.id)
print([t.title for t in svc.list(done=True)])
print([t.title for t in svc.list(done=False)])
print(svc.rename(b.id, 'Write story S0003').title, svc.get(b.id).created_at.isoformat())
"
```

Expect: three lines, `['Buy milk']`, then `['Write the next story']`, then `Write story S0003 2026-10-04T12:00:00+00:00`.

```bash
uv run python -c "
from uuid import uuid4
from app.repository.memory import InMemoryTodoRepository
from app.service.todo_service import TodoService
svc = TodoService(InMemoryTodoRepository())
for call in (lambda: svc.create('   '), lambda: svc.complete(uuid4())):
    try:
        call()
    except Exception as e:
        print(type(e).__name__)
print(svc.list())
"
```

Expect: three lines, `InvalidTitle`, then `TodoNotFound`, then `[]`.

## Journal

1. 2026-11-01 human: created.
2. factory: started intake as demo.
3. intake: accepted
   Interface: `src/app/service/todo_service.py` names `Clock`, `utc_now` and `TodoService` with typed signatures for all seven use cases. The collaborators it relies on (`TodoRepository`, `InMemoryTodoRepository`, `InvalidTitle`, `TodoNotFound`) come from S0001. I did not open the S0001 sources.
   Criteria: each is testable by one test function. Every Interface behaviour has a criterion: the clock stamp (1), `list(done=None)` as no filter and creation order (4, 5), error propagation (2, 3, 7, 13), and `utc_now` and its default use (14, 15). Every rule has both sides: blank title rejected on create (2) and rename (7), unknown id for all four mutators (13), and complete/reopen idempotence (9, 11). The 200-character title limit is a domain rule from S0001, and the service passes its errors through unchanged, so it needs no criterion here. Criteria 16 and 17 are the two closing ones, in the right order.
   Smoke test: both commands are plain `uv run python -c` runs and do not call pytest. Each `Expect:` line is checkable against the printed output: the three exact lines in the first, and `InvalidTitle`, `TodoNotFound`, `[]` in the second.
   Architecture: the service depends on the repository protocol only, and tests may import the in-memory repository. This matches the layering in CLAUDE.md, and `make layers` enforces it.
   Scope: the story covers feature decisions 5 and 17 and the feature's service-layer scope bullet. It adds no API, no persistence and no sorting beyond creation order, so it stays out of "Out of scope".
4. factory: started tests as demo.
5. tester: Wrote the service tests from the Interface and criteria 1–15, using `InMemoryTodoRepository` as the concrete repository. Two fixtures: a service on a fixed clock (`NOON`) and one on a clock that ticks a minute per call, used where creation order has to be visible (criteria 4 and 5).
   criterion 1: tests/service/test_todo_service.py::test_create_strips_the_title_and_stamps_the_clock_time
   criterion 2: tests/service/test_todo_service.py::test_create_with_a_blank_title_is_rejected_and_stores_nothing
   criterion 3: tests/service/test_todo_service.py::test_get_with_an_unknown_id_raises_not_found
   criterion 4: tests/service/test_todo_service.py::test_list_returns_every_todo_in_creation_order
   criterion 5: tests/service/test_todo_service.py::test_list_filters_by_the_done_flag_in_creation_order (rows done=True, done=False, done=None over four alternately created todos)
   criterion 6: tests/service/test_todo_service.py::test_rename_changes_only_the_title (renames a completed todo, so a reset done flag would be caught)
   criterion 7: tests/service/test_todo_service.py::test_rename_with_a_blank_title_is_rejected_and_keeps_the_old_title
   criterion 8: tests/service/test_todo_service.py::test_complete_marks_the_todo_done
   criterion 9: tests/service/test_todo_service.py::test_complete_on_a_completed_todo_keeps_it_done
   criterion 10: tests/service/test_todo_service.py::test_reopen_marks_the_todo_open
   criterion 11: tests/service/test_todo_service.py::test_reopen_on_an_open_todo_keeps_it_open
   criterion 12: tests/service/test_todo_service.py::test_delete_removes_the_todo
   criterion 13: tests/service/test_todo_service.py::test_changing_an_unknown_todo_raises_not_found (rows rename, complete, reopen, delete)
   criterion 14: tests/service/test_todo_service.py::test_utc_now_is_the_current_time_in_utc
   criterion 15: tests/service/test_todo_service.py::test_service_without_a_clock_stamps_the_current_utc_time
   Criteria 16 (`make check`) and 17 (docs) are not tests.
   Files created: tests/service/__init__.py, tests/service/test_todo_service.py.
   Module the test run could not import: `app.service.todo_service`. `make test` shows a collection ImportError for tests/service/test_todo_service.py, and the 61 earlier tests pass. `make lint` is green.
   I did not move the `T0` constant from tests/repository/test_contract.py to a shared place. A one-line datetime value isn't a shared helper, so this file defines its own `NOON`. No earlier test files were changed.

   `lint`: lint: green (0.0 s)
   `test`: 61 passed, 1 error in 0.79s
6. factory: started doing as demo.
7. coder: Built the service layer: `src/app/service/__init__.py` (package docstring) and `src/app/service/todo_service.py` with `Clock`, `utc_now()` and `TodoService`. `TodoService` depends only on the `TodoRepository` protocol. It stamps `created_at` with the injected clock through `Todo.new` and filters `list(done=...)` over `list_all()`, so the list keeps the repository's creation order. `rename`, `complete` and `reopen` read the todo with `get`, build the changed copy with the domain's `with_title` / `with_done` and save it through one private `_save` (update, then return). The domain enforces the title rule, and `InvalidTitle` / `TodoNotFound` pass through unchanged. `make check` is green: 81 passed, 100% coverage.

   Main choice: the service filters in memory over `list_all()`. The alternative was a `done` parameter on the repository protocol. I rejected it because it changes the S0001 protocol and contract, which is outside this story, and the filter is a use-case concern the description gives to the service. The trade-off is that a later SQL repository loads every row before filtering. Until the human asks for a filtered query, that is acceptable at single-user scale.

   Refactor pass: I read the diff and found nothing to change. `_save` already removes the repeated update-and-return.

   Noticed, not touched: the docs criterion (17, `docs/project-guide.md`) is the documenter's job. I wrote no route or schema, so `make openapi` was not needed. The journal did not change the meaning of the description.

   `check`: check: green
   `duplicates`: duplicates: 0 similar code, 6 dead code, in .reports/
8. factory: started review as demo.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: `src/app/service/__init__.py`, `src/app/service/todo_service.py`, `tests/service/__init__.py` and `tests/service/test_todo_service.py`, against the work item.

   Groups 1 to 3 pass.
   - Acceptance criteria: each of criteria 1–15 has a test that checks what the criterion says. Criterion 5 is three rows over four todos created alternately on the ticking clock. Criterion 13 is four rows, and each asserts `todo_id`. The Interface rules are covered: the clock stamp (1), no filter on `done=None` (5) and creation order (4, 5). Errors pass through for a blank title on create and on rename (2, 7) and for an unknown id on every operation (3, 13). The default clock is `utc_now` (14, 15). The Interface states no limit of its own; the 200-character title rule belongs to the domain and is tested in S0001. The coder's `make check` was green (journal entry 7).
   - Architecture: `app.service` imports only `app.domain.model` and `app.domain.repository`, and reaches storage only through the `TodoRepository` protocol.
   - Security: there is nothing to flag, and no suppression markers were added.

   Group 4 (quality) fails on the test file:

   1. `tests/service/test_todo_service.py:13`: `NOON = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)` is a third copy of the existing constant `T0`, which has the same value in `tests/domain/test_model.py:11` and `tests/repository/test_contract.py:13`. The tester's entry chose to keep this copy. CLAUDE.md's standing leave covers constants as well as helpers, and a second copy of an existing helper counts as a finding. Fix: the tester moves `T0` to one shared place under `tests/`, such as `tests/fakes.py` (or `tests/conftest.py`). The two earlier modules and the service tests then import it from there, and every earlier test keeps its name and what it checks.

   I rejected two other possible findings:
   - The criterion pairs 8/9 and 10/11 as separate test functions: the intake defined them as separate criteria, and each checks something different (the change and its readback, against idempotence without an error).
   - The method name `list` shadowing the builtin: the Interface sets that name.

   Group 5 was not reached because group 4 failed.

   Earlier tests: none. The diff adds test files only (status `A`) and changes no test file that `main` already holds.
10. factory: started doing as demo.
11. coder: Round 1. The reviewer's single finding (entry 9, group 4) is in the tests, not in the code, so I changed no code and no test.

    Requested change, under the standing leave in CLAUDE.md to move a shared test constant: move the constant `datetime(2026, 10, 4, 12, 0, tzinfo=UTC)` to one shared place under `tests/`. Today it is defined three times:
    - `T0` in `tests/domain/test_model.py:11`
    - `T0` in `tests/repository/test_contract.py:13`
    - `NOON` in `tests/service/test_todo_service.py:13`

    There is no `tests/fakes.py` and no `tests/conftest.py` yet. A plain module constant, for example `T0` in a new `tests/fakes.py`, fits better than a fixture, since all three files use it as a module-level value. All three test modules should then import it from there, and every earlier test keeps its name and what it checks. The tester's entry names each earlier test file it changed.

    Built: nothing new this round. The service layer from entry 7 (`src/app/service/__init__.py`, `src/app/service/todo_service.py`) stays as it is. The reviewer passed groups 1 to 3 on it.

    Main choice: I hand this to the tester (`tests`) rather than asking the human (`question`). The rejected alternative was a `question`, which is not needed: CLAUDE.md gives standing leave for moving a shared test constant, and the coder may not make the move.

    Noticed, not touched: `tests/domain/test_model.py:125` uses naive datetimes with the same date and time. That is test data for the rule that refuses times without a usable UTC offset, not a copy of the constant, so it should stay as it is. The journal did not change the meaning of the description.
