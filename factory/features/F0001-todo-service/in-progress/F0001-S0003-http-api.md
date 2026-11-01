---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 3
comments_read: [6558637547]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T13:29:55.453830Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T13:29:55.457920Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-01T13:30:26.624434Z'
  stage: intake
  run: 085fc987f31946dfa603100e12c56b3c
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-01T13:32:44.265454Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-01T13:33:01.604412Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-01T13:33:17.776787Z'
  stage: intake
  run: ee508e4f74e6427a8bef18c5ef189992
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-01T13:33:38.055038Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-01T13:35:07.306030Z'
  stage: tests
  run: 8dac314487e248a3b4c6ff0b15e2a7cd
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-01T13:35:27.412919Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-01T13:36:51.241268Z'
  stage: doing
  run: 800a94e7b594474386769153ef02f172
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-01T13:37:11.104448Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:38:13.235363Z'
  stage: review
  run: e02ed2cc132e4ac5b08f286bb2d7a289
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-01T13:38:33.029449Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-01T13:38:48.101397Z'
  stage: doing
  run: 12a412f363614803b5fed96f94c13473
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-01T13:39:08.132668Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-01T13:39:43.469056Z'
  stage: tests
  run: 60dc2cb9215d4906a5090d5ed189eaa0
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-01T13:40:03.442435Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-01T13:40:32.562223Z'
  stage: doing
  run: f82ec623f7e949f98e2b7ed425354df1
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-01T13:40:52.349871Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-01T13:41:31.175193Z'
  stage: review
  run: 39ac13020f634e03a6ae9694f20e08d8
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-01T13:41:51.261350Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-11-01T13:42:34.202745Z'
  stage: docs
  run: f1a2267bfba44cebb933cae03dc87ef7
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-01T13:42:54.243434Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-11-01T13:43:18.663539Z'
  stage: smoke-test
  run: 1e11806299374f718c6247cdd5fb5e16
---

# HTTP API

## Description

