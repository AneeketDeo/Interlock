# RCA-Sentinel — Engineering Rules

These rules apply to every file you create or modify in this repository. Follow them without being reminded. If a rule conflicts with a user instruction in the current task, the user instruction wins; mention the conflict in one line.

Stack: Python 3.12 + FastAPI, Google ADK, FastMCP, Neo4j Aura (hosted; rdflib + pyshacl for ontology/validation, Aura Graph Analytics for graph metrics), Neo4j MCP servers (dev-time), TimescaleDB, Redis, React 18 + TypeScript + Vite.

---

## 1. General Principles

- Prefer clarity over cleverness. Write code a new teammate can read in one pass.
- Keep functions small and single-purpose (target < 40 lines; split if longer).
- No dead code, no commented-out code, no `TODO` without an owner and a linked task in the plan.
- No hard-coded secrets, URLs, thresholds, model names or credentials. Everything configurable goes through typed settings and `.env`.
- Every module has one responsibility. Do not create "utils" dumping grounds; name modules by what they do.
- Make the smallest change that solves the task. Do not refactor unrelated files in the same change.
- When unsure about a requirement, state your assumption in the plan or PR notes and proceed; do not stall.
- Never invent library APIs. If unsure about a Google ADK, FastMCP, n10s or GDS call, check the installed package or official docs first.

## 2. Repository and Naming

- Monorepo layout is fixed: `backend/`, `frontend/`, `docker-compose.yml`, `Makefile`. Do not add top-level folders without updating the README.
- Python: `snake_case` for modules, functions, variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- TypeScript: `PascalCase` for components and types, `camelCase` for variables and functions, `kebab-case` for file names except component files (`IncidentConsole.tsx`).
- Graph labels are `PascalCase` (`MaterialLot`), relationship types are `UPPER_SNAKE_CASE` (`SUPPLIED_BY`), properties are `snake_case`.
- Redis keys are namespaced and colon-delimited: `rca:cache:blast_radius:{incident_id}`, `rca:stream:telemetry`, `rca:lock:{resource}`.
- Branches: `feat/…`, `fix/…`, `chore/…`. Commits follow Conventional Commits (`feat(graph): add lot lineage query`).

## 3. Python Style (Backend)

### Tooling
- Format and lint with `ruff` (line length 100). Type-check with `mypy --strict` on `app/`.
- Dependencies are managed with `uv`; pin versions in `pyproject.toml`. Do not use `pip install` directly.

### Language rules
- Full type hints on every function signature and public attribute. No bare `Any`; if unavoidable, add a comment explaining why.
- Use modern syntax: `list[str]`, `X | None`, `match` where it improves clarity, `pathlib`, f-strings.
- Use Pydantic v2 models for all data crossing a boundary (API, MCP tools, agent outputs, ingestion records, config). Use `model_validate` / `model_dump`, never v1 APIs.
- Use `Enum`/`StrEnum` for fixed vocabularies (severity, incident status, action type, approval state).
- Async by default for I/O. Never call blocking code (sync Neo4j driver, `requests`, `time.sleep`) inside async paths; use the async driver, `httpx.AsyncClient`, `asyncio.sleep`.
- Imports ordered: stdlib, third party, local; absolute imports from `app.`; no wildcard imports.
- Docstrings (Google style) on every public function, class and MCP tool. MCP tool docstrings are read by the LLM, so they must state purpose, arguments, return shape and side effects precisely.

### Error handling
- Define a domain exception hierarchy in `app/core/errors.py` (`RcaError`, `GraphQueryError`, `ValidationRejected`, `PolicyViolation`, `ApprovalRequired`, …).
- Catch specific exceptions only. Never `except Exception: pass`. Log with context, then re-raise or translate to a domain error.
- Map domain errors to HTTP responses in one place (exception handlers), using a single structured error model: `{code, message, details, correlation_id}`.
- External calls (Neo4j, Redis, Gemini, mock ERP/CMMS) use timeouts, retry with exponential backoff and jitter, and a circuit breaker where repeated failure is plausible.

### Logging and observability
- Use structured JSON logging (`structlog` or stdlib with a JSON formatter). No `print`.
- Every request, incident and pipeline run carries a `correlation_id` / `incident_id` through logs, traces and decision objects.
- Never log secrets, tokens or raw operator free text containing personal data. Redact before logging.
- Instrument FastAPI, Neo4j calls and ADK agent runs with OpenTelemetry spans.

