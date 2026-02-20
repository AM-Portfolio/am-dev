from app.agents.state import AgentState
from app.core.stream import log_streamer
from app.agents.graph import agent_graph
import asyncio

logger = logging.getLogger(__name__)

class JobController:
    """
    Manages the lifecycle of autonomous missions (start, cancel, tracking).
    """
    
    def __init__(self):
        self.active_jobs: Dict[str, dict] = {}

    def start_job(self, user_input: str, repo_url: Optional[str] = None) -> str:
        """
        Initializes a new autonomous mission.
        """
        job_id = str(uuid.uuid4())[:8]
        logger.info(f"JOB CONTROLLER: Starting new job {job_id} for mission: {user_input}")
        
        # Initial state setup
        initial_state: AgentState = {
            "job_id": job_id,
            "user_input": user_input,
            "repo_url": repo_url,
            "status": "starting",
            "repo_path": f"workspace/{job_id}",
            "plan": None,
            "task_graph": [],
            "project_state": {},
            "strategy": None,
            "attempts": 0,
            "retry_count": 0,
            "test_errors": None,
            "error_class": None,
            "original_branch": None,
            "risk_score": 0,
            "reflection_hypothesis": None,
            "next_recommended_action": None
        }
        
        self.active_jobs[job_id] = {"state": initial_state, "cancelled": False}
        log_streamer.publish_log(job_id, f"🚀 Job {job_id} initiated.", "SUCCESS")
        
        # In a production system, we'd spawn a background task:
        # asyncio.create_task(self.execute_job(job_id, initial_state))
        
        return job_id

    async def execute_job(self, job_id: str, state: AgentState):
        """
        Runs the autonomous mission through the LangGraph workflow.
        """
        logger.info(f"JOB CONTROLLER: Executing job {job_id} workflow...")
        try:
            # We use the compiled graph
            final_state = await agent_graph.ainvoke(state)
            self.active_jobs[job_id]["state"] = final_state
            log_streamer.publish_log(job_id, f"🏁 Job {job_id} completed with status: {final_state.get('status')}", "SUCCESS")
        except Exception as e:
            logger.error(f"JOB CONTROLLER: Job {job_id} failed during execution: {e}")
            log_streamer.publish_log(job_id, f"❌ Job {job_id} failed: {str(e)}", "ERROR")

    def cancel_job(self, job_id: str):
        """
        Safely marks a job as cancelled.
        """
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["cancelled"] = True
            logger.warning(f"JOB CONTROLLER: Job {job_id} has been marked for cancellation.")
            log_streamer.publish_log(job_id, "🛑 Job cancellation requested. Cleaning up...", "WARN")
            
            # Logic for physical cleanup (branch deletion) would go here or in the graph's cleanup node
        else:
            logger.error(f"JOB CONTROLLER: Job {job_id} not found.")

    def is_cancelled(self, job_id: str) -> bool:
        return self.active_jobs.get(job_id, {}).get("cancelled", False)

job_controller = JobController()
