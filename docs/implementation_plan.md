# Implementation Plan: Dev-Agent Product (Auto-Pilot Mode)

## Goal Description
Build the **Python Core Module** (`dev-agent-python`) to replace the TypeScript orchestrator. The goal is a production-grade, pure Python system handling planning, execution, and monitoring.

> [!IMPORTANT]
> **Execution Strategy**: This plan is designed for **Autonomous Execution**. The agent will proceed phase-by-phase, making best-effort technical decisions and running basic verification tests without waiting for human approval.

## Technology Stack
*   **Language**: Python 3.10+
*   **Framework**: FastAPI (API), Celery (Async), LangGraph (Agents)
*   **Database**: Redis (Queue), SQLite (State), FAISS (Vector)
*   **Frontend**: Flutter Web

## Phase 1: Foundation (The Brain)
**Goal**: Establish the Python project structure and reliable Codex integration.
*   **Task 1.1**: Bootstrap `dev-agent-python`.
    *   Initialize `poetry`, `fastapi`, `pydantic-settings`.
    *   *Test*: Run `uvicorn` and hit `/health` endpoint.
*   **Task 1.2**: Implement `CodexConnector`.
    *   Create `app/agents/wrapper.py` using `subprocess` with timeout & sanitization.
    *   *Test*: Run a simple "Hello World" prompt via the wrapper and verify output.
*   **Task 1.3**: Implement `GitTools`.
    *   Create `app/git_tools.py` for commit, checkout, log.
    *   *Test*: Script that helps create a dummy commit and verifies `git log`.
*   **Task 1.4**: API Security.
    *   Add API Key middleware + Rate Limiter.
    *   *Test*: `curl` without key (expect 403), with key (expect 200).

## Phase 2: Intelligent Agents (The Speed)
**Goal**: Enable complex, multi-step agent behaviors.
*   **Task 2.1**: LangGraph Workflow.
    *   Implement nodes: Planner -> Coder -> Tester -> Reviewer.
    *   *Test*: Run a mock workflow that cycles through nodes.
*   **Task 2.2**: State Persistence.
    *   Configure SQLite Checkpointer.
    *   *Test*: Interrupt a workflow, restart app, resume workflow.
*   **Task 2.3**: Parallel Merge Logic.
    *   Implement branch-per-agent strategy.
    *   *Test*: Create 2 branches, merge them into main using the orchestrator.

## Phase 3: Fire & Forget (The Product)
**Goal**: Async execution and reliability.
*   **Task 3.1**: Celery + Redis.
    *   Move LangGraph execution to background workers.
    *   *Test*: Submit job, get ID, query status until 'completed'.
*   **Task 3.2**: WebSocket Streaming.
    *   Stream agent logs to frontend.
    *   *Test*: Connect `wscat` and see real-time log events.
*   **Task 3.3**: Job Cancellation.
    *   Implement `cancel_job(id)` logic (revoke Celery task + git reset).
    *   *Test*: Start long job, cancel it, verify rollback.

## Phase 4: Product Experience (Flutter UI)
**Goal**: User-facing monitoring and control.
*   **Task 4.1**: Flutter Scaffold.
    *   Setup `dev-agent-ui` with WebSocket client.
    *   *Test*: Load page, connect to backend.
*   **Task 4.2**: Agent Monitor.
    *   Build UI for live logs and progress.
    *   *Test*: Visual check of log streaming.
*   **Task 4.3**: Safety Controls.
    *   Implement "Approval Dialog" for interrupts.
    *   *Test*: Trigger interrupt, click "Approve" in UI, verify resumption.
