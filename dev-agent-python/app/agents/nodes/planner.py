from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
from app.agents.logic.token_monitor import token_monitor
import logging

logger = logging.getLogger(__name__)

async def planner_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    user_input = state.get("user_input", "")
    
    logger.info("PLANNING: Generating plan...")
    log_streamer.publish_log(job_id, f"🧠 Planning: Generating implementation plan for '{user_input}'...", "INFO")
    
    prompt = (
        f"Goal: Create a structured Task Graph for the mission: {user_input}\n\n"
        f"You must output a JSON list of tasks. Each task must have: 'id', 'name', 'dependencies' (list of IDs).\n\n"
        f"Format: AGENT_JSON_START: {{\"task_graph\": [{{...}}]}}\n"
    )
    
    # Define Task Graph Schema
    expected_schema = {
        "type": "object",
        "properties": {
            "task_graph": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "dependencies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["id", "name", "dependencies"]
                }
            }
        },
        "required": ["task_graph"]
    }

    # Call LLM with framing and schema validation
    plan_text, stderr, code = codex.run_prompt(
        prompt, 
        expected_schema=expected_schema,
        approval="never"
    )
    
    # Track planning cost
    token_monitor.log_usage(job_id, len(prompt)//4, len(plan_text)//4)
    
    if code != 0:
        error_msg = f"Planning failed: {stderr}"
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "failed", "error": error_msg}

    # Extract Task Graph from validated JSON
    import re
    task_graph = []
    json_match = re.search(r"AGENT_JSON_START:\s*(\{.*?\})", plan_text, re.MULTILINE)
    if json_match:
        try:
            task_graph = json.loads(json_match.group(1)).get("task_graph", [])
        except:
             pass
        
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
        "task_graph": task_graph,
        "status": "planning_complete",
        "attempts": state.get("attempts", 0)
    }
