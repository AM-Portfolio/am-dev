from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
import logging

logger = logging.getLogger(__name__)

async def coder_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    logger.info("CODING: Implementing plan...")
    
    plan = state.get("plan", "No plan available")
    guidelines = state.get("architecture_guidelines", "")
    test_errors = state.get("test_errors", None)
    retry_count = state.get("retry_count", 0)
    
    if test_errors:
        log_streamer.publish_log(job_id, f"♻️ Retry #{retry_count}: Fixing errors...", "WARN")
        # Retry Prompt: Be extremely explicit about the format again
        prompt = (
            f"Goal: Fix the following implementation errors.\n"
            f"Original Plan Request:\n{plan}\n\n"
            f"Errors Encountered:\n{test_errors}\n\n"
            f"CRITICAL INSTRUCTION: You MUST provide the corrected code as a valid JSON array.\n"
            f"Do NOT write any conversational text or thinking blocks.\n"
            f"Format: [{{\"path\": \"src/snake_game.py\", \"content\": \"import pygame...\"}}]\n"
            f"Task: Provide ONLY the JSON array."
        )
    else:
        log_streamer.publish_log(job_id, "👨‍💻 Coding: Implementing solution...", "INFO")
        prompt = (
            f"Goal: Implement the following plan in code.\n"
            f"Plan:\n{plan}\n\n"
            f"Architecture Guidelines:\n{guidelines}\n\n"
            f"IMPORTANT: Return the output as a SINGLE JSON array of file objects to be written to disk.\n"
            f"Format: [{{\"path\": \"src/main.py\", \"content\": \"...\"}}]\n"
            f"Do NOT wrap in markdown blocks. Just raw JSON."
        )
    
    # Call LLM with streaming logging
    def stream_callback(line: str):
        if line.strip():
            # Use 'DEBUG' level so frontend can filter or show as verbose logs
            # Prefix with emoji to make it clear it's from the bot's internal process
            job_id = state.get("job_id", "unknown")  # Grab ID from state since it's cleaner
            log_streamer.publish_log(job_id, f"🤖 {line.strip()}", "DEBUG")

    code_text, stderr, code = codex.run_prompt(prompt, log_callback=stream_callback)
    
    if code != 0:
        error_msg = f"Coding failed: {stderr}"
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "failed", "error": error_msg}

    # Attempt to parse JSON response for file actions
    import json
    import os
    file_actions = []
    
    # Save Artifact (Raw Implementation Response/Plan)
    repo_path = state.get("repo_path")
    if repo_path and code_text:
        artifact_dir = os.path.join(repo_path, ".agent_artifacts")
        os.makedirs(artifact_dir, exist_ok=True)
        with open(os.path.join(artifact_dir, "implementation_plan.md"), "w", encoding="utf-8") as f:
            f.write(f"# Implementation Details\n\n## Generation Output\n\n{code_text}")
        log_streamer.publish_log(job_id, f"📄 Saved implementation artifact to {artifact_dir}", "INFO")
    
    # Write the raw output first for debugging
    output_dir = "generated_output"
    os.makedirs(output_dir, exist_ok=True)
    debug_file = os.path.join(output_dir, f"{job_id}_raw_response.txt")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(code_text)
    
    try:
        # Strip markdown if model is stubborn
        clean_text = code_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"): # Use elif to avoid double stripping
             clean_text = clean_text[3:] 
             
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        file_actions = json.loads(clean_text)
        log_streamer.publish_log(job_id, f"✅ Generated {len(file_actions)} file actions for application.", "SUCCESS")
    except Exception as e: # Catch broadly
        log_streamer.publish_log(job_id, f"⚠️ Failed to parse structured JSON response: {e}. Returning raw text.", "WARN")
        # For Snake, maybe we can regex extract python blocks? as fallback
        import re
        # Try finding markdown python blocks
        python_blocks = re.findall(r"```python(.*?)```", code_text, re.DOTALL | re.IGNORECASE)
        if not python_blocks:
             # Try Just code block
             python_blocks = re.findall(r"```(.*?)```", code_text, re.DOTALL)

        if python_blocks:
             # If multiple blocks, maybe combine them or just take the largest?
             # For now, let's assume one main file or concat
             combined_content = "\n\n".join(python_blocks)
             file_actions = [{"path": "snake_game.py", "content": combined_content}]
             log_streamer.publish_log(job_id, f"✅ Extracted Code block as fallback.", "SUCCESS")

    return {
        **state,
        "code_diffs": [code_text],
        "file_actions": file_actions,
        "status": "coding_complete"
    }