Expose the service over HTTP with FastAPI: create, list (optionally filtered by `done`), read, update and delete todos as JSON. Pydantic schemas at the edge, one error shape for every error (`{"detail": "<one sentence>"}`), errors mapped to status codes in one place, and the concrete repository chosen only in the composition root, still in memory. The OpenAPI schema is committed as `docs/openapi.json`, which the coder writes with `make openapi` (the one file under `docs/` in the coder's write paths). Single user, no authentication.

## Interface

`src/app/api/schemas.py`

```python
class TodoCreate(BaseModel):
    title: str

class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

class TodoRead(BaseModel):
    id: UUID
    title: str
    done: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, todo: Todo) -> "TodoRead": ...
```

The schemas put no length or blank rule on `title`: the domain's rule applies, after stripping, with the domain's message. A `TodoUpdate` that sets neither field (both absent or `null`) is rejected with 422. A field sent as `null` counts as not set.

`src/app/api/dependencies.py`

```python
def get_service(request: Request) -> TodoService: ...
Service = Annotated[TodoService, Depends(get_service)]
```

`get_service` returns the service `create_app` was given; every router takes the service through `Service`.

`src/app/api/errors.py`

```python
def register_error_handlers(app: FastAPI) -> None: ...
```

| Raised | Status | Body |
| :- | -: | :- |
| `TodoNotFound` | 404 | `{"detail": "todo <id> not found"}` (the error's message) |
| `InvalidTitle` | 422 | `{"detail": "<the error's message>"}` |
| `RequestValidationError` | 422 | `{"detail": "<location>: <message>"}` of the first error, the location joined with dots, e.g. `body.title: Field required` |

`src/app/api/routes.py`: `router = APIRouter(prefix="/todos", tags=["todos"])`

| Method | Path | Body | Success | Errors |
| :- | :- | :- | :- | :- |
| POST | `/todos` | `TodoCreate` | 201, `TodoRead` | 422 |
| GET | `/todos`, optional query `done=true\|false` | | 200, `list[TodoRead]` in creation order | 422 |
| GET | `/todos/{todo_id}` | | 200, `TodoRead` | 404, 422 |
| PATCH | `/todos/{todo_id}` | `TodoUpdate` | 200, `TodoRead` | 404, 422 |
| DELETE | `/todos/{todo_id}` | | 204, empty body | 404, 422 |

`PATCH` applies `title` first (rename), then `done` (`true` completes, `false` reopens), so an invalid title changes nothing.

`src/app/api/app.py`

```python
def create_app(service: TodoService) -> FastAPI: ...   # titled "Todo service"; stores the service, includes the router, registers the handlers
```

`src/app/api/main.py`

```python
app = create_app(TodoService(InMemoryTodoRepository()))   # the only module that imports app.repository
```

Run with `uv run uvicorn app.api.main:app --port 8765`. `make openapi` writes `docs/openapi.json` from `app.api.main:app`; the coder runs it after the routes exist.

Tests: `tests/api/test_todos.py` through FastAPI's `TestClient` against `create_app(TodoService(InMemoryTodoRepository()))` from a fixture; `tests/api/test_openapi.py` (criteria 21 and 22); `tests/api/test_imports.py` (criterion 23, naming only the forbidden import).

## Acceptance criteria

1. `POST /todos` with `{"title": "Buy milk"}` returns 201 and a body with exactly the keys `id`, `title`, `done`, `created_at`: a UUID, `"Buy milk"`, `false`, and an ISO 8601 timestamp whose offset is UTC (`Z` or `+00:00`).
2. `POST /todos` with `{"title": "   "}` returns 422 and the body `{"detail": "title must not be blank"}`.
3. The length rule on both sides, as rows of one parametrized test: `POST /todos` with a 200-character title returns 201; with a 201-character title it returns 422 and the body `{"detail": "title must be at most 200 characters"}`.
4. `POST /todos` with `{}` returns 422 and the body `{"detail": "body.title: Field required"}`.
5. `GET /todos` returns 200 and every todo, in creation order.
6. The done filter, as rows of one parametrized test: `GET /todos?done=true` returns only the completed todos, and `GET /todos?done=false` only the open ones.
7. `GET /todos?done=maybe` returns 422 and a body whose only key is `detail`, a string starting with `query.done: `.
8. `GET /todos/{id}` for a known id returns 200 and that todo.
9. `GET`, `PATCH` (with `{"done": true}`) and `DELETE` of `/todos/not-a-uuid` each return 422 and a body whose only key is `detail`, a string starting with `path.todo_id: `: three rows of one parametrized test.
10. `PATCH /todos/{id}` with `{"done": true}` returns 200 and the todo completed; a following `PATCH` with `{"done": false}` returns it open.
11. `PATCH /todos/{id}` with `{"title": " New title "}` returns 200 and the todo titled `New title`, with the same id, done flag and `created_at` as before.
12. `PATCH /todos/{id}` with `{}`, `{"title": null}`, `{"done": null}` and `{"title": null, "done": null}` (four rows of one parametrized test) returns 422 and a body whose only key is `detail`, a string; a `GET` of the todo afterwards shows it as before.
13. `PATCH /todos/{id}` with `{"title": "   ", "done": true}` returns 422 and the body `{"detail": "title must not be blank"}`; a `GET` afterwards shows the old title and the todo still open.
14. `PATCH /todos/{id}` with `{"title": " New title ", "done": true}` on an open todo returns 200 and the todo titled `New title` and completed, with the same id and `created_at`; a `GET` afterwards shows both changes.
15. `DELETE /todos/{id}` returns 204 with an empty body, and a `GET` of that id returns 404 afterwards.
16. `GET`, `PATCH` (with `{"done": true}`) and `DELETE` of `/todos/{id}` for an unknown id each return 404 and the body `{"detail": "todo <id> not found"}`, the id in its hyphenated form: three rows of one parametrized test.
17. The routes use the service given to `create_app`: a todo created directly through that service is returned by `GET /todos`.
18. The API is called `Todo service`: `app.openapi()["info"]["title"]` of `create_app(service)` is `"Todo service"`.
19. `get_service` hands each route the service of its own app: two apps built by `create_app` on two services each list only the todos of their own service.
20. Every error body the API returns has `detail` as its only key: the bodies of criteria 2, 4, 7, 9 and 16 are dicts with exactly the key `detail`, never a list.
21. `docs/openapi.json`, parsed as JSON, equals `app.openapi()` of `app.api.main.app`.
22. The schema of `app.api.main.app` names the paths `/todos` and `/todos/{todo_id}` with the tag `todos`.
23. Of the `app.api` modules, only `app.api.main` imports `app.repository`.
24. `POST /todos` with `{"title": "  Buy milk "}` returns 201 and the title `Buy milk`.
25. A field sent as `null` beside a set one counts as not set, as rows of one parametrized test: `PATCH /todos/{id}` on an open todo with `{"title": null, "done": true}` returns 200 and the todo completed with its old title; with `{"title": " New title ", "done": null}` it returns 200 and the todo titled `New title`, still open; a `GET` afterwards shows the same.
26. `make check` stays green.
27. docs: `docs/api.md` describes each endpoint (method, path, body, success and error statuses), the title rules, the error body `{"detail": "…"}` and the `PATCH` rules, with a curl example for creating and for listing; the README's *Getting started* shows how to start the server and names `/docs` for the interactive schema, and its *Where to look next* links `docs/api.md`.

## Smoke test

```bash
d=$(mktemp -d); trap 'kill $pid 2>/dev/null; wait $pid 2>/dev/null; rm -rf "$d"' EXIT
uv run uvicorn app.api.main:app --port 8765 >"$d/uvicorn.log" 2>&1 & pid=$!
for i in $(seq 40); do curl -s -o /dev/null localhost:8765/todos && break; sleep 0.5; done
ID=$(curl -s -X POST localhost:8765/todos -H 'content-type: application/json' -d '{"title":"  Buy milk "}' | uv run python -c "import json, sys; print(json.load(sys.stdin)['id'])")
curl -s -X PATCH localhost:8765/todos/$ID -H 'content-type: application/json' -d '{"done":true}'; echo
curl -s 'localhost:8765/todos?done=false'; echo
curl -s -X POST localhost:8765/todos -H 'content-type: application/json' -d '{"title":"   "}'; echo
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE localhost:8765/todos/$ID
curl -s localhost:8765/todos/$ID; echo
```

Expect: five lines: the todo as JSON with `"title":"Buy milk"` and `"done":true`; then `[]`; then `{"detail":"title must not be blank"}`; then `204`; then `{"detail":"todo <the same id> not found"}`.

## Journal

1. 2026-11-01 human: created.
2. factory: started intake as demo.
3. intake: Format check passed. One finding from the rule that every Interface behaviour has its own criterion:

   1. The Interface says the title rule applies "after stripping" on any title the schemas receive. Criterion 11 tests stripping on PATCH, but no criterion tests it on `POST /todos`. Only the smoke test sends a padded title there, and that is not a test. Should I add a criterion such as "`POST /todos` with `{"title": "  Buy milk "}` returns 201 and the title `Buy milk`"? I would choose to add it, placed before the two closing criteria. I have not edited the story.

   Everything else checked out:
   - Interface: concrete modules and signatures.
   - Criteria: each is testable by one test; the failing sides are covered (2, 3, 4, 7, 9, 12, 13, 16); the 200/201 limit is a parametrized row pair.
   - Smoke test: runnable, and its `Expect:` line is checkable. It runs no pytest, so the `-q` rule does not apply.
   - Architecture: the layering fits, and only `main` imports `app.repository`.
   - Scope: within the feature, and `make openapi` exists in the Makefile.
4. 2026-11-01 human: Yes, as you propose: add the criterion `POST /todos` with `{"title": "  Buy milk "}` returns 201 and the title `Buy milk`, placed before the two closing criteria. It follows from the Interface's rule that every title is checked after stripping.
5. factory: started intake as demo.
6. intake: accepted
   - Interface: concrete modules and signatures (schemas, dependencies, errors, routes, app, main); the status and error tables are explicit. Every stated behaviour has a criterion, now including stripping on POST.
   - Criteria: each is testable by one test function. Each rule has both sides: blank title (2), length 200/201 (3), missing field (4), bad filter (7), bad uuid (9), empty PATCH (12), invalid title changes nothing (13), unknown id (16). The new criterion 24 covers stripping on POST.
   - Smoke test: runnable and runs no pytest, so the `-q` rule does not apply. The `Expect:` line gives five checkable lines.
   - Architecture: api → service → domain. Only `app.api.main` imports `app.repository` (criterion 23), and errors are mapped in one place.
   - Scope: within F0001's HTTP API scope, with nothing from its Out of scope. Decisions 6, 7, 9, 10, 11 and 12 are covered by criteria.

   Carried in from journal entry 4 (the human's answer): I added criterion 24, "`POST /todos` with `{"title": "  Buy milk "}` returns 201 and the title `Buy milk`", before the two closing criteria. `make check` is now criterion 25 and `docs:` is 26. The Interface's references to criteria 21–23 are unchanged. I made no other edits.
7. factory: started tests as demo.
8. tester: I wrote one test for each acceptance criterion. All tests go through FastAPI's `TestClient` against `create_app(TodoService(InMemoryTodoRepository(), clock=ticking_clock()))`, built in a fixture. I used the ticking clock so that the order in which todos are created is deterministic.

   - criterion 1: tests/api/test_todos.py::test_create_returns_the_new_open_todo
   - criterion 2: tests/api/test_todos.py::test_create_with_a_blank_title_is_rejected
   - criterion 3: tests/api/test_todos.py::test_create_enforces_the_title_length_limit (rows 200 → 201, 201 → 422)
   - criterion 4: tests/api/test_todos.py::test_create_without_a_title_names_the_missing_field
   - criterion 5: tests/api/test_todos.py::test_list_returns_every_todo_in_creation_order
   - criterion 6: tests/api/test_todos.py::test_list_filters_by_done (rows true, false)
   - criterion 7: tests/api/test_todos.py::test_list_with_an_invalid_done_filter_is_rejected
   - criterion 8: tests/api/test_todos.py::test_get_returns_the_known_todo
   - criterion 9: tests/api/test_todos.py::test_an_id_that_is_not_a_uuid_is_rejected (rows GET, PATCH, DELETE)
   - criterion 10: tests/api/test_todos.py::test_patch_done_completes_and_reopens_the_todo
   - criterion 11: tests/api/test_todos.py::test_patch_title_renames_the_todo_and_keeps_the_rest
   - criterion 12: tests/api/test_todos.py::test_patch_that_sets_no_field_is_rejected_and_changes_nothing (four rows)
   - criterion 13: tests/api/test_todos.py::test_patch_with_a_blank_title_changes_nothing
   - criterion 14: tests/api/test_todos.py::test_patch_title_and_done_applies_both
   - criterion 15: tests/api/test_todos.py::test_delete_removes_the_todo
   - criterion 16: tests/api/test_todos.py::test_an_unknown_id_is_not_found (rows GET, PATCH, DELETE)
   - criterion 17: tests/api/test_todos.py::test_routes_use_the_service_given_to_create_app
   - criterion 18: tests/api/test_todos.py::test_the_api_is_called_todo_service
   - criterion 19: tests/api/test_todos.py::test_each_app_lists_only_the_todos_of_its_own_service
   - criterion 20: tests/api/test_todos.py::test_every_error_body_has_detail_as_its_only_key (one row per request from criteria 2, 4, 7, 9 and 16)
   - criterion 21: tests/api/test_openapi.py::test_committed_openapi_schema_is_up_to_date
   - criterion 22: tests/api/test_openapi.py::test_schema_names_the_todo_paths_with_the_todos_tag
   - criterion 23: tests/api/test_imports.py::test_only_main_imports_the_repository_layer (it names only the forbidden `app.repository`)
   - criterion 24: tests/api/test_todos.py::test_create_strips_the_title
   - criteria 25 and 26: the factory's check and the docs stage; no tests.

   Files I created: tests/api/__init__.py, tests/api/test_todos.py, tests/api/test_openapi.py, tests/api/test_imports.py, tests/imports.py.

   I moved two shared helpers under the standing leave in CLAUDE.md *Tests*. Each earlier test keeps its name and checks the same thing:
   - The ticking clock moved from tests/service/test_todo_service.py into tests/fakes.py as `ticking_clock`. I changed tests/service/test_todo_service.py to import it from there.
   - The AST import reader moved from tests/domain/test_imports.py into the new tests/imports.py as `imported_modules`. It now works out the package from the path under `src/` instead of a fixed `app.domain` prefix. I changed tests/domain/test_imports.py to use it.

   Result of `make test`:
   - The test runner could not import `app.api.app` (tests/api/test_todos.py) or `app.api.main` (tests/api/test_openapi.py), so both modules give collection errors.
   - test_only_main_imports_the_repository_layer fails because `src/app/api` has no sources yet.
   - All 81 earlier tests pass.

   `make lint` is green. Nothing in the criteria needed interpreting, so I have no question open.

   `lint`: lint: green (0.0 s)
   `test`: 1 failed, 81 passed, 4 warnings, 2 errors in 1.44s
9. factory: started doing as demo.
10. coder: I built the HTTP API in the modules the Interface names. I wrote no tests and changed none. `make check` is green: 122 tests pass and coverage is 100%.

    What I built:
    - `src/app/api/__init__.py`: package docstring.
    - `src/app/api/schemas.py`: `TodoCreate`, `TodoUpdate` and `TodoRead.from_domain`.
      - The schemas put no rule on `title`, so the domain's rule and messages apply.
      - `TodoUpdate` has an after-validator that rejects a body setting neither field. That error becomes a `RequestValidationError` with the location `body`, so it returns 422.
    - `src/app/api/dependencies.py`: `get_service` reads the service from `request.app.state.service`; `Service` is the `Annotated` alias.
    - `src/app/api/errors.py`: one table, `STATUS_BY_ERROR` (`TodoNotFound` → 404, `InvalidTitle` → 422), with one handler that uses the error's message as `detail`. For a `RequestValidationError`, `detail` is the first error's location joined with dots, then `: ` and its message.
    - `src/app/api/routes.py`: the five endpoints. `PATCH` renames first, then completes or reopens, so a title the domain refuses changes nothing.
    - `src/app/api/app.py`: `create_app`, titled "Todo service".
    - `src/app/api/main.py`: the composition root, using `InMemoryTodoRepository`.
    - `docs/openapi.json`: written by `make openapi`.

    Main choice: I register the handlers with FastAPI's decorator form, `app.exception_handler(cls)(handler)`, so each handler can take its own error class as its parameter type. I rejected `add_exception_handler`: Starlette types its handler as `(Request, Exception)`, so it needs either an `isinstance` assert (which ruff's S101 flags) or a cast. I also rejected one handler for the `TodoError` base class. `DuplicateTodo` has no status in the Interface and should not be given one silently.

    Refactor: I renamed `_error_body` to `_error_response`, because it returns a response, not a body. Nothing else needed changing.

    Noticed, not touched:
    - `PATCH` reads the todo once more before applying the changes, so that the handler always has a todo to return. Each service call then reads it again, which costs one extra read in memory.
    - The test client prints a `StarletteDeprecationWarning` about `httpx` versus `httpx2`. It comes from the pinned dependencies and is outside this work item.
    - No journal entry changed the task's meaning, so I left the Description as it is.

    `check`: check: green
    `duplicates`: duplicates: 0 similar code, 6 dead code, in .reports/
11. factory: started review as demo.
12. reviewer: Review, round 0. I read the work item, the diff stat and `git diff main...HEAD -- . ':!factory' ':!docs/openapi.json'`. Then I went through criteria 1–24 and through every rule in the Interface, one by one. Group 1 (acceptance criteria) fails because of one gap, so I stopped there, as the checklist says.

    1. criterion 25 added: it needs its test. The Interface says "A field sent as `null` counts as not set". Criterion 12 tests only the refused side of that rule (every field is null, so the request gets 422). No criterion tests the accepted side: a `null` field sent beside a set one. The code already handles it: `src/app/api/routes.py:29-38` skips any field that is `None`. Without a test, a later change could break this unnoticed, for example one that reads `model_fields_set` and calls `rename(None)`. The new criterion 25 sits before the two closing criteria, which are now 26 (`make check`) and 27 (`docs:`). It has two rows of one parametrized test. `{"title": null, "done": true}` must complete the todo and keep its old title. `{"title": " New title ", "done": null}` must rename it to `New title` and leave it open. In both rows, a `GET` afterwards must show the same todo. Fix: the coder hands this to the tester, who adds the test to `tests/api/test_todos.py`. No change under `src/` is needed.

    Checked and fine:
    - Every criterion from 1 to 24 has a test named after it that tests what the criterion says.
    - The 200/201 length limit is tested on both sides, as rows of one parametrized test.
    - The coder's `make check` was green (entry 10).

    Earlier tests:
    - `tests/domain/test_imports.py`: changed under the standing leave to move a shared test helper. The AST import reader moved to `tests/imports.py` as `imported_modules`. For files under `app/domain` it gives the same package prefix as before. The test keeps its name and checks the same thing.
    - `tests/service/test_todo_service.py`: changed under the same standing leave. `_ticking_clock` moved to `tests/fakes.py` as `ticking_clock`. Every test keeps its name and checks the same thing.
    - `tests/fakes.py`: changed under the same standing leave. It is the shared place, and the only change is the added `ticking_clock`.
13. factory: started doing as demo.
14. coder: Round 1. This round has one finding: the reviewer added criterion 25, and it needs only a test. I changed no code and no tests.

    Criterion 25 for the tester: one parametrized test in `tests/api/test_todos.py` with two rows. In both rows the request is `PATCH /todos/{id}` on an open todo.
    - `{"title": null, "done": true}` returns 200 and the todo completed, with its old title.
    - `{"title": " New title ", "done": null}` returns 200 and the todo titled `New title`, still open.
    - In both rows, a `GET` afterwards shows the same todo.

    `tests/api/test_todos.py` has no test that sends a `null` field yet. The code needs no change: `src/app/api/routes.py` already skips a field that is `None`. When the new test is in place, the work item should pass `make check` without any change under `src/`.

    Built: nothing new this round. The paths from entry 10 stay as they were.
    - Main choice: hand the work item to the tester and change no code. I rejected changing `src/`, because the finding is about a missing test, not about how the code behaves.
    - Description: the reviewer already added criterion 25 and renumbered the closing criteria to 26 and 27. No journal entry changed the task otherwise, so I left the Description alone.
    - Noticed, not touched: nothing new beyond entry 10. That is the extra read in `PATCH` and the `StarletteDeprecationWarning` from the pinned dependencies.
15. factory: started tests as demo.
16. tester: Round 1, tests: I wrote the test for criterion 25, the one the reviewer added and the coder handed over in entry 14. I edited no earlier test.

    - criterion 25: `tests/api/test_todos.py::test_patch_ignores_a_null_field_beside_a_set_one`. It is one parametrized test with two rows. Each row creates an open todo titled `Old title` and sends `PATCH /todos/{id}`:
      - `{"title": null, "done": true}` must return 200 and the todo completed, with the title `Old title`.
      - `{"title": " New title ", "done": null}` must return 200 and the todo titled `New title`, still open.
      - In both rows, the body must equal the todo from before with only those fields changed, and a `GET` afterwards must return the same body.

    Files: I created no new file. I added this one test to `tests/api/test_todos.py`, the test module this story already has, and reused its `client` fixture.

    Imports: every module imported. As the coder said, the code already does this, so the new test passes rather than failing first. `make test` gave 124 passed, coverage 100%. `make lint` is green.

    Open: nothing. I needed no interpretation: the criterion names both rows and the `GET` check.

    `lint`: lint: green (0.0 s)
    `test`: test: green (2.3 s)
17. factory: started doing as demo.
18. coder: Round 1 (back from the tests stage). The only finding this round was criterion 25. The tester has now added its test: `tests/api/test_todos.py::test_patch_ignores_a_null_field_beside_a_set_one`. I ran `make check` and it is green: 124 tests pass and coverage is 100%. The new test passes against the code from round 0, because `src/app/api/routes.py` already skips any field sent as `None`.

    - Built: nothing new this round. I changed no code and no tests. The paths from entry 10 still apply.
    - Main choice: I handed the work item to review unchanged. I rejected touching `src/`, because the finding was a missing test and the code already behaves as criterion 25 requires.
    - Refactor: no change to the code since entry 10, where I already did the refactor, so there was nothing new to refactor.
    - Description: the reviewer added criterion 25 and the closing criteria are now 26 and 27. No journal entry changed the task otherwise, so I left the Description as it is.
    - Noticed, not touched: the same as entry 10. `PATCH` reads the todo once more before applying the changes, and the test client prints a `StarletteDeprecationWarning`, which comes from the pinned dependencies.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 similar code, 6 dead code, in .reports/
19. factory: started review as demo.
20. reviewer: Review, round 1. I read the work item, the diff stat, the name-status list and `git diff main...HEAD -- . ':!factory' ':!docs/openapi.json'`. I went through criteria 1–25 and every rule of the Interface one at a time, then through groups 2–5.

    no findings

    What I checked:
    - Group 1, acceptance criteria:
      - Every criterion from 1 to 25 has a test in `tests/api/test_todos.py`, `tests/api/test_openapi.py` or `tests/api/test_imports.py`, and each test checks what its criterion says.
      - Criterion 25, added last round, is `test_patch_ignores_a_null_field_beside_a_set_one`. It has two rows of one parametrized test, and in both rows the `GET` afterwards must equal the response.
      - Each stated limit and rule is tested on both sides. Title length is tested at 200 and 201 as rows of one test. A blank title is tested on POST (2) and on PATCH (13). A body that sets no field (12) is tested against a null field beside a set one (25). A bad filter (7) is tested against valid filters (6). An id that is not a UUID (9) and an unknown id (16) are tested against a known id (8, 10, 11).
      - The coder's `make check` was green (entry 18: 124 passed, coverage 100%).
    - Group 2, architecture:
      - `app.api` imports `app.service` and `app.domain` (the errors and `Todo`). Only `src/app/api/main.py` imports `app.repository`.
      - Errors map to status codes in one place: `STATUS_BY_ERROR` and the two handlers in `src/app/api/errors.py`.
      - Pydantic is used at the edge, and the service comes in through `Service`/`get_service` from `app.state`.
    - Group 3, security:
      - No secrets, and no shell or SQL built from strings.
      - Input is validated by the schemas and by FastAPI's path and query types.
      - Error bodies carry only the domain message or the first validation location and message.
      - The diff adds no suppression markers.
    - Group 4, quality:
      - The names fit and every module has a docstring.
      - The comments explain why: the order of the PATCH steps, and the decorator form of the handlers.
      - `docs/openapi.json` is checked by criterion 21.
      - The extra `service.get` in `update_todo` (`src/app/api/routes.py:31`) is a small read cost the coder noted. It is not dead code: it gives the handler a todo to return.
    - Group 5, work item hygiene:
      - The Description matches what was built.
      - The journal gives the main choice (the decorator-form handlers) and what was rejected (`add_exception_handler`, and one handler for the `TodoError` base class).
      - Docs criterion 27 still says what a reader needs.

    Earlier tests:
    - `tests/domain/test_imports.py`: changed under the standing leave to move a shared test helper. `_imported_modules` moved to `tests/imports.py` as `imported_modules`. For files under `app/domain` it gives the same package prefix as before. The test keeps its name and checks the same thing.
    - `tests/service/test_todo_service.py`: changed under the same standing leave. `_ticking_clock` moved to `tests/fakes.py` as `ticking_clock`. Every test keeps its name and checks the same thing.
    - `tests/fakes.py`: changed under the same standing leave. It is the shared place, and the only change is the added `ticking_clock`.
21. factory: started docs as demo.
22. documenter: Docs, round 1. This is the first documentation pass for this story: docs/api.md did not exist, and the rework rounds so far were for the tests. I found no contradiction between the code and the Interface, so there are no findings.

    Files changed (documents only, so I did not run `make check`; the factory's checks decide):
    - `docs/api.md` (new): every endpoint with method, path, body and success/error statuses; the done filter; the title rules (strip, blank, 200/201); the PATCH rules (null counts as not set, empty body is 422, title first so a refused title changes nothing); the single error body `{"detail": "…"}` with its three cases; curl examples for create and list.
    - `README.md`: Getting started now shows the uvicorn command and names `/docs`. Where to look next links `docs/api.md`.
    - `docs/project-guide.md`: replaced the sentence "The API layer ... is built by a later story" with the current state and a pointer to `docs/api.md` and `src/app/api/`.

    Examples run: I started the server with the uvicorn command and ran the two curl examples (create with a padded title returns the stripped `Buy milk`; `?done=false` lists it). `/docs` returned 200.

    Cross-read and found current: the layer table, the domain model, title rules and service sections of `docs/project-guide.md` against the diff, and `docs/openapi.json` (generated, not touched; criterion 21 tests it).

    Stale text I noticed and left: the README's opening paragraph says todos are "kept in memory or in a SQLite file". SQLite storage is not built yet, so for now only memory is true. I added a sentence in Getting started saying todos are in memory, but left the intro alone. A later storage story should correct it.

    `check`: check: green
23. factory: started smoke-test as demo.
24. smoke-tester: I ran the `## Smoke test` block exactly as written, from the repository root, as one bash script. The server started in the background, answered within the wait loop and was stopped by the script's trap. The script exited 0 and left nothing behind in `/tmp`, and nothing was listening on port 8765 afterwards.

    Output (5 lines, nothing trimmed):

    ```
    {"id":"2e3809a7-6f5f-4545-b950-df2227ad6ed6","title":"Buy milk","done":true,"created_at":"2026-11-01T13:43:08.259132Z"}
    []
    {"detail":"title must not be blank"}
    204
    {"detail":"todo 2e3809a7-6f5f-4545-b950-df2227ad6ed6 not found"}
    ```

    Result against `Expect:` — met, line by line:
    1. PATCH `{"done":true}` returned the todo as JSON with `"title":"Buy milk"` and `"done":true`. Also checked: the POST stripped the title `"  Buy milk "` (criterion 24); the body has exactly the keys `id`, `title`, `done`, `created_at`; and `created_at` is ISO 8601 with a `Z` offset (criterion 1).
    2. `GET /todos?done=false` returned `[]`, which is right because the only todo is completed (criterion 6).
    3. POST with a blank title returned `{"detail":"title must not be blank"}` (criterion 2).
    4. DELETE returned `204` (criterion 15).
    5. GET of the deleted id returned `{"detail":"todo <same id> not found"}`, with the id in hyphenated form (criteria 15 and 16).

    Acceptance criteria re-read: the output contradicts none of them. The error bodies have `detail` as their only key (criterion 20). The smoke test does not exercise criteria 26 (`make check`) or 27 (docs), and I did not judge them here because the factory runs the checks.

    Findings: none.

    Nothing fixed or changed. Nothing open.
