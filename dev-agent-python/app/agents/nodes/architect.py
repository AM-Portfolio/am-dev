from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
import logging

logger = logging.getLogger(__name__)

async def architect_node(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "unknown")
    plan = state.get("plan", "")
    
    logger.info("ARCHITECT: Designing structure...")
    log_streamer.publish_log(job_id, "🏗️ Architect: Designing system patterns...", "INFO")
    
    prompt = (
        f"Role: Software Architect\n"
        f"Goal: Create comprehensive architectural guidelines based on the plan.\n"
        f"Plan:\n{plan}\n\n"
        f"Requirements:\n"
        f"1. Define file structure and modules.\n"
        f"2. Specify design patterns (e.g., MVVM, Repository Pattern, Vertical Slicing).\n"
        f"3. Enforce clean code principles (SOLID, DRY).\n"
        f"4. Identify key interfaces and data models.\n"
        f"Return ONLY the markdown design document."
    )
    
    # We can invoke the wrapper directly
    # For architecture, streaming might be nice too to show "Designing..."
    def stream_callback(line: str):
        if line.strip():
            log_streamer.publish_log(job_id, f"📐 {line.strip()}", "DEBUG")

    design_doc, stderr, _ = codex.run_prompt(prompt, log_callback=stream_callback)
    
    if not design_doc:
        design_doc = "No architectural guidelines generated. Proceeding with default structure."
        log_streamer.publish_log(job_id, f"⚠️ Architecture generation failed: {stderr}", "WARN")
    else:
        # Save Artifact
        import os
        repo_path = state.get("repo_path")
        if repo_path:
            artifact_dir = os.path.join(repo_path, ".agent_artifacts")
            os.makedirs(artifact_dir, exist_ok=True)
            with open(os.path.join(artifact_dir, "architecture_design.md"), "w", encoding="utf-8") as f:
                f.write(f"# Architectural Guidelines\n\n{design_doc}")
            log_streamer.publish_log(job_id, f"📄 Saved architecture artifact to {artifact_dir}", "INFO")

        log_streamer.publish_log(job_id, "✅ Architecture design complete.", "SUCCESS")
    
    return {
        **state,
        "architecture_guidelines": design_doc,
        "status": "designed"
    }
