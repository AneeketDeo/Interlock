# RCA-Sentinel Frontend

> **Autonomous, Knowledge-Graph-Driven Root Cause Analysis Console for Manufacturing**  
> Built with React 18, TypeScript Strict, Vite, Tailwind CSS, Zustand, TanStack Query, React Flow, and D3.

---

## 1. Aesthetic Vision & Design System

RCA-Sentinel departs from generic SaaS tropes to deliver an **industrial control-room console** designed for plant managers, reliability engineers, and quality investigators.

### Core Token System
- **Dual Themes**:
  - **Night Shift (Default)**: Deep ink-navy surfaces (`#0A121D`, `#0F1B2A`, `#16283A`), low eye-fatigue for 24/7 control rooms.
  - **Day Shift**: Architectural paper-white surfaces (`#EBEEF2`, `#FFFFFF`, `#F4F6F9`), high contrast for executive boardrooms and projector displays.
  - **Instant Switching**: Press `T` or toggle the theme icon in the top bar.
- **Strictly Semantic Color**:
  - **Healthy / Contained (Seafoam)**: `#3DD6A5` (Nominal operations, verified inventory, $128.4k saved)
  - **Caution (Amber)**: `#FFB000` (Telemetry vibration warnings, handover duration flags)
  - **Critical (Vermilion)**: `#FF5A3C` (Scrap spike 12.2%, out-of-spec lot 1.82% Si, feed-hold actuator)
  - **Agent Activity (Cobalt)**: `#4C8DFF` (Google ADK agent reasoning stream, knowledge-graph traversal)
- **Industrial Typography**:
  - Headings & KPI Numerals: **Barlow Semi Condensed** (bundled locally via `@fontsource/barlow-semi-condensed`).
  - Body & Provenance: **Public Sans** (bundled locally via `@fontsource/public-sans`).
  - Tabular Numerals (`font-variant-numeric: tabular-nums`) enabled on all metrics to prevent layout jitter during live telemetry ticks.
- **Budgeted Boldness**: Visual weight is concentrated in two high-impact anchors:
  1. The **Live Plant Floor Schematic** on the Command Center (animated conveyors, live station health halos, and diversion paths).
  2. The **Root Cause Reveal Graph** on the Incident Case Board (multi-hop graph traversal with culprit beacons and decoy dimming).

---

## 2. Visual Tour & Screenshots

### Command Center (Night Shift)
![Command Center Night Shift](../../docs/screenshots/command_center_night.png)
*Live production flow schematic across 4 lines, top KPI strip with operational context, financial exposure waterfall, and streaming AI agent log.*

### Command Center (Day Shift)
![Command Center Day Shift](../../docs/screenshots/command_center_day.png)
*High-legibility architectural paper theme with instant contrast compliance for executive presentations.*

### Incident Case Board & Multi-Hop Evidence Graph
![Incident Case Board](../../docs/screenshots/screen_incident.png)
*Automated 5-stage D2-D5 diagnostic tracker with interactive React Flow multi-hop evidence graph isolating Supplier Lot #40921 and Crew B skipped calibration.*

### Forward Impact & Blast Radius
![Impact and Blast Radius](../../docs/screenshots/screen_impact.png)
*Multi-tier Sankey dispersion tracing contaminated lot through WIP batches to Tesla and Boeing contracts ($184.8k unmitigated exposure vs. $128.4k avoided loss).*

### Human-in-the-Loop Approval Gate
![Approval Gate](../../docs/screenshots/screen_approvals.png)
*Mandatory engineering signoff gate with SLA countdown, risk levels, and reversible actuator controls.*

### Supply Chain Lineage & Metallurgy
![Supply Chain Lineage](../../docs/screenshots/screen_supply_chain.png)
*Genealogy of raw alloy lots, spectrometry certificates showing 1.82% Silicon, and 100% staged verified buffer stock.*

### Shift & Maintenance Intelligence
![Shift & Maintenance Intelligence](../../docs/screenshots/screen_maintenance.png)
*Weekly calibration compliance matrix highlighting skipped tramming on Station 03B, and crew handover duration correlation.*

### Auto-Populated 8D Report
![8D Report](../../docs/screenshots/screen_report.png)
*Standard automotive/aerospace 8D problem-solving report ready for PDF export and executive review.*

### Data & Trust Architecture
![Data Trust](../../docs/screenshots/screen_trust.png)
*Real-time ingestion health, SHACL ontology validation status, and append-only cryptographic audit trail.*

