from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
from app.agents.logic.token_monitor import token_monitor
import logging
import os

logger = logging.getLogger(__name__)

async def coder_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    repo_path = state.get("repo_path")
    
    logger.info("CODING: Implementing plan autonomously...")
    
    plan = state.get("plan", "No plan available")
    current_task = state.get("current_task")
    reflection_hypothesis = state.get("reflection_hypothesis")
    guidelines = state.get("architecture_guidelines", "")
    test_errors = state.get("test_errors", None)
    retry_count = state.get("retry_count", 0)
    
    # We can inject an AGENTS.md dynamically into the repo path
    if repo_path:
        agents_content = (
            "You are the Greater God Agent Coder.\n"
            "Your objective is to read the repository, implement the requested features, and edit the files directly.\n"
            "You have full write access to the workspace. Do not ask for user approval.\n"
            f"{guidelines}\n"
        )
        try:
            with open(os.path.join(repo_path, "AGENTS.md"), "w", encoding="utf-8") as f:
                f.write(agents_content)
        except Exception as e:
            logger.warning(f"Could not write AGENTS.md: {e}")

    # Define strict JSON contract for the response
    CODEX_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success", "incomplete", "failed"]},
            "intent": {"type": "string"},
            "files_modified": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["status", "intent", "files_modified"]
    }

    if test_errors:
        log_streamer.publish_log(job_id, f"♻️ Retry #{retry_count}: Fixing errors for task '{current_task['name'] if current_task else 'Current Task'}'...", "WARN")
        # Retry Prompt with Reflection
        reflection_context = f"\n\nReflection/Hypothesis: {reflection_hypothesis}" if reflection_hypothesis else ""
        prompt = (
            f"IMPORTANT: You MUST start your response with a JSON block.\n"
            f"JSON Format: {{\"status\": \"...\", \"intent\": \"...\", \"files_modified\": [...]}}\n\n"
            f"Goal: Fix errors in task '{current_task['name'] if current_task else 'Current Task'}'.\n"
            f"Task Description: {current_task['description'] if current_task else plan}\n"
            f"Errors Encountered:\n{test_errors}"
            f"{reflection_context}\n\n"
            f"Please edit the files directly to resolve these errors."
        )
    else:
        task_name = current_task['name'] if current_task else "mission components"
        log_streamer.publish_log(job_id, f"👨‍💻 Coding: Implementing task '{task_name}'...", "INFO")
        prompt = (
            f"IMPORTANT: You MUST start your response with a JSON block.\n"
            f"JSON Format: {{\"status\": \"...\", \"intent\": \"...\", \"files_modified\": [...]}}\n\n"
            f"Goal: Implement atomic task '{task_name}'.\n"
            f"Description: {current_task['description'] if current_task else plan}\n"
            f"Acceptance Criteria: {', '.join(current_task.get('acceptance_criteria', [])) if current_task else 'N/A'}\n\n"
            f"Please write the code and modify the necessary files in the workspace directly."
        )
    
    # Call LLM with streaming logging
    def stream_callback(line: str):
        if line.strip():
            log_streamer.publish_log(job_id, f"🤖 {line.strip()}", "DEBUG")

    # Fire and Forget execution
    code_text, stderr, exit_code = codex.run_prompt(
        prompt, 
        log_callback=stream_callback,
        sandbox="workspace-write",
        approval="never",
        cwd=repo_path,
        expected_schema=CODEX_RESPONSE_SCHEMA
    )
    
    # Track coding cost
    token_monitor.log_usage(job_id, len(prompt)//4, len(code_text)//4)
    
    if exit_code != 0:
        error_msg = f"Coding failed: {stderr or code_text}"
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "failed", "error": error_msg}

    log_streamer.publish_log(job_id, f"✅ Autonomous coding execution completed.", "SUCCESS")

    # Extract files_modified from validated JSON
    import re
    files_modified = []
    json_match = re.search(r"AGENT_JSON_START:\s*(\{.*?\})", code_text, re.MULTILINE)
    if json_match:
        try:
             files_modified = json.loads(json_match.group(1)).get("files_modified", [])
        except:
             pass

    return {
        **state,
        "code_diffs": [code_text],
        "files_modified": files_modified,
        "status": "coding_complete"
    }
