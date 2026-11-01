---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 3
comments_read: [6558637547]
handed_over: null
claim:
  instance: demo
  stage: doing
  started_at: '2026-11-01T13:35:27.412919Z'
  lease_duration: 60
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
25. `make check` stays green.
26. docs: `docs/api.md` describes each endpoint (method, path, body, success and error statuses), the title rules, the error body `{"detail": "…"}` and the `PATCH` rules, with a curl example for creating and for listing; the README's *Getting started* shows how to start the server and names `/docs` for the interactive schema, and its *Where to look next* links `docs/api.md`.

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
