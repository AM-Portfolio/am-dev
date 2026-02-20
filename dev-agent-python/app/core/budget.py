import logging

logger = logging.getLogger(__name__)

class BudgetExceededError(Exception):
    pass

class BudgetManager:
    """
    Manages token/cost budgets for agents.
    """
    def __init__(self, max_cost_per_job: float = 2.0):
        self.max_cost = max_cost_per_job
        # In memory store for now, move to Redis in Phase 3
        self._usage = {} 

    def add_cost(self, job_id: str, cost: float):
        if job_id not in self._usage:
            self._usage[job_id] = 0.0
        self._usage[job_id] += cost
        self.check_budget(job_id)

    def check_budget(self, job_id: str):
        current = self._usage.get(job_id, 0.0)
        if current > self.max_cost:
            logger.error(f"Job {job_id} exceeded budget: ${current} > ${self.max_cost}")
            raise BudgetExceededError(f"Budget exceeded for job {job_id}")

    def get_usage(self, job_id: str) -> float:
        return self._usage.get(job_id, 0.0)

budget_manager = BudgetManager()
