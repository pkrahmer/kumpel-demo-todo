# To-do service

A single-user to-do service with an HTTP API: create todos, list and filter them, rename, complete, reopen and delete them, kept in memory or in a SQLite file. It is being built story by story; this README grows with it.

## Getting started

```bash
uv sync       # install
make check    # everything the pipeline checks: lint, types, layers, static analysis, secrets, licences, tests
```

## Where to look next

- `docs/project-guide.md`: the layers and their reasons, the domain model, the repository protocol
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)

## How it is built

Built by the factory (github.com/pkrahmer/factory): features and their stories live under `factory/features/`, one folder per feature, and one stage agent at a time takes a story through tests, code, review, docs and a smoke test. A story's pull request carries the whole story; merging it accepts the story.
