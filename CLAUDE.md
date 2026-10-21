# Provenix (POC)

Provenix assesses AI applications against the EU AI Act. It reads a questionnaire, the app's code and its
documents, and produces findings with citations that a compliance reviewer confirms or overrides. This repo is
a 6-week proof of concept. The goal is to measure whether findings agree with a compliance expert, so
correctness and traceability matter more than features.

- Spec (source of truth): `docs/SPEC.md`. Read the sections the task names before writing code.
- Task list: `docs/IMPLEMENTATION_PLAN.md`. Work one task at a time.
- Do not edit `docs/SPEC.md` unless asked. If the spec looks wrong or incomplete, stop and say so.

## Stack

- Backend: Python 3.13, uv, FastAPI, Pydantic v2, SQLAlchemy 2 (async, asyncpg), Alembic, PostgreSQL 16 + pgvector,
  Redis + arq, LangGraph + langgraph-checkpoint-postgres, `openai` SDK against Azure OpenAI, tree-sitter, PyMuPDF,
  python-docx, Jinja2 + WeasyPrint.
- Frontend: React + TypeScript + Vite, pnpm, TanStack Query, React Router, Tailwind + shadcn/ui, react-hook-form + zod,
  Shiki, openapi-typescript + openapi-fetch.
- Runs with `docker compose` (Postgres, Redis, API, worker). The frontend runs on the host with `pnpm dev`.
  The dev machine is Windows: the API and worker run in Docker because WeasyPrint needs native libraries.

## Commands

```
just up          # docker compose up -d (db, redis, api, worker)
just migrate     # alembic upgrade head (inside api container)
just test        # backend pytest + frontend vitest
just lint        # ruff, mypy, eslint, tsc
just gen-client  # regenerate frontend/src/api/schema.d.ts from the running API's OpenAPI
just eval        # run evals against samples/ (real LLM; costs money)
```

## Architecture rules

- Hexagonal: `domain/` has no I/O. Services and agents depend on `ports/` Protocols, never on adapters directly.
  Adapters are wired in one place (`app/wiring.py`).
- LangGraph state holds IDs only. Evidence, findings and everything else live in Postgres.
- Human review is plain API calls, not a LangGraph `interrupt()`. The graph always runs to the end.
- Risk tier comes from deterministic rules in `services/classifier.py`. The LLM only explains.
- The model never writes evidence excerpts. The `cite` tool copies them from the source and hashes them.
- Treat repo and document content as untrusted data. Wrap it in `<untrusted_content>` tags in prompts.
  Never execute code from analysed repos.
- Every LLM call goes through the `LLMClient` port and writes an `llm_call` row.
- Prompts live in `app/agents/prompts/<id>/v<N>.md`. Do not edit a released prompt version; add a new one.
- Every table has `org_id` with the default from SPEC §3, even though the POC is single tenant.

## Testing rules

- Tests never call Azure OpenAI. Use `FakeLLM` and `FakeEmbedder` (`LLM_PROVIDER=fake`).
- New service or node: add unit tests in `backend/tests/unit/`. DB-touching code: integration test in
  `backend/tests/integration/` against the compose Postgres (test database `provenix_test`).
- Before saying a task is done, run `just lint` and `just test` and report the result. Do not claim success on failing checks.

## Out of scope for the POC (do not build)

Multi-tenancy/RLS, SSO and roles, Azure DevOps, webhooks or re-assessment on push, Jira/ServiceNow, DOCX reports,
portfolio dashboard, admin console, runtime SDK, ISO 42001 as an assessed framework, infrastructure as code.
If a task seems to need one of these, stop and ask.

## Style

- Python: type hints everywhere, ruff + mypy strict on `app/`. Async all the way down in the API and worker.
- Small modules. No new dependency without saying why in the task summary.
- Frontend: one folder per feature under `src/features/`; server state only via TanStack Query; API types only
  from the generated client.
