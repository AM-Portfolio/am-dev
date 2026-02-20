import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)

class GitTools:
    """
    Git operations helper.
    """
    @staticmethod
    def run_cmd(cmd: List[str], cwd: str = ".") -> str:
        """Runs a git command in the specified directory."""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}. Error: {e.stderr}")
            raise RuntimeError(f"Git error: {e.stderr}")

    @classmethod
    def checkout_new_branch(cls, branch_name: str, cwd: str = ".") -> None:
        cls.run_cmd(["checkout", "-b", branch_name], cwd)

    @classmethod
    def checkout_existing_branch(cls, branch_name: str, cwd: str = ".") -> None:
        cls.run_cmd(["checkout", branch_name], cwd)

    @classmethod
    def commit(cls, message: str, cwd: str = ".") -> None:
        cls.run_cmd(["add", "."], cwd)
        cls.run_cmd(["commit", "-m", message], cwd)

    @classmethod
    def get_current_sha(cls, cwd: str = ".") -> str:
        return cls.run_cmd(["rev-parse", "HEAD"], cwd)

    @classmethod
    def reset_hard(cls, sha: str, cwd: str = ".") -> None:
        cls.run_cmd(["reset", "--hard", sha], cwd)

    @classmethod
    def log(cls, n: int = 5, cwd: str = ".") -> str:
        return cls.run_cmd(["log", f"-n {n}", "--oneline"], cwd)
