import subprocess
import shlex
import logging
import os
from typing import Tuple, Optional, Callable
from app.core.config import settings

logger = logging.getLogger(__name__)

class CodexConnector:
    """
    Wrapper around the 'codex' CLI tool.
    Ensures safe execution via subprocess and proper error handling.
    """
    def __init__(self, cli_path: str = settings.CODEX_CLI_PATH, timeout: int = 300):
        import os
        if not os.path.isabs(cli_path):
             self.cli_path = os.path.abspath(cli_path)
        else:
             self.cli_path = cli_path
        self.timeout = timeout

    def run_prompt(self, prompt: str, model: str = settings.CODEX_MODEL, log_callback: Optional[Callable[[str], None]] = None) -> Tuple[str, str, int]:
        """
        Runs a prompt against the Codex CLI.
        Falls back to direct Azure OpenAI API call if CLI is missing.
        Returns: (stdout, stderr, exit_code)
        """
        # Check if CLI exists (fast check to avoid exception overhead if known missing)
        import shutil
        if not shutil.which(self.cli_path) and not os.path.exists(self.cli_path):
             return self._run_api_fallback(prompt, model)

        # Use 'exec' subcommand for non-interactive mode
        # Pass prompt via stdin for robustness
        # Skip git checks since we are running via wrapper
        # Explicitly configure Azure provider
        cmd = [
            self.cli_path, "exec", 
            "--skip-git-repo-check", 
            "--model", model, 
            "-c", "model_provider=azure",
            "-c", "model_providers.azure.name=\"Azure OpenAI\"",
            "-c", f"model_providers.azure.base_url=\"{settings.AZURE_OPENAI_ENDPOINT}\"",
            "-c", "model_providers.azure.env_key=AZURE_OPENAI_API_KEY",
            "-c", "model_providers.azure.wire_api=\"responses\"",
            "--sandbox", "read-only",
            "-"
        ]
        # configured to read this specific environment variable name.
        env = os.environ.copy()
        env["AZURE_OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY
        # Force unbuffered output for Python subprocesses (if codex is python)
        env["PYTHONUNBUFFERED"] = "1"

        stdout_lines = []
        stderr_lines = [] # We merge stderr into stdout for streaming, but keep separate if possible? No, merging is safer.

        try:
            logger.info(f"Running Codex command: {' '.join(cmd)} ...") 
            
            # Using Popen for streaming output
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr for simpler unified streaming
                text=True,
                encoding='utf-8', # Fix: Force UTF-8 encoding for Windows
                env=env,
                bufsize=1  # Line buffered
            )
            
            # Write prompt to stdin
            if process.stdin:
                try:
                    # Ensure prompt ends with newline just in case the CLI tool expects it
                    if not prompt.endswith("\n"):
                        prompt += "\n"
                    process.stdin.write(prompt)
                    process.stdin.flush() # Explicit flush
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass # Process might have exited early

            # Read output line by line
            if process.stdout:
                # Use a while loop with explicit readline to ensure we don't buffer excessively
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        stdout_lines.append(line)
                        if log_callback:
                            # Send immediately without buffering
                            log_callback(line.rstrip())
                            # Force a small sleep to yield if loop is too tight? No, this is blocking IO.
            
            process.wait(timeout=self.timeout)
            
            full_output = "".join(stdout_lines)
            
            # Extract code blocks if present to separate from logs
            # Simple heuristic: if we find a code block, try to extract it?
            # Or just return everything and let the node handle it.
            # But the user sees the raw log file.
            
            return full_output, "", process.returncode

        except subprocess.TimeoutExpired:
            logger.error(f"Codex CLI timed out after {self.timeout}s")
            if process:
                process.kill()
            return "".join(stdout_lines), "TimeoutExpired", 124
        except FileNotFoundError:
            # Fallback if shutil.which failed to detect absence or path issues
            return self._run_api_fallback(prompt, model)
        except Exception as e:
            logger.exception("Unexpected error running Codex CLI")
            return "", str(e), 1

    def _run_api_fallback(self, prompt: str, model: str) -> Tuple[str, str, int]:
        """
        Direct API call to Azure OpenAI when CLI is not available.
        """
        import requests
        
        if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
            return "", "Azure OpenAI credentials not configured.", 1

        # Construct URL
        # URL format: https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version={api-version}
        
        endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        
        # Standardize base URL by removing known suffixes that might be pasted in by users
        # e.g. .../openai/v1 -> .../openai
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        
        # Ensure we don't double up on /openai/deployments if the user just gave the resource root
        if "/openai" not in endpoint:
             endpoint = f"{endpoint}/openai"

        # Now endpoint should be .../openai
        
        # But wait, if user provided .../openai/v1, stripping /v1 gives .../openai.
        # Then we want .../openai/deployments/...
        
        # However, if user provided .../openai/, stripping /v1 (if not present) leaves .../openai.
        
        # Safe construction:
        # If the endpoint already has /deployments, assume it's a full URL and don't touch it (rare/custom proxy).
        if "/deployments" in endpoint:
             # Just append chat/completions if not present? Too risky.
             # Let's assume standard Azure resource URL structure.
             pass
             
        # Let's simply handle the common case: user provided .../openai/v1
        base_url = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3] # Remove /v1
            
        # If it still ends in /openai, great. If not (resource root), add /openai?
        # Actually Azure endpoints are usually .../openai/deployments/...
        
        # Robust fix:
        if base_url.endswith("/openai"):
             pass # Correct
        elif "/openai" not in base_url:
             base_url = f"{base_url}/openai"
             
        # If base_url is .../openai, then append /deployments/...
        
        # Determine if Chat or Completion model based on name (heuristic)
        # GPT-5 Codex models are actually Chat Com-letion models despite the name
        is_chat_model = True 
        
        operation = "chat/completions" if is_chat_model else "completions"
        if is_chat_model:
             # Ensure we don't have double /chat/completions if the user already provided it in base_url (rare but possible)
             pass

        url = f"{base_url}/deployments/{model}/{operation}?api-version={settings.AZURE_OPENAI_API_VERSION}"
        
        headers = {
            "api-key": settings.AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        if is_chat_model:
            # Chat Completion payload
            payload = {
                "messages": [{"role": "user", "content": prompt}]
            }
            # Remove unsupported params for reasoning models if necessary
            # payload["max_tokens"] = 2000 
            # payload["temperature"] = 0.7
        else:
            # Legacy Completion payload (for Codex models)
            payload = {
                "prompt": prompt,
                "max_tokens": 2000,
                "temperature": 0.7
            }
        
        try:
            logger.info(f"Calling Azure OpenAI API ({operation}): {model} at {base_url}...")
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if is_chat_model:
                    content = data["choices"][0]["message"]["content"]
                else:
                    content = data["choices"][0]["text"]
                return content, "", 0
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return "", error_msg, 1
                
        except Exception as e:
            logger.exception("Azure OpenAI API Connection Failed")
            return "", str(e), 1

codex = CodexConnector()
