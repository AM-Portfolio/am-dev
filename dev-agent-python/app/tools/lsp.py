import subprocess
import logging
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class LSPTool:
    """
    Wraps Language Servers / Linters CLI to provide diagnostics.
    """
    def check_python(self, file_path: str) -> List[Dict]:
        """
        Runs pyright on a file.
        """
        try:
            # pyright file.py --outputjson
            result = subprocess.run(
                ["pyright", file_path, "--outputjson"],
                capture_output=True,
                text=True
            )
            data = json.loads(result.stdout)
            return data.get("generalDiagnostics", [])
        except FileNotFoundError:
            logger.warning("Pyright not found.")
            return []
        except Exception as e:
            logger.error(f"LSP Error: {e}")
            return []

    def check_typescript(self, file_path: str) -> List[str]:
        """
        Runs tsc (TypeScript Compiler) in check-only mode.
        """
        try:
            # tsc --noEmit file.ts
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", file_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return []
            return result.stdout.splitlines()
        except FileNotFoundError:
             logger.warning("TSC not found.")
             return []

lsp_tool = LSPTool()