---

## 3. 3-Minute Hackathon Demo Script

Follow this scripted walkthrough to present RCA-Sentinel to technical and business judges:

| Elapsed Time | Screen / Action | Hotkey / Click | Narrative & Talking Points |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:35** | **Command Center** | `G` (Reset to Stage 0) $\rightarrow$ `Space` (Play) | *"We are at Austin Advanced Manufacturing Plant 01. Four production lines are running nominally. Watch Line 03: a 12.2% scrap spike suddenly trips statistical CUSUM alarms on Machine Station-03B. Cost of poor quality surges. Every metric on screen answers 'so what?' for operations."* |
| **0:35 - 1:25** | **Incident Case Board** | Click banner `Open Case Board` or press `2` | *"The Google ADK multi-agent pipeline immediately kicks off. In under 2 seconds, the DiagnoseAgent executes ISO GQL multi-hop traversals over Google Cloud Spanner Graph across physical machines, ERP batches, and CMMS logs. Look at the Root Cause Reveal: it isolates a compound failure—AlloyTech Lot #40921 had 1.82% silicon (+34% over spec), which combined with a skipped spindle tramming calibration by Maintenance Crew B during a rushed 4-minute shift handover. Notice how alternative hypotheses like tool wear are automatically dimmed and ruled out."* |
| **1:25 - 2:05** | **Blast Radius & Impact** | Press `3` (Blast Radius) | *"What is the business exposure? Our ForecastAgent traces downstream: 420 assemblies are contaminated across 3 batches affecting Tesla Powertrain and Boeing Tier-1 purchase orders. Gross unmitigated risk is $184,800. But if we contain right now, avoided loss is $128,400."* |
| **2:05 - 2:40** | **Approval Gate (HITL)** | Press `4` (Approvals) | *"AI agents cannot trip physical actuators autonomously. The RemediateAgent drafts 3 gated actions: 1) Emergency PLC interlock on Station-03b, 2) ERP quarantine of Lot #40921 with auto-reroute to verified backup Lot #40889, 3) Dispatch emergency CMMS work order. As Chief Reliability Engineer, I review the before/after and sign approval. Notice the permanent DRY_RUN safety banner."* |
| **2:40 - 3:00** | **Resolution & Verification** | Press `1` (Return to Command Center) | *"Watch the Plant Floor schematic update live: Station-03B enters physical feed hold, the conveyor visibly diverts to clean Lot #40889, scrap rates collapse back to 0.8%, and $128,400 in plant loss is permanently avoided. A formal 8D report is auto-generated and ready for audit."* |

---

## 4. Execution & Data Modes

### Offline Mock Mode (`VITE_DATA_MODE=mock`)
Runs completely offline with zero backend or database requirements:
- Deterministic mock scenario engine (`src/mock/scenario.ts`) emitting factory ticks, 5 agent reasoning streams, and multi-hop graph nodes.
- Pre-loaded with 4 lines, 20 machines, 3 supplier tiers, and 30-day calibration logs.
- Fully interactive scenario stepping via keyboard controls (`Space`, `->`, `<-`, `G`).

```bash
# Start local development in mock mode
npm run dev
```

### Live Mode (`VITE_DATA_MODE=live`)
Connects to the FastAPI backend (`:8000`) and FastMCP server (`:8001`) via TanStack Query and Server-Sent Events (SSE):
```bash
# In .env or shell:
VITE_DATA_MODE=live
VITE_API_BASE_URL=https://rca-sentinel-864573324943.asia-south1.run.app
npm run dev
```

---

## 5. Keyboard Navigation & Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`T`** | Toggle between Night Shift (control room) and Day Shift (executive review) |
| **`P`** | Open / Close 3-Minute Presenter Walkthrough Guide |
| **`Space`** | Play / Pause automated scenario playback |
| **`->`** | Step forward to next RCA scenario stage |
| **`<-`** | Step backward to previous RCA scenario stage |
| **`G`** | Reset to Baseline nominal state and run Golden Scenario |
| **`Cmd / Ctrl + K`** | Open Command Palette (jump to any line, station, or action) |
| **`?`** | Open Keyboard Shortcut Cheatsheet |

---

## 6. Build & Test Verification

```bash
# Run unit tests (formatters, state machine, scenario engine)
npm run test

# Typecheck and bundle production distribution
npm run build
```

Both build and unit tests pass with zero TypeScript errors and local font assets bundled.
