import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SecretsSanitizer:
    """
    Scrubs sensitive data from autonomous agent logs and outputs.
    """
    
    PATTERNS = [
        r"(?i)api[-_]?key\s*[:=]\s*['\"]?[a-zA-Z0-9]{32,128}['\"]?",
        r"(?i)bearer\s+[a-zA-Z0-9\._\-]{64,}",
        r"(?i)secret\s*[:=]\s*['\"]?[a-zA-Z0-9]{32,128}['\"]?",
        r"(?i)password\s*[:=]\s*['\"]?[^ \n\r]{8,}['\"]?",
        r"(?i)sk-[a-zA-Z0-9]{20,}", # OpenAI keys
        r"(?i)ghp_[a-zA-Z0-9]{36,}" # GitHub tokens
    ]

    def sanitize(self, text: str) -> str:
        """
        Replaces sensitive patterns with [REDACTED].
        """
        if not text:
            return text
            
        sanitized = text
        for pattern in self.PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)
            
        return sanitized

sanitizer = SecretsSanitizer()
