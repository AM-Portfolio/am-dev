import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ReActGuard:
    """
    Enforces ReAct behavioral discipline: call caps and oscillation detection.
    """
    
    def __init__(self, max_calls_per_task: int = 6, max_repeated_actions: int = 3):
        self.max_calls_per_task = max_calls_per_task
        self.max_repeated_actions = max_repeated_actions
        # (job_id, task_id) -> list of action strings
        self.history: Dict[tuple, List[str]] = {}

    def track_action(self, job_id: str, task_id: str, action: str) -> bool:
        """
        Tracks a ReAct action. Returns False if a policy is violated.
        """
        key = (job_id, task_id)
        if key not in self.history:
            self.history[key] = []
            
        history = self.history[key]
        history.append(action)
        
        # 1. Check Call Cap
        if len(history) > self.max_calls_per_task:
            logger.warning(f"⚠️ REACT GUARD: Max calls ({self.max_calls_per_task}) exceeded for task {task_id}.")
            return False
            
        # 2. Check Oscillation (Repeated Actions)
        if history.count(action) >= self.max_repeated_actions:
            logger.warning(f"⚠️ REACT GUARD: Tool oscillation detected! Action '{action}' repeated {self.max_repeated_actions} times.")
            return False
            
        return True

    def reset_task(self, job_id: str, task_id: str):
        key = (job_id, task_id)
        if key in self.history:
            del self.history[key]

react_guard = ReActGuard()