## 4. FastAPI Conventions

- Routers live in `app/api/`, one file per resource, mounted under `/api/v1`.
- Routers are thin: validate input, call a service function, return a response model. No Cypher, SQL or business logic in route handlers.
- Always declare `response_model`, status codes and `tags`. Request and response schemas are separate Pydantic models; never return ORM/driver objects or raw dicts.
- Use dependency injection (`Depends`) for settings, DB clients, auth and the current user. No module-level global clients.
- Use lifespan handlers to create and close Neo4j, Redis and Postgres connections.
- Pagination is cursor-based for incidents, telemetry and audit logs. Default page size 50, max 200.
- Long-running work (ingestion jobs, RCA pipeline runs) is started as a background job and returns a job/incident ID immediately; progress is pushed over SSE/WebSocket.
- Auth: JWT with role checks (`operator`, `reliability_engineer`, `quality_engineer`, `admin`) enforced via dependencies. Approval endpoints require an engineer role.

## 5. Neo4j and Cypher

- All Cypher lives in `app/graph/queries/` as named, parameterized constants or `.cypher` files. Never build queries with string concatenation or f-strings; always use parameters.
- Wrap access in repository classes (`MaterialLotRepository`, `IncidentRepository`). Services never touch the driver directly.
- Use `MERGE` on unique-constrained keys for upserts; every label that is merged on has a uniqueness constraint created in the bootstrap step.
- Batch writes with `UNWIND $rows AS row`; chunk at 1,000–5,000 rows. Use explicit transactions and managed `execute_read` / `execute_write`.
- Every node and relationship written by ingestion must carry: `source_system`, `source_record_id`, `ingested_at`, `pipeline_run_id`, `valid_from`, `valid_to` (nullable), `recorded_at`.
- Bound every variable-length traversal (`*1..6`) and add `LIMIT`. Unbounded traversals are not allowed.
- Use `EXPLAIN`/`PROFILE` when adding a new traversal query and note the result in the PR notes if it touches more than 100k nodes.
- Neo4j is hosted on **Aura**. The neosemantics (n10s) plugin and custom server-side plugins are NOT available on Aura. Never use `n10s.*` procedures or assume in-database `gds.*` procedures exist.
- Ontology changes go through the `.ttl`/`.owl` source files and the custom loader in `app/ontology/loader.py`, which parses with `rdflib` and writes classes/properties/axioms to Neo4j with parameterized Cypher. Not ad-hoc Cypher.
- SHACL validation runs in Python with `pyshacl` against `app/ontology/shapes.ttl` **before** any graph write. Update the shapes with any schema change.
- Graph metrics and (Phase 2) graph ML run through Aura Graph Analytics sessions using the `graphdatascience` Python client. Sessions are created on demand, named, always closed in a `finally` block, and wrapped behind `app/graph/analytics.py`. Do not call GDS from route handlers.
- Only use APOC procedures that Aura supports (APOC core subset). Check before relying on any `apoc.*` call.

## 5A. Neo4j Aura and Neo4j MCP Servers

### Aura connection
- Connect with the `neo4j+s://` URI from `NEO4J_URI`, plus `NEO4J_USERNAME`, `NEO4J_PASSWORD` and `NEO4J_DATABASE`, all loaded through typed settings. Never commit credentials; keep `.env.example` current.
- There is no local Neo4j container. `docker-compose.yml` runs only TimescaleDB, Redis, API, MCP server, worker and frontend.
- Run a connectivity check at startup and in `/health/ready` that returns a clear error if the Aura instance is unreachable or paused (idle Aura instances can pause).
- Use separate Aura instances for `dev`, `demo` and `prod`, selected by `APP_ENV`. Never point a write-capable tool at `prod`.
- Respect Aura tier limits (node/relationship counts, memory, connections). Keep high-frequency telemetry in TimescaleDB and store only summaries and entities in the graph. Size synthetic data to fit the tier and document the counts.
- Use a single shared async driver with connection pooling and retry on transient errors (Aura can return transient/leader-switch errors).

