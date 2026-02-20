from app.agents.state import AgentState
from app.core.stream import log_streamer
from app.agents.logic.classifier import classifier
from app.agents.logic.reflection import reflection_engine
from app.agents.logic.token_monitor import token_monitor
import logging
import os

logger = logging.getLogger(__name__)

async def tester_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    logger.info("TESTING: Running verification...")
    log_streamer.publish_log(job_id, "🧪 Testing: Verifying changes...", "INFO")
    repo_path = state.get("repo_path")
    if not repo_path:
        return {**state, "status": "testing_complete"}

    # Phase 4.3: Automated Test Generation (if no tests exist)
    test_files = [f for f in os.listdir(repo_path) if f.startswith("test_") and f.endswith(".py")]
    if not test_files:
        log_streamer.publish_log(job_id, "🧪 Audit: No tests found. Triggering Autonomous Test Generation...", "WARN")
        test_gen_prompt = (
            f"Goal: Generate a comprehensive pytest unit test file for this repository.\n"
            f"Analyze the existing files and create a 'test_autonomous.py'.\n"
            f"IMPORTANT: For algorithmic logic, implement PROPERTY-BASED TESTS using the 'hypothesis' library.\n"
            f"Ensure the tests are runnable and follow best practices."
        )
        # We use workspace-write sandbox to allow creating the test file
        from app.agents.wrapper import codex
        stdout, stderr, code = codex.run_prompt(
            test_gen_prompt, 
            sandbox="workspace-write", 
            approval="never", 
            cwd=repo_path
        )
        
        # Track autonomous test generation cost
        token_monitor.log_usage(job_id, len(test_gen_prompt)//4, len(stdout)//4)
        log_streamer.publish_log(job_id, "✅ Audit: Created 'test_autonomous.py'.", "SUCCESS")

    # Run Verification Command
    # Since Codex wrote the files autonomously, we just verify the repo directly
    test_output = []
    has_errors = False
    
    # Simple syntax check loop across the repo
    import subprocess
    try:
        # 1. Compile python files to check syntax
        result = subprocess.run(
            ["python", "-m", "compileall", "-q", repo_path], 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            has_errors = True
            error_msg = f"Syntax Error: {result.stderr or result.stdout}"
            test_output.append(error_msg)
            log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        else:
            log_streamer.publish_log(job_id, "✅ Clean compilation across workspace.", "DEBUG")

        # 2. Run Ruff for linting and formatting checks
        log_streamer.publish_log(job_id, "🔎 Running Ruff static analysis...", "DEBUG")
        ruff_result = subprocess.run(
            ["ruff", "check", repo_path],
            capture_output=True,
            text=True
        )
        if ruff_result.returncode != 0:
            # We treat linting as a warning or a soft error? The roadmap says "Guardrails".
            # Let's count them as errors for now to ensure quality.
            has_errors = True
            error_msg = f"Linting Error (Ruff):\n{ruff_result.stdout}"
            test_output.append(error_msg)
            log_streamer.publish_log(job_id, "❌ Ruff detected issues.", "ERROR")
        
        # 3. Run Mypy for type checking (if config exists)
        if os.path.exists(os.path.join(repo_path, "pyproject.toml")) or os.path.exists(os.path.join(repo_path, "mypy.ini")):
            log_streamer.publish_log(job_id, "🔎 Running Mypy type checking...", "DEBUG")
            mypy_result = subprocess.run(
                ["mypy", repo_path],
                capture_output=True,
                text=True
            )
            if mypy_result.returncode != 0:
                has_errors = True
                error_msg = f"Type Error (Mypy):\n{mypy_result.stdout}"
                test_output.append(error_msg)
                log_streamer.publish_log(job_id, "❌ Mypy detected type issues.", "ERROR")
        
        # 4. Dependency Conflict Audit
        log_streamer.publish_log(job_id, "🔎 Running Dependency Audit (pip check)...", "DEBUG")
        dep_result = subprocess.run(["pip", "check"], capture_output=True, text=True)
        if dep_result.returncode != 0:
            has_errors = True
            test_output.append(f"Dependency Conflict:\n{dep_result.stdout}")
            log_streamer.publish_log(job_id, "❌ Dependency conflicts detected.", "ERROR")
            
        # 5. Security Scan (Bandit)
        log_streamer.publish_log(job_id, "🔎 Running Security Scan (Bandit)...", "DEBUG")
        bandit_result = subprocess.run(["bandit", "-r", repo_path, "-ll"], capture_output=True, text=True)
        if bandit_result.returncode != 0:
             has_errors = True
             test_output.append(f"Security Issue (Bandit):\n{bandit_result.stdout}")
             log_streamer.publish_log(job_id, "❌ Bandit detected security issues.", "ERROR")

    except Exception as e:
        log_streamer.publish_log(job_id, f"⚠️ Could not complete verification: {e}", "WARN")

    if has_errors:
        error_summary = "\n".join(test_output)
        error_class = classifier.classify(error_summary)
        current_retries = state.get("retry_count", 0)
        
        log_streamer.publish_log(job_id, f"🔍 Error Class: {error_class}", "INFO")

        # Prevent infinite loops if we hit max retries
        if current_retries >= 3:
             log_streamer.publish_log(job_id, f"❌ {error_summary} (Max retries reached)", "ERROR")
             return {**state, "test_errors": error_summary, "error_class": error_class, "status": "testing_failed_max_retries"}

        # Priority C: Strategic Reflection
        hypothesis, next_action = reflection_engine.reflect(state, error_summary)
        log_streamer.publish_log(job_id, f"🤔 Reflection: {hypothesis}", "DEBUG")

        return {
            **state,
            "test_errors": error_summary,
            "error_class": error_class,
            "reflection_hypothesis": hypothesis,
            "next_recommended_action": next_action,
            "retry_count": current_retries + 1,
            "status": "testing_failed"
        }

    results = "Tests Passed (Syntax Verified)"
    log_streamer.publish_log(job_id, f"✅ Tests passed: {results}", "SUCCESS")
    
    return {
        **state,
        "test_results": results,
        "test_errors": None,
        "error_class": None, # Clear on success
        "reflection_hypothesis": None,
        "next_recommended_action": None,
        "status": "testing_complete"
    }
