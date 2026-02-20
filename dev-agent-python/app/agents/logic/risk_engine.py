import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class RiskScore:
    LOW = 30
    MEDIUM = 70
    HIGH = 90
    CRITICAL = 100

class RiskEngine:
    """
    Heuristic engine to score the risk/danger level of an autonomous mission.
    """
    
    SENSITIVE_PATHS = [
        r"auth/", r"security/", r"database/", r"infra/", 
        r"\.env", r"config/", r"secrets/", r"billing/",
        r"main\.py$", r"app\.py$", r"settings\.py$", r"kernel/"
    ]
    
    DANGEROUS_KEYWORDS = [
        r"secrets", r"password", r"cryptography", r"token",
        r"delete", r"drop", r"truncate", r"rm -rf", r"sudo",
        r"chmod", r"chown", r"eval\(", r"exec\("
    ]

    def calculate_score(self, manifest: Dict, confidence: float = 1.0) -> int:
        """
        Calculates a risk score from 0-100 based on the job manifest and metadata.
        """
        score = 0
        file_list = manifest.get("files", {})
        
        # 1. Path Sensitivity (Max 40 points)
        path_hits = 0
        for file_path in file_list:
            if any(re.search(pattern, file_path.lower()) for pattern in self.SENSITIVE_PATHS):
                path_hits += 1
        
        if path_hits > 0:
            score += min(40, 20 + (path_hits * 5))
            logger.info(f"Risk: {path_hits} sensitive paths detected.")

        # 2. Diff Complexity (Max 30 points)
        file_count = len(file_list)
        if file_count > 10:
            score += 30
        elif file_count > 5:
            score += 15
        elif file_count > 2:
            score += 5

        # 3. Model Confidence (Max 30 points)
        # If confidence is low, risk is high
        confidence_penalty = int((1.0 - confidence) * 30)
        score += max(0, confidence_penalty)

        # 4. Keyword Detection (Bonus points up to 100 total)
        # We can't easily scan the full diff text here without the repo access, 
        # but if we have the manifest we can at least flag dangerous operations in commit messages
        # or triggered by specific file extensions.
        
        final_score = min(100, score)
        logger.info(f"Risk: Calculated total score of {final_score}/100")
        return final_score

    def scan_intent(self, intent: str) -> int:
        """
        Scans the user intent for high-risk requests before planning.
        """
        score = 0
        if any(re.search(word, intent.lower()) for word in self.DANGEROUS_KEYWORDS):
             score += 50
             logger.warning(f"Risk: Dangerous keyword detected in intent: {intent}")
        return score

risk_engine = RiskEngine()
