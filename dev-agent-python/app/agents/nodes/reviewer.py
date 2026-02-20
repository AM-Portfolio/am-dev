from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
import logging

logger = logging.getLogger(__name__)

async def reviewer_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    
    logger.info("REVIEWING: Analyzing changes...")
    log_streamer.publish_log(job_id, "🧐 Review: Analyzing changes...", "INFO")
    
    prompt = f"Review these changes:\n{state.get('code_diffs', [])}\n\nTest Results:\n{state.get('test_results', '')}\n\nApprove or Reject?"
    
    # Call LLM
    review_output, stderr, code = codex.run_prompt(prompt)
    
    # Save Artifact
    import os
    repo_path = state.get("repo_path")
    if repo_path and review_output:
        artifact_dir = os.path.join(repo_path, ".agent_artifacts")
        os.makedirs(artifact_dir, exist_ok=True)
        with open(os.path.join(artifact_dir, "code_review.md"), "w", encoding="utf-8") as f:
            f.write(f"# Automated Code Review\n\n{review_output}")
        log_streamer.publish_log(job_id, f"📄 Saved review artifact to {artifact_dir}", "INFO")

    start_excerpt =  review_output[:50] + "..." if review_output else "No feedback"
    log_streamer.publish_log(job_id, f"📝 Feedback: {start_excerpt}", "INFO")
    
    return {
        **state,
        "review_feedback": review_output,
        "status": "completed" # End of loop for now
    }
