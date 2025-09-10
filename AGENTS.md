# GPT Pilot — AGENTS Handbook---

## Repository Reality Check

**Primary language:** Python (core orchestrator + agents)  
**Frontend templates:** Vite + React
**Key entrypoints:** 
- `main.py` (bootstrap)  
- `core/cli/main.py` (CLI orchestrator)  
- `core/web/server.py` (HTTP API for project mgmt)

**Core subsystems:**  
- **Agents:** `core/agents/*` (25 modules)  
- **Prompts:** `core/prompts/<agent>/*.prompt` (≈79 prompt files, one folder per agent)  
- **State & Memory:** `core/state/state_manager.py`, `core/memory/shared_memory.py`, `core/memory/context_engine.py`  
- **Persistence:** SQLAlchemy + Alembic migrations under `core/db/*`  
- **UI adapters:** `core/ui/console.py`, `core/ui/ipc_client.py`, `core/ui/virtual.py`

**Project scaffolds (selected by Architect):**  
`core/templates/tree/` → `vite_react/`, `fastapi_sqlite/`, `flask_sqlite/`, `typer_cli/`

---

## Mission & Boundaries

- **Mission:** Take a raw product idea and deliver a *working* codebase with docs, tests, and repeatable builds.  
- **Boundaries:**
  - No secrets committed; use `.env.example` patterns.
  - Prefer minimal, well-explained diffs; remove dead artifacts.
  - Produce *complete* code—no placeholders blocking execution.

---

## Agent Catalog

Each item lists the **module path** and the role it actually plays in this codebase.

- **Orchestrator** — `core/agents/orchestrator.py`  
  Coordinates the full run: schedules agents, aggregates results, pushes messages via `core.messaging`, and updates `StateManager`.
- **SpecWriter** — `core/agents/spec_writer.py`  
  Converts the user brief into an evolving **Specification**; can iterate based on feedback and prior responses.
- **TechLead** — `core/agents/tech_lead.py`  
  Generates **Epics** and **Tasks** (see `APIEndpoint`, `Epic`, `Task` models in this file). Methods like `create_initial_project_epic()`
  and `update_epics_and_tasks()` keep the plan current.
- **Architect** — `core/agents/architect.py`  
  Chooses a project template and base dependencies (`AppType`, `SystemDependency`, `PackageDependency`), and can `prepare_example_project`.
- **Developer** — `core/agents/developer.py`  
  Breaks work into **steps** (see `StepType`, `CommandOptions`), writes/edits files, runs commands/tests, and returns `AgentResponse`.
- **Frontend** — `core/agents/frontend.py`  
  Owns UI-related tasks; integrates with the Vite React template under `core/templates/tree/vite_react`.
- **Executor** — `core/agents/executor.py`  
  Runs shell commands via a `ProcessManager`, logs to DB (`exec_log`), and feeds results back to the pipeline.
- **Git** — `core/agents/git.py`  
  Initializes repos, decides if/when to commit, and ensures clean history during automation.
- **Importer** — `core/agents/importer.py`  
  Ingests existing code into the workspace & DB models (`File`, `FileContent`), enabling refactors & context.
- **ProblemSolver** — `core/agents/problem_solver.py`  
  Focused remediation/patch agent for tricky issues.
- **BugHunter** — `core/agents/bug_hunter.py`  
  Iteratively analyzes logs, requests more data, and derives reproducible steps for bugs.
- **ExternalDocs** — `core/agents/external_docs.py`  
  Fetches and condenses external documentation into actionable **snippets** for a topic.
- **WebSearch** — `core/agents/web_search.py`  
  Performs topical web queries and distills results for downstream agents.
- **HumanInput** — `core/agents/human_input.py`  
  Requests and ingests user clarifications or approvals when needed.
- **ErrorHandler** — `core/agents/error_handler.py`  
  Centralized recovery patterns when agents fail.
- **LegacyHandler** — `core/agents/legacy_handler.py`  
  Maintains back-compat for older task formats.
- **CodeMonkey** — `core/agents/code_monkey.py`  
  Utility implementer for simpler edits or bulk file changes.
- **Convo / Response** — `core/agents/convo.py`, `core/agents/response.py`  
  Conversation state, `ResponseType`, and helpers like `AgentResponse.done()` / `.error()`

> **Prompts:** Each agent’s behavior is governed by prompts residing in `core/prompts/<agent>/*.prompt` (e.g., `core/prompts/bug-hunter/*`,
> `core/prompts/code-monkey/*`, `core/prompts/architect/*`). These are **real** in the repo and should be updated alongside code.

---

## State, Memory & Persistence

- **State Manager:** `core/state/state_manager.py` owns transitions and holds the current *Project → Branch → State* hierarchy.
- **Relational DB:** SQLAlchemy models live under `core/db/models/*` (e.g., `project.py`, `file.py`, `file_content.py`, `project_state.py`, `llm_request.py`).
  Alembic migrations are in `core/db/migrations/*`.
