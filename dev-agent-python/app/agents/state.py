from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    Represents the internal state of the agent workflow.
    """
    job_id: str
    user_input: str
    
    # Context
    repo_path: Optional[str]                # New: Path to the target repository or folder
    repo_url: Optional[str]                 # New: GitHub URL (if cloning is needed)

    # Artifacts
    plan: Optional[str]
    architecture_guidelines: Optional[str]  # New: Architecture design
    implementation_steps: List[str]
    code_diffs: List[str]
    file_actions: Optional[List[dict]]      # New: Structured actions for filesystem changes
    test_results: Optional[str]
    test_errors: Optional[str]              # New: For feedback loop
    review_feedback: Optional[str]
    
    # Metadata
    status: str
    error: Optional[str]
    attempts: int
    retry_count: int                        # New: Loop counter
