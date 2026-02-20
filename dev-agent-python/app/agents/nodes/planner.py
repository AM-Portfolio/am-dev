from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
import logging

logger = logging.getLogger(__name__)

async def planner_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    user_input = state.get("user_input", "")
    
    logger.info("PLANNING: Generating plan...")
    log_streamer.publish_log(job_id, f"🧠 Planning: Generating implementation plan for '{user_input}'...", "INFO")
    
    prompt = f"Create a step-by-step implementation plan for: {user_input}"
    
    # Call LLM
    plan_text, stderr, code = codex.run_prompt(prompt)
    
    if code != 0:
        error_msg = f"Planning failed: {stderr}"
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "failed", "error": error_msg}
        
    # Save Artifact
    import os
    repo_path = state.get("repo_path")
    if repo_path:
        artifact_dir = os.path.join(repo_path, ".agent_artifacts")
        os.makedirs(artifact_dir, exist_ok=True)
        with open(os.path.join(artifact_dir, "planning_summary.md"), "w", encoding="utf-8") as f:
            f.write(f"# Implementation Plan\n\nGenerated for: {user_input}\n\n{plan_text}")
        log_streamer.publish_log(job_id, f"📄 Saved planning artifact to {artifact_dir}", "INFO")

    log_streamer.publish_log(job_id, "✅ Plan generated successfully", "SUCCESS")
    return {
        **state,
        "plan": plan_text,
        "status": "planning_complete",
        "attempts": state.get("attempts", 0)
    }