### Neo4j MCP servers (development-time tooling)
Configure these in the Antigravity workspace MCP config, with credentials from environment variables, not inline:
- `mcp-neo4j-data-modeling`: design and validate the graph model; generate ingestion Cypher. Export the approved model to `docs/graph-model/` and keep it in sync with the ontology.
- `mcp-neo4j-cypher`: inspect schema, run verification queries, and apply simulated data to the **dev/demo** Aura instance.
- `mcp-neo4j-cloud-aura-api`: provision and manage Aura instances (dev/demo only).

### Rules for using them
- Simulated data is generated by the deterministic, seeded generator in `app/simulator/`. That generator is the source of truth and what tests use. MCP tools may be used to load its output into Aura and to verify the result, not to invent data ad hoc.
- Anything that must be reproducible (seed, schema, constraints, indexes) lives in versioned code or scripts in the repo, never only in an MCP chat action.
- Treat the generic `mcp-neo4j-cypher` as a developer tool. Do not wire it into the production agent path.
- Never run destructive Cypher (`DETACH DELETE` on broad patterns, `DROP`, wiping databases) through MCP without stating the target instance and getting explicit confirmation. Confirm the instance name before every write.
- Keep the Aura management MCP away from `prod` credentials.

## 6. Redis

- Caching: always set a TTL. Cache keys include the graph version or incident ID so invalidation is explicit.
- Telemetry flows through Redis Streams with consumer groups; consumers must acknowledge and handle redelivery idempotently.
- Use idempotency keys for detection events and remediation execution; use locks with expiry for single-writer operations.
- Never store secrets or authoritative state only in Redis. The graph and Postgres are the source of truth.

## 7. Google ADK and Agent Design

