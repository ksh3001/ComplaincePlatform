# Provenix POC — Implementation Plan (vibe-coding edition)

33 tasks (T00–T32) in 8 milestones, sized so that each one fits a single AI coding session (roughly 30–90 minutes).
Each task has a prompt you can paste, the spec sections it relies on, and a **Done when** check that you
verify yourself before committing.

Calendar fit: M0–M1 = week 1, M2–M3 = week 2, M4 = week 3, M5 = week 4, M6 = week 5, M7 = week 6.

---

## Scope control (POC scale)

The POC question is "do findings agree with an expert?". Anything that does not feed that measurement is
cuttable. If you are more than ~3 days behind at the end of a milestone, cut in this order:

1. **T24 tracing** — `llm_call` is enough.
2. **T15 app C** — keep app D (false-positive test); app C is the third gap-bearing app.
3. **T28 PDF report** — fall back to a single HTML page printed to PDF; drop the per-finding pages.
4. **T25 SSE timeline** — fall back to polling `GET /assessments/{id}` every 2 s.

Further trims (spec §4, §12, §14 need a matching edit by you when adopted):
- **T09/T14:** onboarding may be one or two plain forms instead of a four-step wizard.
- **T23 remediation:** optional; skip unless the SME wants remediation in the report.
- **T25:** polling status page preferred over SSE; if so, T18 drops the SSE endpoint.
- **T10/T15:** three sample apps (A, B, D) are enough; app C is dropped.

Deferrals already applied below: Azure adapters move to T21 (written when first exercised), GitHub cloning is
optional (local path is enough for samples), DOCX parsing is optional (PDF and Markdown cover the samples),
and T17 is folded into T16.

---

## How to work

1. **One task per session.** Start a fresh session (`/clear`) for each task. The agent reads `CLAUDE.md`
   automatically; the prompt tells it which SPEC sections to read.
2. **Plan first on tasks marked `[plan]`.** Use plan mode, read the plan, correct it, then let it build.
3. **Verify, then commit.** Run the Done-when check yourself. If it passes: `git add -A && git commit -m "T07: ..."`.
   If the session goes off the rails, `git reset --hard` and re-run the task with a narrower prompt.
   Small commits are what make vibe coding safe.
4. **Never let the agent "fix" a failing test by weakening it.** If it tries, reject and ask for the root cause.
5. **Change the spec deliberately.** When you learn something, edit `docs/SPEC.md` yourself (or ask the agent to
   propose an edit), commit it, then continue. Code follows the spec, not the other way round.
6. **Build against FakeLLM until T21.** Everything up to the real agents runs without Azure, so a delay in
   Azure OpenAI access does not block you.
7. **Keep a log.** After each task, add one line to `docs/progress.md` (task, date, anything surprising).
   It becomes your readout material in week 6.

Prompt template used below (the agent sees CLAUDE.md automatically):

```
Task Txx: <title>. Read docs/SPEC.md §a, §b first.
<what to build>
Done when: <checks>. Add tests as described in CLAUDE.md, run `just lint` and `just test`, and summarise what changed.
```

---

## M0 — Setup (day 1)

