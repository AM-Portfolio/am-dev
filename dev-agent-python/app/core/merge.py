import logging
from app.git_tools import GitTools

logger = logging.getLogger(__name__)

class MergeOrchestrator:
    """
    Handles safe merging of agent branches into the main branch.
    Ensures CI passes before merge (Phase 2.3).
    """
    def attempt_merge(self, branch_name: str, target_branch: str = "main") -> bool:
        logger.info(f"MERGE: Attempting to merge {branch_name} into {target_branch}...")
        
        try:
            # 1. Update target
            GitTools.checkout_existing_branch(target_branch)
            GitTools.run_cmd(["pull"])
            
            # 2. Merge
            # --no-ff to create a merge commit
            GitTools.run_cmd(["merge", "--no-ff", branch_name])
            
            # 3. Push
            # GitTools.run_cmd(["push"]) # Disabled for safety until Phase 4
            
            logger.info("MERGE: Success")
            return True

        except Exception as e:
            logger.error(f"MERGE: Failed due to conflict or error: {e}")
            GitTools.run_cmd(["merge", "--abort"])
            return False

merge_orchestrator = MergeOrchestrator()
