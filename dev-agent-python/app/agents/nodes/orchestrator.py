import logging
from typing import Dict, List
from app.agents.state import AgentState
from app.agents.logic.strategy_router import strategy_router
from app.agents.logic.completion_checker import completion_checker
from app.core.stream import log_streamer

logger = logging.getLogger(__name__)

async def strategy_node(state: AgentState) -> AgentState:
    """
    Decides the strategic execution mode for the mission.
    """
    job_id = state.get("job_id", "unknown")
    risk_score = state.get("risk_score", 0)
    confidence = 1.0 # Default
    
    strategy = strategy_router.route(risk_score, confidence, state)
    log_streamer.publish_log(job_id, f"⚖️ Orchestrator: Strategy '{strategy}' selected.", "INFO")
    
    return {**state, "strategy": strategy, "status": "strategy_selected"}

async def scheduler_node(state: AgentState) -> AgentState:
    """
    Picks the next task from the TaskGraph (DAG).
    """
    job_id = state.get("job_id", "unknown")
    task_graph = state.get("task_graph", [])
    project_state = state.get("project_state", {})
    completed_ids = [f["id"] for f in project_state.get("features_completed", [])]
    
    # Simple dependency resolution
    next_task = None
    for task in task_graph:
        if task["id"] not in completed_ids:
            # Check if dependencies are met
            deps_met = all(dep_id in completed_ids for dep_id in task.get("dependencies", []))
            if deps_met:
                next_task = task
                break
                
    if next_task:
        log_streamer.publish_log(job_id, f"📅 Scheduler: Next task is '{next_task['name']}' ({next_task['id']})", "INFO")
        return {**state, "current_task": next_task, "status": "task_scheduled"}
    else:
        log_streamer.publish_log(job_id, "🏁 Scheduler: All tasks in graph accounted for.", "SUCCESS")
        return {**state, "current_task": None, "status": "all_tasks_scheduled"}

async def completion_check_node(state: AgentState) -> AgentState:
    """
    Final semantic verification of the mission.
    """
    job_id = state.get("job_id", "unknown")
    satisfied, explanation = completion_checker.check(state)
    
    if satisfied:
        log_streamer.publish_log(job_id, "🏁 Mission Accomplished: Acceptance criteria satisfied.", "SUCCESS")
        return {**state, "status": "mission_success"}
    else:
        log_streamer.publish_log(job_id, f"⚠️ Mission Incomplete: {explanation}", "WARN")
        return {**state, "status": "mission_incomplete", "error": explanation}