### T00 — Machine and repo (you, no agent)
- Install: Docker Desktop (WSL2 backend), Git, Python 3.13, `uv`, Node 22 LTS, `pnpm`, `just`.
- `git init`, add a `.gitignore` for Python, Node, `.env`, `data/`.
- Create `.env.example` with: `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER=fake`, `AZURE_OPENAI_ENDPOINT`,
  `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`,
  `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, `RUN_TOKEN_BUDGET=400000`, `GITHUB_TOKEN`.
- Never commit `.env`. Never paste keys into an agent prompt.

### T01 — Monorepo scaffold `[plan]`
```
Task T01: scaffold the monorepo. Read docs/SPEC.md §1.
Create the folder layout from §1 with placeholder __init__.py files. Backend: uv project in backend/ with
FastAPI, uvicorn, pydantic-settings, SQLAlchemy[asyncio], asyncpg, alembic, pgvector, redis, arq, pytest,
pytest-asyncio, httpx, ruff, mypy. Frontend: Vite React TypeScript app in frontend/ with pnpm, Tailwind,
shadcn/ui initialised, TanStack Query, React Router, vitest. docker-compose.yml with pgvector/pgvector:pg16
(databases provenix and provenix_test), redis:7, api (uvicorn --reload, source mounted) and worker (arq)
built from backend/Dockerfile. The Dockerfile installs WeasyPrint's system libraries. A justfile with the
commands listed in CLAUDE.md (gen-client and eval can be stubs for now).
Done when: `just up` starts all four containers, `just lint` and `just test` run (with one trivial test each
side), and `pnpm dev` shows the Vite page.
```
**Done when:** containers healthy in Docker Desktop; both test suites green.

### T02 — API skeleton
```
Task T02: API skeleton. Read docs/SPEC.md §1, §4 (conventions and /health only).
app/main.py app factory, app/config.py settings from env, async DB session dependency, Redis client,
/api/v1/health checking DB and Redis, RFC 9457 problem-details exception handlers, structured JSON logging
with a request id, CORS for http://localhost:5173. Integration test for /health.
```
**Done when:** `curl localhost:8000/api/v1/health` returns `{"status":"ok","db":true,"redis":true}`; `/docs` loads.

---

## M1 — Data, content and onboarding (week 1)

### T03 — Domain models
```
Task T03: domain enums and models. Read docs/SPEC.md §2, §10.3.
Implement every enum and model in backend/app/domain/ exactly as specified. No I/O in this package.
Unit tests for validation edge cases (Locator needs path+lines for code, document_id+page for doc,
question_id for answer).
```

### T04 — Database tables and first migration `[plan]`
```
Task T04: SQLAlchemy models and Alembic migration. Read docs/SPEC.md §3.
Create all 11 tables in backend/app/db/models.py, enable the vector and pgcrypto extensions in the migration,
HNSW cosine index on chunk.embedding, the org_id default. `just migrate` must apply it cleanly to both
databases. Integration test: insert and read back one row per table.
```
**Done when:** `just migrate` works on a fresh `docker compose down -v && just up`.

### T05 — Ports and adapters
```
Task T05: ports and adapters. Read docs/SPEC.md §5.
Protocols in app/ports/. Adapters: FakeLLM (canned responses registered by prompt_id, records calls),
FakeEmbedder (deterministic hash vectors, dims 1536), LocalBlobStore, LocalGit. GitHubGit (shallow clone,
token from settings) is optional: add it only if you need to assess a real GitHub repo. The Azure adapters
are NOT written here; they arrive in T21 when first exercised. app/wiring.py picks adapters from
LLM_PROVIDER. The llm_call row writing and token budget (BudgetExceeded) live in a wrapper around any
LLMClient so they apply to Azure later. Unit tests for the fakes, LocalGit and the budget logic.
```

### T06 — Control pack `[plan]`
```
Task T06: EU AI Act control pack v0.1. Read docs/SPEC.md §6.
Write the 10 control YAML files in backend/control_packs/eu_ai_act/0.1/ following the PVX-HUM-01 example:
objective, applies_when, framework_refs, evidence (questions, documents, 2–4 code_signals with search_hints
each), assessment_guidance with Met / Partial / Not met / No evidence criteria, remediation_template.
Use your own words; do not quote ISO/IEC 42001. Add a Pydantic loader with validation, a CLI
`python -m app.control_packs validate`, GET /api/v1/controls, and tests (all files load; ids unique;
applicability matches the table in §6).
```
**Done when:** validator passes. **Then send the 10 YAMLs to your compliance SME for review.**

### T07 — Questionnaire
```
Task T07: questionnaire. Read docs/SPEC.md §7 and §4 (questionnaire endpoints).
Write backend/questionnaire/v1.json with all questions from §7 (clear wording, help text for legal terms such
as Annex III areas and the Art. 6(3) derogation). Endpoints: GET /questionnaire/schema, GET and PUT
/applications/{id}/questionnaire with partial upsert and a computed `complete` and `missing`.
Integration tests for partial save and completeness.
```

### T08 — Applications API
```
Task T08: applications API. Read docs/SPEC.md §3 (application), §4.
POST/GET /applications, GET /applications/{id} including snapshot, documents and latest assessment summary.
Integration tests. Then implement `just gen-client` (openapi-typescript from http://localhost:8000/openapi.json
into frontend/src/api/schema.d.ts) and a typed openapi-fetch client in frontend/src/api/client.ts.
```

### T09 — Frontend shell, applications list, onboarding steps 1–2 `[plan]`
```
Task T09: frontend shell. Read docs/SPEC.md §4, §7.
App layout with a left nav (Applications), React Router routes, TanStack Query provider. Applications list
page (name, tier badge, latest assessment status, created date). Onboarding wizard with steps
Details → Questionnaire → Repository → Documents; build Details and Questionnaire now. The questionnaire
renders entirely from GET /questionnaire/schema (all five question types) with react-hook-form + zod,
autosaves on blur via PUT, and shows section progress. Steps 3–4 are placeholders.
Use shadcn components. Vitest tests for the schema-driven form renderer.
```
**Done when:** you can create an app and fill the full questionnaire in the browser; refreshing keeps answers.

### T10 — Sample apps A and B `[plan]`
```
Task T10: build sample apps A and B. Read docs/SPEC.md §14.
samples/app-a-cv-screener and samples/app-b-support-bot: realistic small apps (1–5k lines), README, docs/
folder with 1–2 Markdown documents (a short model card or design note; leave out the things that are
planted gaps), and GAPS.md listing each planted gap with the file and lines that show it. The code must look
like a real team wrote it; do not add comments that point at compliance gaps. They do not need to run
against a real LLM; a stub client is fine.
Also write evals/golden/app-a.yaml and app-b.yaml in the §13 format as a DRAFT for the SME to correct.
```
**Done when:** you read GAPS.md and agree the gaps are real but not obvious. Send golden drafts to the SME.

---

## M2 — Ingestion (week 2)

### T11 — Repo ingestion job `[plan]`
```
Task T11: repo ingestion. Read docs/SPEC.md §3 (repo_snapshot, chunk), §4 (POST repo), §5.
POST /applications/{id}/repo creates a snapshot and enqueues an arq job that: checks out via GitHost into
./data/checkouts/<snapshot_id>; walks files (skip binaries, vendored and build folders, lockfiles, files over
300 KB, and GAPS.md); redacts secrets (regexes for keys, tokens, connection strings; replace with
[REDACTED]); chunks with tree-sitter by function/class for Python, TypeScript and JavaScript and by
60-line windows otherwise, keeping line_start/line_end/symbol; embeds in batches; stores chunks; sets
file_count, line_count, status READY or FAILED with error. Integration test using samples/app-a with FakeEmbedder.
```
**Done when:** connecting `samples/app-a-cv-screener` (provider local) reaches READY and `chunk` has rows with sensible line ranges.

### T12 — Search
```
Task T12: search service. Read docs/SPEC.md §9 (search_code, search_docs).
services/search.py: hybrid search over chunk for an application and source: pgvector cosine top-k combined
with Postgres full-text rank (add a generated tsvector column via migration), with optional keyword boost
terms. Returns the shapes in §9. Tests with FakeEmbedder showing keyword boost changes ranking.
```

### T13 — Document ingestion
```
Task T13: document ingestion. Read docs/SPEC.md §3 (document, chunk), §4 (POST documents).
Multipart upload of PDF and MD (DOCX optional, add only if a sample needs it); store in BlobStore; arq job
parses (PyMuPDF for PDF with page numbers, Markdown by heading, python-docx with headings if DOCX), chunks ~800 tokens with page/section anchors,
embeds, stores chunks, sets status. Tests with a small PDF and DOCX fixture.
```

### T14 — Onboarding steps 3–4
```
Task T14: onboarding repo and documents steps. Read docs/SPEC.md §4.
Repository step: provider select (local path or GitHub URL + ref), submit, poll snapshot status, show file
and line counts or the error. Documents step: drag-and-drop upload, list with status. A final "Ready to
assess" summary showing questionnaire completeness, snapshot status, document count, and the Start
assessment button (disabled with a reason until all are ready). Regenerate the client first.
```
**Done when:** full onboarding of app A works in the browser.

### T15 — Sample apps C and D
```
Task T15: build sample apps C and D, same rules as T10. Read docs/SPEC.md §14.
App D must have no planted gaps and should be a fair false-positive test (a minimal-risk internal tool with
ordinary engineering practices). Draft evals/golden/app-c.yaml and app-d.yaml.
```

---

## M3 — Classification (week 2)

### T16 — Rules classifier
```
Task T16: classifier. Read docs/SPEC.md §2 (Classification, RuleHit), §11.
Pure functions in services/classifier.py implementing every rule with a trace. GET
/applications/{id}/classification computes it live from saved answers. Table-driven unit tests: one case per
rule, plus the four sample apps' intended answers (put those answers in samples/<app>/questionnaire.json).
Add a tiny script `just seed-sample <app>` that creates the application, loads its questionnaire.json,
connects the repo and uploads its docs.
```
**Done when:** all four sample apps classify as §14 expects. **Ask the SME to review §11 rules and the test cases.**

### T17 — Classification in the UI (fold into T16 in the same session; keep the heading for numbering)
```
Task T17: show classification. On the onboarding summary and application page, show the tier badge,
roles, and the rule trace as a short list ("Annex III area: employment → high-risk", with the question it
came from). Show a needs-review banner when the Art. 6(3) derogation was claimed.
```

---

## M4 — The agent (week 3)

### T18 — Events and graph skeleton `[plan]`
```
Task T18: graph skeleton with events. Read docs/SPEC.md §8, §12, §4 (assessments endpoints).
POST /applications/{id}/assessments validates readiness (409 with problem details otherwise), creates an
assessment, enqueues an arq job that runs the LangGraph graph with the Postgres checkpointer
(thread id = assessment id). Implement intake, classify, scope and finalize for real; assess_control,
verify and remediate as stubs that write placeholder findings with status not_assessable. Every node emits
start/complete events to the Redis stream; GET /assessments/{id}/events streams them as SSE from the
beginning. Integration test running the whole graph with FakeLLM.
```
**Done when:** starting an assessment for app A produces 10 placeholder findings and `curl -N .../events` shows the node sequence.

### T19 — Agent tools
```
Task T19: agent tools. Read docs/SPEC.md §9, §2 (Locator).
Implement every tool in app/agents/tools/ scoped by (application_id, snapshot_id, assessment_id,
control_id). read_file reads from the snapshot checkout and rejects paths outside it. cite copies the
excerpt from the source, hashes it, inserts evidence_item, and returns an error message the model can act
on when the locator does not resolve. Tool outputs truncated to 8,000 chars. Unit and integration tests,
including path traversal attempts (../, absolute paths).
```

### T20 — Prompts, prompt loader, FakeLLM scripts
```
Task T20: prompts. Read docs/SPEC.md §10.
Prompt loader for prompts/<id>/v<N>.md with front matter and prompts/active.yaml. Write v1 of
gather_evidence, map_control, grounding_check, remediate and classify_rationale. gather_evidence gets the
control YAML (objective, code_signals, documents, questions, assessment_guidance) and must search before
concluding, cite only what it read, and stop when it has enough evidence or has run its searches.
map_control applies assessment_guidance strictly and uses no_evidence rather than guessing. All repo and
document text goes inside <untrusted_content>. Register FakeLLM scripts for each prompt so the graph runs
offline. Snapshot tests of rendered prompts.
```
**Review the prompts yourself.** They decide most of the POC's quality.

### T21 — Real assess_control node `[plan]`
```
Task T21: implement assess_control. Read docs/SPEC.md §8, §9, §10.
First write AzureOpenAILLM and AzureOpenAIEmbedder (openai SDK, structured outputs) behind the ports, wrapped
by the T05 llm_call/budget wrapper. Fan out with Send per control id. Each branch: gather via LLMClient.tool_loop (max 12 steps) with the tools,
then map via LLMClient.structured into MapResult, validating that evidence_ids belong to this control;
write the finding. Catch errors per branch → not_assessable with the error. Cap concurrency at 4.
Emit per-control events with evidence counts. Test with FakeLLM. Then, with LLM_PROVIDER=azure, run once on
app A and paste the findings summary and total cost into the task summary.
```
**Done when:** a real run on app A finishes and each finding cites code you can open and recognise.

### T22 — Verifier and grounding
```
Task T22: verify node. Read docs/SPEC.md §10.3 (verifier and needs_review).
Deterministic verification of every evidence item (re-read, re-hash, set verified, remove unverified ids
from findings, downgrade empty findings to no_evidence). Then one grounding_check call per finding that
grades each remaining evidence item. Compute needs_review and review_reasons. Unit tests for each rule,
including a tampered file whose hash no longer matches.
```

### T23 — Remediation node
```
Task T23: remediate node. Read docs/SPEC.md §8, §10.3 (RemediationResult).
For findings with status partial or not_met, call remediate with the control's remediation_template, the
finding rationale and its evidence; store in finding.remediation. code_pointers must be locators that
resolve (validate them like the verifier). Tests with FakeLLM.
```

### T24 — Tracing (optional)
```
Task T24: optional Langfuse tracing. Add a tracing hook in the LLM adapters that sends spans to Langfuse
when LANGFUSE_* settings are present, and does nothing otherwise. Do not add Langfuse to docker-compose;
document how to run it separately in docs/langfuse.md.
```
Skip this if the `llm_call` table gives you enough visibility.

---

## M5 — Review UI (week 4)

### T25 — Run timeline
```
Task T25: assessment run page. Read docs/SPEC.md §12.
useEventSource hook (reconnects, parses typed events). Run page: vertical timeline of nodes, a row per
control under assess_control with spinner/done/failed, elapsed time and evidence count, and a final status
card with findings, needs-review count and cost. Navigates to the findings workbench when finished.
```

### T26 — Findings workbench `[plan]`
```
Task T26: findings workbench. Read docs/SPEC.md §4 (findings, evidence), §6.
Left: control list grouped by status with filters (status, needs review) and colour-coded status pills.
Right: selected finding with control title and EU AI Act / ISO 42001 refs, status, confidence, rationale,
review reasons, and evidence cards. Clicking a code evidence card opens a drawer showing the file excerpt
with the cited lines highlighted (Shiki), path and line numbers; doc evidence shows document, page and the
excerpt; answer evidence shows the question and answer. Remediation section with steps, effort and owner.
```
**Done when:** every finding on app A can be traced to its source in two clicks.

### T27 — Review actions
```
Task T27: review. Read docs/SPEC.md §4 (POST /findings/{id}/review), §3 (review_decision).
API: confirm or override with required reason (min 10 chars) and reviewer name; sets final_status; moves the
assessment to REVIEWED when no finding still needs review. UI: Confirm and Override buttons on the finding
panel; override opens a dialog with the new status and reason; a "Needs review" queue filter with a count.
Tests for the state transitions.
```

---

## M6 — Report and evals (week 5)

### T28 — PDF report
```
Task T28: PDF report. Read docs/SPEC.md §4 (report endpoints), §3 (report).
Jinja2 template → WeasyPrint. Sections: cover (app, date, assessment id, pack version, models and prompt
versions used), classification with rule trace, summary table of controls by final status, one page per
finding (status, rationale, evidence excerpts with path:lines, review decision and reason, remediation),
and a methodology and limitations page stating that the report is decision support, not legal advice.
Store via BlobStore with sha256. Report page in the UI with preview and download.
```

### T29 — Eval harness `[plan]`
```
Task T29: eval harness. Read docs/SPEC.md §13.
backend/evals/run_eval.py: for each golden file, seed the sample app, run the assessment (with --runs N),
compare to labels, and compute every metric in §13. Write evals/results/<timestamp>.json and a Markdown
scorecard with per-app and overall tables plus a list of every disagreement (control, expected, got,
rationale). `just eval` wires it up. A --fake flag runs it with FakeLLM for CI.
```
**Done when:** `just eval --runs 1` produces a scorecard for all four apps.

### T30 — Tuning rounds (you, with the agent)
Run `just eval --runs 3`. For each disagreement, decide whether the cause is the **label**, the **control YAML**,
the **prompt**, or a **tool**. Fix the cause, never the symptom:
- Wrong label → the SME corrects the golden file.
- Vague guidance → edit the control's `assessment_guidance`.
- Prompt behaviour → add `v2.md`, switch `active.yaml`, re-run.
- Missing evidence → improve `search_hints`, chunking or tools.

Limit to **two rounds**. Record each round's scorecard in `docs/progress.md`.

---

## M7 — Demo and readout (week 6)

### T31 — Demo hardening
```
Task T31: demo readiness. Add `just demo-reset` (wipe DB, seed all four sample apps, run assessments).
Check empty, loading and error states on every page; make sure a failed node shows a readable message.
Write README.md with setup, commands and a 10-minute demo script.
```

### T32 — Readout pack (you)
- Final scorecard (3 runs per app) against the POC pass marks.
- SME timed comparison for H7 (manual assessment of one app vs. Provenix-assisted review).
- Cost and run time per assessment, variance across runs.
- What failed and why, from `docs/progress.md`.
- Go / Adjust / Stop recommendation and the v1.0 scope.

---

## Where vibe coding goes wrong on this project

| Watch for | Do this |
| --- | --- |
| The agent invents an evidence snippet or line range | Only the `cite` tool creates evidence. Reject any change that lets the model write excerpts. |
| Tests pass because everything is mocked | From T21 on, run one real assessment per task and read the findings yourself. |
| Prompts get edited in place | New version file, change `active.yaml`, re-run evals. |
| Scope creep ("let me add auth quickly") | Point the agent at the out-of-scope list in CLAUDE.md. |
| Large tasks drift | If a task runs past ~90 minutes, stop, commit what works, split the rest. |
| Sample apps leak the answers | No compliance-flavoured comments in sample code; GAPS.md is excluded from ingestion. |
| Cost surprises | Check `llm_call` totals after each real run; lower `RUN_TOKEN_BUDGET` if needed. |
| Windows path or line-ending bugs | Keep the backend in Docker; set `git config core.autocrlf input`. |
