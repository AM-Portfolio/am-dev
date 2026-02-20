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
    original_branch: Optional[str]          # New: Track original branch for transactional merge
    error_class: Optional[str]              # New: Category for targeted repair (SYNTAX, DEP, etc)
    risk_score: Optional[int]               # New: Priority 2 risk assessment score
    task_graph: Optional[List[Dict]]        # New: Priority 3 DAG of tasks
    project_state: Optional[Dict]           # New: Priority 3 persistent memory
    strategy: Optional[str]                 # New: Priority A selected execution strategy
    reflection_hypothesis: Optional[str]    # New: Priority C repair logic
    next_recommended_action: Optional[str]  # New: Priority C repair logic
    current_task: Optional[Dict]            # New: Priority B current DAG node mapping