- **Shared Memory & Context:** `core/memory/shared_memory.py` and `core/memory/context_engine.py` implement semantic retrieval
  to surface the most relevant items to each agent step.

---

## UI / Control Planes

- **Console UI:** `core/ui/console.py` (headless interactive flow).
- **IPC Client:** `core/ui/ipc_client.py` defines message types and events for external UIs to drive the run (e.g., a desktop shell).
- **Virtual UI:** `core/ui/virtual.py` for non-interactive or scripted sessions.
- **HTTP API (optional):** `core/web/server.py` exposes endpoints to create/open projects and control runs.

> There is **no VS Code extension** in this repository; instead, projects can scaffold a **Vite React** client (`core/templates/tree/vite_react/*`).

---

## Orchestration Flow (as coded)

1. **Intake → Spec**  
   `SpecWriter` drafts/iterates the specification from user input (`core/agents/spec_writer.py`).
2. **Plan → Epics & Tasks**  
   `TechLead` produces an initial epic and tasks (`create_initial_project_epic`) and keeps them fresh (`update_epics_and_tasks`).
3. **Architecture & Scaffold**  
   `Architect` selects template(s) and dependencies; can `prepare_example_project` to bootstrap code.
4. **Implementation**  
   `Developer` executes steps (write/edit files, run commands, run tests). `Executor` performs shell actions, stores logs.
5. **Docs & Frontend**  
   `Frontend` and `ExternalDocs` refine UI and developer docs; `WebSearch` augments knowledge.
6. **Version Control**  
   `Git` guards repo hygiene; commits atomic changes.
7. **Debugging**  
   `BugHunter` reduces failures into reproducible cases; `ProblemSolver` applies focused fixes.
8. **Human-in-the-Loop (when needed)**  
   `HumanInput` pauses for confirmations/choices, routed via `console`/`ipc`/`virtual` UIs.
9. **State & Memory Updates**  
   `StateManager` persists transitions; `SharedMemory/ContextEngine` update retrieval context.

---

## How to Run (from this repo)

```bash
# 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) DB migrations
python -c "from core.db.setup import run_migrations; run_migrations()"

# 3) Start the orchestrator (interactive / CLI)
python -m core.cli.main      # or: python main.py

# 4) Optional HTTP API (if using the web control plane)
python -m core.web.server
```

> If you plan to scaffold a Vite React app, the generated project will contain its own `client/` directory with `package.json`,
> `vite.config`, and `src/*.tsx`. That is **template output**, not the orchestrator itself.

---

## Agent Review Checklist (tailored to repo)

- [ ] **Spec & Plan:** `SpecWriter` + `TechLead` outputs exist under project state and are consistent.  
- [ ] **Files & Diffs:** `Developer` changes are complete; no blocking TODOs/placeholders.  
- [ ] **Commands & Logs:** `Executor` logs stored (`exec_log`), errors actionable.  
- [ ] **Memory:** Relevant items appear via `ContextEngine`; retrieval limits tuned.  
- [ ] **Git:** Repo initialized and commits are atomic & signed off if required.  
- [ ] **Docs:** Update prompts under `core/prompts/<agent>` when agent behavior changes.  
- [ ] **Tests:** Ensure `tests/agents/*` run green for orchestrator, web_search, tech_lead, etc.

---

## Prompt Hygiene (this repo’s layout)

- Keep each agent’s prompts in `core/prompts/<agent>/`.  
- Prefer small, composable prompt files: `system.prompt`, `iteration.prompt`, `breakdown.prompt`, etc.  
- Co-evolve prompts with code: any behavior change must include test updates in `tests/agents/`.

---

## Failure Playbook

- Attach `exec_log` snippets when raising issues; include the agent and step (`StepType`) that failed.
- Use `BugHunter` → reproduce → `ProblemSolver` → fix loop.
- For repeated failures, capture new context into `SharedMemory` and refine relevant prompts.

---

## Security & Telemetry

- See `docs/TELEMETRY.md`. Ensure telemetry is **opt‑in** and redacts sensitive data.
- Secrets never land in the repo; document `.env.example` for each scaffolded runtime.

---

## Acceptance Criteria Template

**User Story:** As a <role>, I want <capability> so that <benefit>.

**Acceptance Criteria:**
- Given <initial state>, when <action>, then <observable outcome>.
- Generated code builds & runs; tests pass.
- Logs show no unhandled exceptions; memory retrieval returns relevant context.

---

## PR Description Template

**Summary** — What changed and why.  
**Design Notes** — Key decisions/trade‑offs.  
**Testing** — Commands, data, and results.  
**Risks** — Known risks and mitigations.  
**Follow‑ups** — Prompt updates, docs, or ADRs.

