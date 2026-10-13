# RCA-Sentinel

> **Autonomous, Knowledge-Graph-Driven Root Cause Analysis (RCA) & Remediation Platform for High-Precision Manufacturing**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.11+-4285F4.svg)](https://github.com/google/adk)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-FF6F00.svg)](https://github.com/jlowin/fastmcp)
[![Neo4j Aura](https://img.shields.io/badge/Neo4j-Aura%20Enterprise-008CC1.svg)](https://neo4j.com/cloud/aura/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL%2016-FDB515.svg)](https://www.timescale.com/)
[![Redis](https://img.shields.io/badge/Redis-7%20Streams-DC382D.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Overview

**RCA-Sentinel** is an enterprise manufacturing diagnostic platform that detects production line anomalies, traverses an ontology-backed knowledge graph to isolate compound root causes across physical equipment, material supply chains, and maintenance logs, forecasts downstream financial blast radius, and drafts gated containment and corrective actions.

### Core Capabilities
- **Hybrid Data Architecture**: High-frequency PLC sensor telemetry and streaming quality metrics in **TimescaleDB**; full plant topology, material traceability, PFMEA taxonomies, and maintenance history in **Neo4j Aura**.
- **Reactive Statistical Detection**: Streaming EWMA, CUSUM, and rolling Z-score detectors running against Redis Streams with consecutive signal suppression.
- **FastMCP Tooling**: Clean Model Context Protocol server exposing multi-hop graph traversals, commonality analysis, blast radius calculation, and action proposal endpoints to AI agents.
- **Sequential Agentic Pipeline (Google ADK)**: Five specialized LLM agents (Detect $\rightarrow$ Diagnose $\rightarrow$ Classify $\rightarrow$ Forecast $\rightarrow$ Remediate) executing structured 8D and PFMEA diagnostic workflows grounded on live graph data.
- **Human-in-the-Loop (HITL) Safety & Guardrails**: Strict policy engine with mandatory approval gating for all physical actuators (PLC interlocks, ERP quarantine, CMMS work orders), dry-run defaults, an emergency kill switch, and automated PII / hallucination scrubbing callbacks.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph DataPlane ["Telemetry & Event Ingestion"]
        PLC["PLC Sensors / Machine Streams"] --> TS["TimescaleDB (Hypertable)"]
        PLC --> RS["Redis Streams (rca:stream:telemetry)"]
        ERP["ERP & CMMS Records"] --> ING["Ingestion Pipeline (SHACL Validated)"]
        ING --> NEO["Neo4j Aura Knowledge Graph"]
    end

    subgraph DetectionPlane ["Anomaly Detection Engine"]
        RS --> DET["Stream Consumer (EWMA / CUSUM)"]
        DET --> INC["Incident Created (rca:cache:incident)"]
    end

    subgraph AgenticPipeline ["Google ADK Multi-Agent Pipeline"]
        INC --> AG1["1. DetectAgent (D2 Problem Description)"]
        AG1 --> AG2["2. DiagnoseAgent (D4 Root Cause Identification)"]
        AG2 --> AG3["3. ClassifyAgent (PFMEA Catalog & RPN)"]
        AG3 --> AG4["4. ForecastAgent (Blast Radius & Financial Risk)"]
        AG4 --> AG5["5. RemediateAgent (D3 Containment & D5 Actions)"]
    end

    subgraph MCPPlane ["FastMCP Server (:8001)"]
        AG1 & AG2 & AG3 & AG4 & AG5 <--> MCP["FastMCP Server (JSON-RPC)"]
        MCP <--> NEO
        MCP <--> TS
    end

    subgraph SafetyPlane ["Safety & HITL Policy Engine"]
        AG5 --> PROP["Action Proposal (PENDING)"]
        PROP --> APPR{"Human Engineer Approval Gate"}
        APPR -- "Approved" --> ACT["Actuators (DRY_RUN / Execution)"]
        APPR -- "Rejected" --> AUDIT["Immutable Audit Log"]
        ACT --> AUDIT
    end

    subgraph Presentation ["Operator & Engineering Console"]
        API["FastAPI REST & SSE / WS (:8000)"]
        UI["React 18 + Vite Console (:5173)"]
        NEO & TS & AUDIT --> API
        API --> UI
    end
```

---

## 3. The Golden Scenario (Evaluation Benchmark)

RCA-Sentinel includes a deterministic synthetic benchmark modeling a compound, multi-factor industrial failure:

```
[Spike Detected]
12% Scrap Rate Spike on Assembly Line 03 (station-03b)
       │
       ├──► Root Cause 1 (Material):
       │    Lot #40921 from Tier-3 vendor AlloyTech Global
       │    Silicon content: 1.82% (Specification Limit: ≤ 1.35%)
       │
       └──► Root Cause 2 (Maintenance):
            Maintenance Crew B skipped required dynamic spindle calibration
            Spindle offset: 0.035 mm (Tolerance: ±0.010 mm)
       │
       ▼
[Compound Effect]
High-silicon alloy + uncalibrated spindle runout = Excessive tool chatter & thermal warp
       │
       ├──► Failure Mode: FM-WAF-001 (Thermal Spindle Warp, Severity: 8, RPN: 280)
       ├──► Blast Radius: 420 downstream assemblies affected across 3 production runs
       ├──► Financial Exposure: ≥ $180,000 gross exposure ($126,000 scrap + $54,000 rework)
       └──► Proposed Remediation:
            1. Equipment Interlock: station-03b (PENDING APPROVAL)
            2. ERP Quarantine: Lot #40921 & sub-lots (PENDING APPROVAL)
            3. CMMS Work Order: Emergency recalibration by Crew A (PENDING APPROVAL)
```

ADK regression assertions in `backend/app/agents/evals/golden_scenario.py` verify that all 5 pipeline stages consistently pinpoint this exact compound cause with 100% citation grounding.

---

## 4. Multi-Agent Pipeline (Google ADK)

| Agent | 8D / PFMEA Stage | Responsibilities | MCP Tools Utilized |
| :--- | :--- | :--- | :--- |
| **DetectAgent** | **D2** (Problem Description) | Validates telemetry anomaly, characterizes scrap rate increase, verifies baseline conditions. | `get_machine_subgraph`, `get_active_incidents` |
| **DiagnoseAgent** | **D4** (Root Cause Analysis) | Traverses material genealogy (`SUPPLIED_BY`, `USED_IN`), checks technician maintenance logs and calibration records. | `trace_lot_provenance`, `get_maintenance_history`, `get_operator_logs`, `diagnose_root_cause` |
| **ClassifyAgent** | **PFMEA** Classification | Matches failure mechanism against standard catalog, assigns Severity (S), Occurrence (O), Detection (D), and computes RPN. | `get_failure_mode_catalog`, `get_ontology_summary` |
| **ForecastAgent** | Blast Radius & Risk | Determines downstream product batches affected by contaminated lot/station, calculates dollar exposure. | `calculate_blast_radius`, `forecast_financial_impact` |
| **RemediateAgent** | **D3** Containment & **D5** Action | Proposes urgent interlock, ERP supplier lot quarantine, and recalibration work order. Cannot execute directly. | `propose_equipment_interlock`, `propose_erp_quarantine`, `propose_cmms_work_order` |

### Agent Guardrails & Callbacks
- **Grounding Callback**: Inspects LLM output to ensure every claim cites valid entity identifiers (e.g., `lot-40921`, `station-03b`). Ungrounded claims trigger validation errors.
- **PII / Secret Scrubber**: Regex-based redaction of employee emails, phone numbers, and credentials before logging or serialization.
- **Session Telemetry**: Records duration, token metrics, and tool invocation counts per agent in the structured session state.

---

## 5. FastMCP Server Reference

The FastMCP server (`backend/app/mcp_server/server.py`) operates on port `8001` and registers:

### Graph & Traversal Tools
- `get_machine_subgraph(machine_id, depth)`: Fetches machine sensors, stations, and line hierarchy.
- `trace_lot_provenance(lot_id)`: Multi-hop upstream supplier and downstream usage trace.
- `get_maintenance_history(machine_id, days_back)`: Queries work orders, crews, and calibration records.
- `get_operator_logs(machine_id, hours_back)`: Retrieves operator shift notes and issue tags.

### Analytical & Impact Tools
- `diagnose_root_cause(incident_id, station_id)`: Performs commonality analysis across lots and maintenance shifts.
- `calculate_blast_radius(lot_id, station_id)`: Returns affected units, work centers, and downstream batches.
- `forecast_financial_impact(affected_units, scrap_cost, rework_cost)`: Computes bounded dollar exposure.

### Remediation Proposal Tools (Gated)
- `propose_equipment_interlock(machine_id, reason, justification)`: Creates a `PENDING` PLC interlock action.
- `propose_erp_quarantine(lot_id, reason, justification)`: Creates a `PENDING` ERP inventory hold action.
- `propose_cmms_work_order(machine_id, action_type, priority, justification)`: Creates a `PENDING` maintenance work order.

### MCP Resources
- `manufacturing://ontology`: OWL ontology schema, class taxonomy, and object property map.
- `manufacturing://incidents`: Active production incidents and severity metrics.
- `manufacturing://pfmea`: PFMEA failure mode catalog with baseline RPN ratings.

---

## 6. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| **Agentic AI** | Google ADK 2.11+, Gemini 2.5 Flash (`gemini-2.5-flash`), Jinja2 prompts |
| **Tool Interface** | FastMCP 2.0+ (Model Context Protocol, JSON-RPC) |
| **Knowledge Graph** | Neo4j Aura (Hosted), Cypher, `rdflib` + `pyshacl` (Ontology & SHACL) |
| **Time-Series Telemetry** | TimescaleDB (PostgreSQL 16 hypertable), `asyncpg` |
| **Streaming & Cache** | Redis 7 (Streams, Consumer Groups, TTL Caching) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| **DevOps & Quality** | Docker Compose, `uv`, `ruff`, `mypy` (strict), `pytest` |

---

## 7. Prerequisites

Before running RCA-Sentinel, ensure you have:
1. **Docker & Docker Compose** (v2.20+)
2. **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/)
3. **Node.js 20+** and `npm`
4. **Neo4j Aura Instance**: A free or enterprise Aura DB instance (`neo4j+s://...`).
5. **Google AI Studio API Key**: For Gemini model access (`GOOGLE_API_KEY`).

---

## 8. Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `dev` | Environment mode (`dev`, `demo`, `prod`) |
| `APP_NAME` | `rca-sentinel` | Application identifier |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins for web console |
| `SECRET_KEY` | - | Random application secret key |
| `NEO4J_URI` | `neo4j+s://...` | Neo4j Aura connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | - | Neo4j Aura database password |
| `NEO4J_DATABASE` | `neo4j` | Target Neo4j database |
| `TIMESCALE_HOST` | `timescaledb` | TimescaleDB host |
| `TIMESCALE_PORT` | `5432` | TimescaleDB port |
| `TIMESCALE_USER` | `rca` | PostgreSQL username |
| `TIMESCALE_PASSWORD` | `rca_password` | PostgreSQL password |
| `TIMESCALE_DB` | `rca_sentinel` | PostgreSQL database name |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `GOOGLE_API_KEY` | - | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | LLM model for ADK agents |
| `GEMINI_TEMPERATURE` | `0.1` | Agent sampling temperature |
| `AGENT_CONFIDENCE_THRESHOLD`| `0.7` | Minimum confidence score before human escalation |
| `MCP_SERVER_HOST` | `0.0.0.0` | FastMCP host interface |
| `MCP_SERVER_PORT` | `8001` | FastMCP port |
| `MCP_AUTH_TOKEN` | - | FastMCP bearer token |
| `API_HOST` | `0.0.0.0` | FastAPI host interface |
| `API_PORT` | `8000` | FastAPI port |
| `DRY_RUN` | `true` | When true, actuators simulate actions without physical I/O |
| `KILL_SWITCH_ENABLED` | `false` | Global emergency actuator kill switch |
| `ACTUATOR_RATE_LIMIT` | `5` | Maximum actuator actions permitted per minute |
| `SIMULATOR_SEED` | `42` | Random seed for deterministic synthetic generator |
| `GOLDEN_SCENARIO_DATE` | `2024-09-15` | Timestamp anchor for the golden scenario |
| `PROACTIVE_DETECTION_ENABLED`| `false` | Feature flag for Phase 2 graph ML drift detector |
| `JWT_SECRET_KEY` | - | Signing secret for authentication tokens |

---

## 9. Quick Start

### 1. Launch Services
Start all containers in detached mode:
```bash
make up
```
This builds and boots:
- `rca-timescaledb` on `:5432`
- `rca-redis` on `:6379`
- `rca-api` on `:8000`
- `rca-mcp-server` on `:8001`
- `rca-worker` (stream detection consumer)
- `rca-frontend` on `:5173`

### 2. Seed Ontology & Synthetic Data
Apply Neo4j uniqueness constraints, parse OWL ontology files, run SHACL validation, and ingest the baseline factory topology and golden scenario records:
```bash
make seed
```

### 3. Access Interfaces
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastMCP Server**: [http://localhost:8001](http://localhost:8001)
- **Frontend Console**: [http://localhost:5173](http://localhost:5173)

---

## 10. Development & Testing Commands

All standard operations are wrapped via `Makefile`:

```bash
# Infrastructure
make up          # Start all Docker services
make down        # Stop containers and remove volumes
make logs        # Tail Docker logs across all containers

# Data Management
make seed        # Bootstrap graph constraints, ontology & generate synthetic data
make replay      # Replay the golden scenario telemetry stream

# Backend Code Quality
make lint        # Run ruff linter and format check
make format      # Auto-format and fix lint errors
make typecheck   # Run mypy --strict on backend
make test        # Run pytest unit test suite
make test-cov    # Run pytest with code coverage report
make check       # Execute lint, typecheck, and test sequentially

# Frontend Code Quality
make fe-dev      # Run frontend in local Vite dev mode
make fe-build    # Compile frontend production bundle
make fe-test     # Run Vitest frontend test suite
make fe-lint     # Run ESLint on frontend

# Housekeeping
make clean       # Remove caches and shutdown containers
```

To run backend tests locally without Docker:
```bash
cd backend
uv run pytest tests/ -v
```

---

## 11. Safety & HITL Compliance Guarantees

In accordance with strict industrial automation standards:
1. **Zero Direct Execution**: Under no circumstances can an AI agent trigger an equipment interlock, adjust an ERP quarantine, or issue a CMMS work order directly.
2. **Gated Proposal State**: All remediation calls generate a `PENDING` action record with a cryptographic hash of the supporting evidence graph.
3. **Role-Enforced Approvals**: Executing or rejecting an action requires explicit human sign-off by a qualified Reliability or Quality Engineer.
4. **Dry-Run by Default**: Even after approval, all actuators run in `DRY_RUN=true` mode unless explicitly overridden in production configurations.
5. **Global Kill Switch**: Actuating `KILL_SWITCH_ENABLED=true` immediately halts all outgoing control signals regardless of approval status.
6. **Immutable Audit Trail**: Every approval, rejection, and simulated actuation is written to an append-only audit log with timestamp, operator ID, and decision justification.

---

## 12. Project Structure

```
rca-sentinel/
├── backend/
│   ├── app/
│   │   ├── agents/          # Google ADK agent definitions, Jinja2 prompts, callbacks & pipeline
│   │   │   ├── prompts/     # Jinja2 prompt templates (detect, diagnose, classify, forecast, remediate)
│   │   │   ├── evals/       # Golden scenario eval assertions
│   │   │   ├── callbacks.py # Grounding verification & PII scrubbing
│   │   │   └── pipeline.py  # SequentialAgent runner
│   │   ├── api/             # FastAPI routers (/health, /api/v1/ingestion, etc.)
│   │   ├── core/            # Configuration, logging, database clients, custom error hierarchy
│   │   ├── detection/       # Real-time detectors (EWMA, CUSUM, Z-score) & Redis stream worker
│   │   ├── domain/          # Pydantic domain models, schemas, enums
│   │   ├── graph/           # Neo4j async client, query repositories, schema bootstrap
│   │   ├── ingestion/       # Declarative schema mappers, entity resolver, SHACL validation
│   │   ├── mcp_server/      # FastMCP server with graph, impact, and action tools
│   │   ├── ontology/        # OWL ontology files (.ttl), custom rdflib loader, SHACL shapes
│   │   ├── remediation/     # Policy engine, approval workflow, safety kill switch, actuators
│   │   ├── simulator/       # Seeded deterministic synthetic data generator
│   │   ├── cli.py           # CLI entry points (seed, replay, bootstrap)
│   │   └── main.py          # FastAPI application lifespan & middleware configuration
│   ├── tests/
│   │   └── unit/            # Unit tests for all phases (93 passing tests)
│   ├── pyproject.toml       # Backend dependencies (uv) & tool configurations
│   └── Dockerfile           # Backend container image
├── frontend/                # React 18 + Vite + Tailwind operator console
├── docs/
│   ├── adr/                 # Architecture Decision Records
│   └── graph-model/         # Exported graph models and schema definitions
├── docker-compose.yml       # Production/local service orchestration
├── Makefile                 # Unified developer CLI targets
└── .env.example             # Template environment configuration
```

---

## 13. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
