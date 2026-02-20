import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Strategy:
    DIRECT_APPLY = "direct-apply"
    PR_ONLY = "pr-only"
    TEST_FIRST = "test-first"
    REACT_MODE = "react-mode"
    HUMAN_ESCALATION = "human-escalation"

class StrategyRouter:
    """
    Selecting the optimal execution mode for a task based on risk, confidence, and state.
    """
    
    def route(self, risk_score: int, confidence: float, state: Dict) -> str:
        """
        Maps inputs to a strategy string.
        """
        # 1. Human Escalation (Safety First)
        if risk_score > 85 or confidence < 0.2:
            logger.warning(f"Strategy: Critical Risk ({risk_score}) or Low Confidence ({confidence}). Escalating.")
            return Strategy.HUMAN_ESCALATION
            
        # 2. ReAct Mode (Complex Missions)
        # If the task graph is large or we are in a multi-step project
        task_graph = state.get("task_graph", [])
        if len(task_graph) > 3:
            logger.info("Strategy: Complex mission detected. Routing to ReAct Mode.")
            return Strategy.REACT_MODE
            
        # 3. Test-First (Medium-High Risk with Existing Tests)
        # If repo has tests, and risk is non-trivial, force test-first
        repo_path = state.get("repo_path", "")
        import os
        has_tests = False
        if repo_path and os.path.exists(repo_path):
            test_files = [f for f in os.listdir(repo_path) if f.startswith("test_") and f.endswith(".py")]
            has_tests = len(test_files) > 0
            
        if risk_score > 50 and has_tests:
            logger.info(f"Strategy: Moderate Risk ({risk_score}) with existing tests. Routing to Test-First.")
            return Strategy.TEST_FIRST
            
        # 4. PR-Only (Moderate-High Risk without confidence to auto-merge)
        if risk_score > 60:
            logger.info(f"Strategy: Moderate-High Risk ({risk_score}). Routing to PR-Only.")
            return Strategy.PR_ONLY
            
        # 5. Direct Apply (Low Risk, High Confidence)
        if risk_score < 35 and confidence > 0.7:
            logger.info(f"Strategy: Low Risk ({risk_score}) and High Confidence ({confidence}). Routing to Direct Apply.")
            return Strategy.DIRECT_APPLY
            
        # Default fallback
        logger.info("Strategy: Default fallback to PR-Only for safety.")
        return Strategy.PR_ONLY

strategy_router = StrategyRouter()
