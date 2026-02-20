import logging
from typing import Dict

logger = logging.getLogger(__name__)

class TokenMonitor:
    """
    Tracks token consumption per job and enforces budget thresholds.
    """
    
    def __init__(self, max_tokens_per_job: int = 200000):
        self.max_tokens_per_job = max_tokens_per_job
        self.job_usage: Dict[str, int] = {}

    def log_usage(self, job_id: str, tokens_in: int, tokens_out: int):
        """
        Records token usage for a specific job.
        """
        total = tokens_in + tokens_out
        if job_id not in self.job_usage:
            self.job_usage[job_id] = 0
            
        self.job_usage[job_id] += total
        
        usage = self.job_usage[job_id]
        logger.info(f"TOKEN MONITOR: Job {job_id} usage: {usage} total tokens.")
        
        if usage > self.max_tokens_per_job:
            logger.warning(f"⚠️ BUDGET EXCEEDED: Job {job_id} has used {usage} tokens (Limit: {self.max_tokens_per_job}).")
            # In a real impl, this would return an Abort signal to the controller

    def get_usage(self, job_id: str) -> int:
        return self.job_usage.get(job_id, 0)

    def is_within_budget(self, job_id: str) -> bool:
        return self.job_usage.get(job_id, 0) <= self.max_tokens_per_job

token_monitor = TokenMonitor()
