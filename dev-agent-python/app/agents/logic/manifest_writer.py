from typing import Dict, List
from app.agents.logic.token_monitor import token_monitor

logger = logging.getLogger(__name__)

class ManifestWriter:
    """
    Handles the generation and storage of mission manifests and artifacts.
    """
    
    def generate_manifest(self, state: Dict, files_modified: List[str]) -> Dict:
        """
        Creates a SHA-256 audit trail for the current job state and files.
        """
        job_id = state.get("job_id", "unknown")
        repo_path = state.get("repo_path", "")
        
        manifest = {
            "job_id": job_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mission": state.get("user_input"),
            "strategy": state.get("strategy"),
            "risk_score": state.get("risk_score"),
            "files": []
        }
        
        if repo_path and os.path.exists(repo_path):
            for file_rel_path in files_modified:
                full_path = os.path.join(repo_path, file_rel_path)
                if os.path.exists(full_path):
                    with open(full_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    manifest["files"].append({
                        "path": file_rel_path,
                        "sha256": file_hash
                    })
        
        # Add sustainability metrics
        manifest["metrics"] = {
            "latency_ms": 0, # TODO: Track timing
            "retry_count": state.get("retry_count", 0),
            "tokens": token_monitor.get_usage(job_id),
            "success": state.get("status") == "mission_success"
        }
        
        return manifest

    def save_manifest(self, repo_path: str, manifest: Dict):
        """
        Writes the MANIFEST.json to the repository root.
        """
        if not repo_path or not os.path.exists(repo_path):
            return
            
        manifest_path = os.path.join(repo_path, "MANIFEST.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"MANIFEST: Saved audit trail to {manifest_path}")
        except Exception as e:
            logger.error(f"MANIFEST: Failed to save manifest: {e}")

manifest_writer = ManifestWriter()
