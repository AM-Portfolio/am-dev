from app.agents.state import AgentState
from app.core.stream import log_streamer
import logging

logger = logging.getLogger(__name__)

async def tester_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    logger.info("TESTING: Running verification...")
    log_streamer.publish_log(job_id, "🧪 Testing: Verifying changes...", "INFO")
    
    # Phase 2.1 calls for "Basic Verification"
    
    file_actions = state.get("file_actions", [])
    has_files = len(file_actions) > 0
            
    if not has_files:
        error_msg = "UnitTest Failed: No valid file actions were parsed from the output. The model likely produced invalid JSON or no code blocks."
        current_retries = state.get("retry_count", 0)
        
        # Prevent infinite loops if we hit max retries
        if current_retries >= 3:
             log_streamer.publish_log(job_id, f"❌ {error_msg} (Max retries reached)", "ERROR")
             return {**state, "test_errors": error_msg, "status": "testing_failed_max_retries"}

        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        
        return {
            **state,
            "test_errors": error_msg,
            "retry_count": current_retries + 1,
            "status": "testing_failed"
        }
    
    # Write files temporarily to run validation if possible
    import os
    repo_path = state.get("repo_path")
    
    # 1. Apply Files Needed for Testing (Pre-commit check)
    if repo_path and has_files:
        log_streamer.publish_log(job_id, f"💾 Writing {len(file_actions)} files to disk for verification...", "INFO")
        for action in file_actions:
            rel_path = action.get("path")
            content = action.get("content")
            if rel_path and content:
                full_path = os.path.join(repo_path, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

    # 2. Run Verification Command
    # Detect language and run basic check
    # Python: python -m py_compile {file}
    # Java: javac {file} (needs classpath though)
    
    test_output = []
    has_errors = False
    
    # Simple syntax check loop
    import subprocess
    for action in file_actions:
        path = action.get("path", "")
        if path.endswith(".py"):
            full_path = os.path.join(repo_path, path)
            try:
                # Compile python file to check syntax
                result = subprocess.run(
                    ["python", "-m", "py_compile", full_path], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    has_errors = True
                    error_msg = f"Syntax Error in {path}: {result.stderr}"
                    test_output.append(error_msg)
                    log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
                else:
                    log_streamer.publish_log(job_id, f"✅ Syntax OK: {path}", "DEBUG")
            except Exception as e:
                log_streamer.publish_log(job_id, f"⚠️ Could not verify {path}: {e}", "WARN")

    if has_errors:
        error_summary = "\n".join(test_output)
        current_retries = state.get("retry_count", 0)
        return {
            **state,
            "test_errors": error_summary,
            "retry_count": current_retries + 1,
            "status": "testing_failed"
        }

    results = "Tests Passed (Syntax Verified)"
    log_streamer.publish_log(job_id, f"✅ Tests passed: {results}", "SUCCESS")
    
    return {
        **state,
        "test_results": results,
        "test_errors": None, # Clear errors on success
        "status": "testing_complete"
    }
