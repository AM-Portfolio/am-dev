import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class ErrorClass:
    SYNTAX = "SYNTAX_ERROR"
    DEPENDENCY = "DEPENDENCY_MISSING"
    TYPE = "TYPE_ERROR"
    SEMANTIC = "SEMANTIC_FAILURE"
    SECURITY = "SECURITY_VIOLATION"
    UNKNOWN = "UNKNOWN_FAILURE"

class ErrorClassifier:
    """
    Automated root-cause classification for code execution failures.
    """
    
    PATTERNS = {
        ErrorClass.SYNTAX: [
            r"SyntaxError:",
            r"IndentationError:",
            r"TabError:",
            r"expected '.*'",
            r"invalid syntax"
        ],
        ErrorClass.DEPENDENCY: [
            r"ModuleNotFoundError:",
            r"ImportError:",
            r"No module named",
            r"cannot import name"
        ],
        ErrorClass.TYPE: [
            r"TypeError:",
            r"AttributeError:",
            r"mypy reported type issues"
        ],
        ErrorClass.SECURITY: [
            r"Operation not permitted",
            r"PermissionError:",
            r"sandbox-exec: sandbox_apply",
            r"bandit detected issues"
        ]
    }

    def classify(self, stderr: str) -> str:
        """
        Classifies a raw traceback or error message into a high-level error class.
        """
        if not stderr:
            return ErrorClass.UNKNOWN

        for error_class, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    logger.info(f"Classified error as {error_class} based on pattern: {pattern}")
                    return error_class
        
        # If we have stderr but no pattern matches, it's likely a logic/semantic failure
        if "assertionfailed" in stderr.lower().replace(" ", "") or "failed:" in stderr.lower():
            return ErrorClass.SEMANTIC
            
        return ErrorClass.UNKNOWN

classifier = ErrorClassifier()