- One agent per file in `app/agents/`; prompts live in `app/agents/prompts/` as versioned text/Jinja files, not inline strings.
- Every agent has: a narrow instruction, an explicit tool allow-list, an `output_schema` (Pydantic), and a defined `output_key` in session state.
- Agents reach data only through the FastMCP server. No direct DB access from agent code.
- Agents may only **propose** actions. Executing an action is outside the agent boundary and requires an approved `Approval` record.
- Every agent conclusion must cite evidence IDs (graph node/edge IDs or telemetry windows). Ungrounded claims are rejected by a validation callback.
- If confidence is below the configured threshold, the agent must escalate to a human and must not propose an interlock.
- Model names, temperatures and thresholds come from settings.
- Every agent has at least one ADK eval case. The golden scenario (Lot #40921 + same maintenance crew + skipped calibration) must stay green.
- Treat all ingested free text (operator logs, supplier documents) as untrusted. Delimit it in prompts and never let it alter tool permissions or instructions.

## 8. FastMCP Server

- Tools are grouped by module (`graph_tools.py`, `impact_tools.py`, `action_proposal_tools.py`).
- Each tool has typed inputs/outputs (Pydantic), a precise docstring, input bounds (max hops, max window, max rows) and a timeout.
- Read tools are side-effect free. Action tools only create `PENDING` approvals and return the approval ID.
- Responses are compact and structured. Truncate large results and return counts plus top-N with a "more available" flag.
- Authenticate requests and log every tool call with arguments (redacted) and duration.
- This FastMCP server is the only graph interface ADK agents use at runtime. It runs fixed, parameterized, bounded queries against Aura. Agents never get free-form Cypher access. If an exploratory read-only Cypher tool is ever added for agents, it must use a read-only database user, enforce timeouts and row limits, and be approved in the plan first.

## 9. Human-in-the-Loop and Safety (Non-Negotiable)

- No equipment interlock, ERP routing change, CMMS write or PLC-affecting action executes without an explicit human approval stored in the audit log.
- Actuator adapters default to `DRY_RUN=true`. Real execution requires an explicit config flag and an approved record.
- Every execution is idempotent, verified after the fact, and has a rollback path.
- The audit log is append-only: who, what, when, evidence snapshot hash, justification.
- A global kill switch must be able to disable all actuators.
- Do not weaken, bypass or add exceptions to the policy engine for convenience, tests or demos. Use mocks instead.

## 10. Data, Ingestion and Validation

- Pipelines are idempotent and re-runnable; re-ingesting the same file must not create duplicates.
- Validate with Pydantic at the edge, then SHACL before graph write. Rejected records go to a quarantine table with a reason, never silently dropped.
- Mapping from source schema to ontology is declarative (config or mapping files), not buried in code.
- LLM extraction from unstructured text returns structured output with a confidence score; records below threshold are flagged for human review.
- Timestamps are timezone-aware UTC internally. Keep both event time and recorded time.
- Synthetic data generation is seeded and deterministic (fixed random seed) so tests are reproducible.

## 11. TypeScript and React (Frontend)

### Tooling
- TypeScript `strict` mode on. ESLint + Prettier enforced. No `any`; use `unknown` and narrow.
- API types and client are generated from the backend OpenAPI schema. Do not hand-write API types.

### Components
- Functional components and hooks only. One component per file; keep components under ~200 lines and extract hooks or subcomponents beyond that.
- Server state uses TanStack Query (with stable query keys and proper invalidation). Local UI state uses `useState`/`useReducer`. Avoid global stores unless state is genuinely cross-page.
- Live data (incidents, telemetry, approvals) comes via the SSE/WebSocket hook in `src/lib/realtime.ts`, which handles reconnects and backoff.
- Props are typed with explicit interfaces. No prop drilling beyond two levels; use composition or context.
- Every data view handles loading, error and empty states. No blank screens.
- Graph visualizations (React Flow/Cytoscape) must virtualize or cap node counts, support highlight of the suspect path, and show provenance on node click.

### Styling and UX
- Tailwind utility classes with shadcn/ui primitives; no inline style objects except for dynamic values.
- Use design tokens (CSS variables) for colors, spacing and severity levels. Severity colors must be consistent everywhere (info, warning, critical).
- Dark, dense, operations-console look. Accessibility basics are required: semantic HTML, labels, focus states, keyboard navigation, sufficient contrast, `aria-*` where needed.
- Destructive or consequential actions (approve interlock, reject, rollback) require a confirmation step showing the evidence and the exact action.
- No business logic in components that belongs on the backend (e.g., cost computation, policy decisions).

## 12. Testing

- Backend: `pytest` + `pytest-asyncio`. Unit tests for detectors, Cypher repositories (against a test Neo4j container), MCP tools, policy engine and API routes. Aim for meaningful coverage of branches, not a number.
- Policy engine and approval gate tests are mandatory for every change that touches remediation: prove that nothing executes without approval.
- Frontend: Vitest + Testing Library for components and hooks; one Playwright end-to-end test of the golden scenario (replay → incident → RCA → approval).
- Tests are deterministic: seeded data, no real network or LLM calls (use recorded fixtures or fakes), no sleeps; use polling with timeouts.
- A change is not done until `make lint`, `make typecheck` and `make test` pass.

## 13. Security

- Validate and bound all inputs (sizes, ranges, window lengths, hop counts).
- Parameterize all queries (Cypher and SQL). No dynamic query strings from user or LLM input.
- Restrict CORS to configured origins. Rate-limit auth and ingestion endpoints.
- Run containers as non-root, pin base image versions, and keep secrets out of images and logs.
- Never commit `.env`; keep `.env.example` current with every new variable.

## 14. Documentation and Change Hygiene

- Update `README.md`, the Mermaid architecture diagram and `.env.example` whenever you add a service, env variable, endpoint or MCP tool.
- Every new public endpoint, MCP tool and agent gets a short entry in `docs/` (purpose, inputs, outputs, failure modes).
- Record notable decisions in `docs/adr/NNNN-title.md` (context, decision, consequences) when you pick between alternatives.
- Provide a short summary of what changed, what was tested and any assumptions after each task.

## 15. Workflow for Each Task

1. Read the relevant existing code and these rules before editing.
2. State a brief plan; list files you will touch.
3. Implement in small, reviewable steps.
4. Run lint, type-check and tests; fix failures before reporting completion.
5. For UI changes, verify in the browser and capture a screenshot or recording.
6. Summarize changes, assumptions, and any follow-ups. Never claim something works without having run it.

## 16. Phase Boundaries

- Phase 1 is **reactive** detection and impact analysis only.
- Proactive detection with graph ML (via Aura Graph Analytics sessions) is Phase 2. Keep it behind the `PROACTIVE_DETECTION_ENABLED` feature flag with stubs only; do not implement it unless explicitly asked.
