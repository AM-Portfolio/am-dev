import shutil
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class RuntimeHealth:
    """
    Verifies that the execution environment has the necessary tools.
    """
    REQUIRED_TOOLS = ["docker", "node", "npm", "git", "python"]
    
    @classmethod
    def check_health(cls) -> Dict[str, bool]:
        """
        Checks for the existence of required tools.
        Returns a dict of tool -> installed (bool).
        """
        status = {}
        for tool in cls.REQUIRED_TOOLS:
            path = shutil.which(tool)
            status[tool] = path is not None
            if not path:
                logger.warning(f"Runtime Check: '{tool}' not found in PATH.")
        
        return status

    @classmethod
    def assert_healthy(cls):
        status = cls.check_health()
        missing = [t for t, installed in status.items() if not installed]
        if missing:
            raise RuntimeError(f"Missing required tools: {', '.join(missing)}")

runtime_health = RuntimeHealth()
