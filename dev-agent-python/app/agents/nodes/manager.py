from app.agents.state import AgentState
from app.core.stream import log_streamer
import git
import os
import shutil
import logging
import hashlib
import json
from app.agents.logic.memory import ProjectState
from app.agents.logic.risk_engine import risk_engine
from app.agents.logic.strategy_router import strategy_router
from app.agents.logic.manifest_writer import manifest_writer
from typing import Optional

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
            
    # Transactionality: Create an ephemeral branch for this job
    original_branch = None
    if os.path.exists(os.path.join(target_path, ".git")):
        try:
            repo = git.Repo(target_path)
            original_branch = repo.active_branch.name
            new_branch = f"job/{job_id}"
            
            # Create and checkout new branch
            log_streamer.publish_log(job_id, f"🌿 Branch: Creating ephemeral branch '{new_branch}'...", "DEBUG")
            repo.git.checkout("-b", new_branch)
        except Exception as e:
            logger.warning(f"Transactional branch creation failed: {e}")
    
    # Priority 3: Initialize Project Memory
    memory = ProjectState(target_path)
    log_streamer.publish_log(job_id, f"🧠 Memory: Loaded persistent state from {target_path}", "DEBUG")
    
    return {
        **state,
        "repo_path": target_path,
        "original_branch": original_branch,
        "project_state": memory.data,
        "status": "workspace_ready"
    }

async def committer_node(state: AgentState) -> AgentState:
    """
    Commits the changes made autonomously by the agent.
    """
    job_id = state.get("job_id", "unknown")
    repo_path = state.get("repo_path", "")
    
    if not repo_path or not os.path.exists(repo_path):
        error_msg = f"Cannot commit: Repository path {repo_path} does not exist."
        log_streamer.publish_log(job_id, f"❌ {error_msg}", "ERROR")
        return {**state, "status": "commit_failed", "error": error_msg}
        
    logger.info("COMMITTER: Committing autonomous changes...")
    log_streamer.publish_log(job_id, "💾 Committer: Committing changes left by agent...", "INFO")

    # Commit Changes (if it's a git repo)
    if os.path.exists(os.path.join(repo_path, ".git")):
        try:
            repo = git.Repo(repo_path)
            original_branch = state.get("original_branch")
            has_errors = bool(state.get("test_errors"))
            
            # Add all modified and untracked files
            repo.git.add(A=True)
            
            # Check if there's anything to commit
            if not repo.is_dirty() and not repo.untracked_files:
                log_streamer.publish_log(job_id, "⚠️ No changes detected by git.", "WARN")
                if original_branch:
                     repo.git.checkout(original_branch)
                return {**state, "status": "no_changes"}
            
            commit_message = f"feat: Autonomous agent implementation for Job {job_id}\n\nTask: {state.get('user_input')}"
            commit = repo.index.commit(commit_message)
            log_streamer.publish_log(job_id, f"✅ Committed changes to ephemeral branch: {commit.hexsha[:7]}", "SUCCESS")

            # Priority F: Cryptographic Auditing (Observability)
            # Find modified files from the coder's output (already in state)
            files_modified = state.get("files_modified", []) # Need to ensure coder sets this
            manifest = manifest_writer.generate_manifest(state, files_modified)
            manifest_writer.save_manifest(repo_path, manifest)
            log_streamer.publish_log(job_id, f"📝 Audit: Generated MANIFEST.json ({len(manifest['files'])} files hashed)", "DEBUG")

            # Priority A: Strategy Routing (Brain Upgrade)
            # We use risk, confidence (default 1.0 for now), and current state
            risk_score = risk_engine.calculate_score(manifest)
            strategy = strategy_router.route(risk_score, 1.0, state)
            
            log_streamer.publish_log(job_id, f"⚖️ Decision: Strategy '{strategy}' selected (Risk: {risk_score}/100)", "INFO")

            # Transactional Merge/Rollback
            if original_branch:
                if not has_errors:
                    if strategy == "human-escalation":
                        log_streamer.publish_log(job_id, "⚠️ CRITICAL RISK: Merging blocked. Escalating for manual review.", "WARN")
                        return {**state, "status": "waiting_for_approval", "risk_score": risk_score, "strategy": strategy, "manifest": manifest}
                    
                    if strategy in ["pr-only", "test-first", "react-mode"]:
                        log_streamer.publish_log(job_id, f"ℹ️ Mode '{strategy}': Mission flagged for PR review only.", "INFO")
                        # For now we simulate non-direct modes by not merging
                        return {**state, "status": "waiting_for_approval", "risk_score": risk_score, "strategy": strategy, "manifest": manifest}

                    log_streamer.publish_log(job_id, f"🔄 Merging '{repo.active_branch.name}' into '{original_branch}'...", "INFO")
            # Priority 3: Update Persistent Memory
            current_task = state.get("current_task")
            if current_task and not has_errors:
                memory = ProjectState(repo_path)
                if "features_completed" not in memory.data:
                    memory.data["features_completed"] = []
                
                # Check if already recorded
                completed_ids = [f["id"] for f in memory.data["features_completed"]]
                if current_task["id"] not in completed_ids:
                    memory.data["features_completed"].append({
                        "id": current_task["id"],
                        "name": current_task["name"],
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                    memory.save()
                    log_streamer.publish_log(job_id, f"🧠 Memory: Task '{current_task['name']}' recorded as completed.", "DEBUG")

            return {**state, "status": "changes_applied", "risk_score": risk_score, "strategy": strategy, "project_state": memory.data}
            
        except Exception as e:
            log_streamer.publish_log(job_id, f"⚠️ Git transaction failed: {e}", "WARN")
            
    return {
        **state,
        "status": "changes_applied"
    }
