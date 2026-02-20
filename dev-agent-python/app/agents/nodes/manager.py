from app.agents.state import AgentState
from app.core.stream import log_streamer
import git
import os
import shutil
import logging

logger = logging.getLogger(__name__)

async def repo_prep_node(state: AgentState) -> AgentState:
    """
    Ensures the target repository is cloned or ready for modification.
    """
    job_id = state.get("job_id", "unknown")
    repo_url = (state.get("repo_url") or "").strip()
    
    # Use a default path if not specified
    target_path = state.get("repo_path") or f"workspace/{job_id}"
    
    logger.info(f"REPO: Preparing workspace at {target_path}...")
    log_streamer.publish_log(job_id, f"📁 Repo: Preparing workspace at {target_path}...", "INFO")
    
    os.makedirs(target_path, exist_ok=True)
    
    if repo_url and not os.path.exists(os.path.join(target_path, ".git")):
        try:
            log_streamer.publish_log(job_id, f"⬇️ Cloning {repo_url}...", "INFO")
            git.Repo.clone_from(repo_url, target_path)
            log_streamer.publish_log(job_id, "✅ Repository cloned successfully.", "SUCCESS")
        except Exception as e:
            error_msg = f"Failed to clone repository: {str(e)}"
            log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
            # Fallback: Just use the empty folder
            pass
            
    # Checkout a new branch for changes? (Future feature)
    
    return {
        **state,
        "repo_path": target_path,
        "status": "workspace_ready"
    }

async def committer_node(state: AgentState) -> AgentState:
    """
    Applies changes to the filesystem and commits them.
    """
    job_id = state.get("job_id", "unknown")
    repo_path = state.get("repo_path", "")
    file_actions = state.get("file_actions", [])
    
    if not repo_path or not os.path.exists(repo_path):
        error_msg = f"Cannot commit: Repository path {repo_path} does not exist."
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "commit_failed", "error": error_msg}
        
    logger.info("COMMITTER: Applying changes to filesystem...")
    log_streamer.publish_log(job_id, "💾 Committer: Applying changes to filesystem...", "INFO")
    
    modified_files = []
    
    # 1. Apply Files
    for action in file_actions:
        # Expected format: {"path": "src/main.py", "content": "..."}
        rel_path = action.get("path")
        content = action.get("content")
        
        if rel_path and content:
            full_path = os.path.join(repo_path, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            modified_files.append(rel_path)
            log_streamer.publish_log(job_id, f"📝 Updated {rel_path}", "DEBUG")

    if not modified_files:
        log_streamer.publish_log(job_id, "⚠️ No files were modified.", "WARN")
        return {**state, "status": "no_changes"}

    # 2. Commit Changes (if it's a git repo)
    if os.path.exists(os.path.join(repo_path, ".git")):
        try:
            repo = git.Repo(repo_path)
            repo.index.add(modified_files)
            
            commit_message = f"feat: Implemented changes for Job {job_id}\n\nTask: {state.get('user_input')}"
            commit = repo.index.commit(commit_message)
            
            log_streamer.publish_log(job_id, f"✅ Committed changes: {commit.hexsha[:7]}", "SUCCESS")
        except Exception as e:
            log_streamer.publish_log(job_id, f"⚠️ Git commit failed (files are saved though): {e}", "WARN")
            
    return {
        **state,
        "status": "changes_applied"
    }
