import re
from typing import Dict, Optional, Tuple

class UniversalErrorParser:
    """
    Parses stack traces to identify the exact file and line number of an error.
    Supports: Python, Node.js, Java, Go, Rust.
    """
    PATTERNS = {
        "python": r'File "([^"]+)", line (\d+)',
        "node": r'at .* \(([^:]+):(\d+):(\d+)\)',
        "java": r'at .*\((\w+\.java):(\d+)\)',
        "go": r'\s+([^:]+):(\d+)',
        "rust": r'--> ([^:]+):(\d+):(\d+)'
    }

    @staticmethod
    def parse(traceback: str, language: str = "python") -> Optional[Tuple[str, int]]:
        """
        Parses the traceback and returns (file_path, line_number).
        """
        pattern = UniversalErrorParser.PATTERNS.get(language.lower())
        if not pattern:
            return None

        # Determine regex flags
        flags = re.MULTILINE
        
        matches = re.finditer(pattern, traceback, flags)
        
        # Usually we want the *last* match for the most relevant user code frame
        # (especially in Python where the top frame is the entry point)
        # But specifically for Python, the *last* frame is usually the error location.
        # For Node, the first frame is often the error.
        
        results = [m for m in matches]
        if not results:
            return None

        last_match = results[-1]
        
        if language == "python":
            return last_match.group(1), int(last_match.group(2))
        elif language == "node":
            return last_match.group(1), int(last_match.group(2))
        elif language == "java":
            # Java trace provides Class.java, need to heuristic path finding?
            return last_match.group(1), int(last_match.group(2))
            
        return results[0].group(1), int(results[0].group(2))

error_parser = UniversalErrorParser()
