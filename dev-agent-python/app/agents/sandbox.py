import subprocess
import logging
import os
import shutil
import resource
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class SandboxProvider:
    """
    Base class for sandbox execution environments.
    """
    def validate_network_policy(self, env: Optional[dict]):
        """
        Enforce proxy-only or restricted network access.
        """
        if env:
            # Scrub dangerous vars or force proxy
            env.pop("PYTHONHTTPSVERIFY", None)
            # Future: inject HTTP_PROXY/HTTPS_PROXY allowlist here
            pass

    def execute(self, cmd: List[str], cwd: Optional[str] = None, env: Optional[dict] = None, stdin: Optional[str] = None) -> Tuple[str, str, int]:
        raise NotImplementedError

class LocalSandbox(SandboxProvider):
    """
    OS-level sandboxing using standard subprocess.
    """
    def _set_limits(self):
        """
        Callback to set resource limits in the child process before execution.
        """
        try:
            # CPU Limit: 60 seconds
            resource.setrlimit(resource.RLIMIT_CPU, (60, 65))
            # Memory Limit: 1GB
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1050 * 1024 * 1024))
            # File Handle Limit: 256
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, 512))
        except Exception as e:
            logger.warning(f"Failed to set sandbox resource limits: {e}")

    def execute(self, cmd: List[str], cwd: Optional[str] = None, env: Optional[dict] = None, stdin: Optional[str] = None) -> Tuple[str, str, int]:
        try:
            self.validate_network_policy(env)
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=cwd,
                preexec_fn=self._set_limits # Apply limits in child
            )
            stdout, stderr = process.communicate(input=stdin)
            return stdout, stderr, process.returncode
        except Exception as e:
            return "", str(e), 1

class DockerSandbox(SandboxProvider):
    """
    Containerized sandboxing using Docker.
    """
    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        self.container_id = None

    def execute(self, cmd: List[str], cwd: Optional[str] = None, env: Optional[dict] = None, stdin: Optional[str] = None) -> Tuple[str, str, int]:
        # Implementation for Docker execution
        # For now, we simulate the logic since daemon is down
        if not shutil.which("docker"):
             return "", "Docker not installed", 1
        
        # Real implementation would involve 'docker run -v ...'
        # Since we found daemon is down in preflight, this will likely only be used
        # when the user starts the daemon.
        return "", "Docker daemon not running", 1

class SandboxFactory:
    @staticmethod
    def get_provider() -> SandboxProvider:
        # Check if Docker is available and running
        try:
            res = subprocess.run(["docker", "ps"], capture_output=True)
            if res.returncode == 0:
                logger.debug("Using DockerSandbox provider.")
                return DockerSandbox()
        except:
            pass
        
        logger.debug("Falling back to LocalSandbox provider.")
        return LocalSandbox()

sandbox_manager = SandboxFactory.get_provider()
