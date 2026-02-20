from app.worker import celery_app
from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.core.budget import budget_manager
from app.core.stream import log_streamer
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def run_agent_workflow(self, user_input: str, job_id: str, repo_url: str = None, repo_path: str = None):
    """
    Executes the LangGraph workflow in a background worker.
    """
    logger.info(f"JOB {job_id}: Starting workflow for '{user_input}' (Repo: {repo_url or 'None'}, Path: {repo_path or 'Default'})")
    log_streamer.publish_log(job_id, f"🚀 Mission Started: {user_input}", "INFO")
    
    # Initialize state
    initial_state: AgentState = {
        "job_id": job_id,
        "user_input": user_input,
        "repo_path": repo_path or f"workspace/{job_id}", # Use provided path or default
        "repo_url": repo_url,
        "plan": None,
        "architecture_guidelines": None,
        "implementation_steps": [],
        "code_diffs": [],
        "file_actions": None,
        "test_results": None,
        "test_errors": None,
        "review_feedback": None,
        "status": "started",
        "error": None,
        "attempts": 0,
        "retry_count": 0
    }
    
    # Run Graph (Async execution in sync task requires asyncio.run)
    config = {"configurable": {"thread_id": job_id}}

    try:
        # Check budget first
        budget_manager.check_budget(job_id)

        # Run Graph with Async Persistence
        from app.agents.graph import workflow
        from langgraph.checkpoint.memory import MemorySaver

        async def _run_workflow():
            # improved: Use MemorySaver for stability (SqliteSaver caused import issues)
            memory = MemorySaver()
            app = workflow.compile(checkpointer=memory)
            return await app.ainvoke(initial_state, config=config)

        final_state = asyncio.run(_run_workflow())
        
        return final_state

    except Exception as e:
        logger.error(f"JOB {job_id}: Failed with {e}")
        # Phase 3.3: Handle failure/rollback here if needed
        return {"status": "failed", "error": str(e)}
