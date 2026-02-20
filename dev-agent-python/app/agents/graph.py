from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.architect import architect_node
from app.agents.nodes.coder import coder_node
from app.agents.nodes.tester import tester_node
from app.agents.nodes.reviewer import reviewer_node
from app.agents.nodes.manager import repo_prep_node, committer_node

def should_retry(state: AgentState):
    """
    Decides whether to loop back to coding or proceed to review.
    """
    if state.get("test_errors") and state.get("retry_count", 0) < 3:
        return "coder"
    return "committer"

# Define Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("repo_prep", repo_prep_node)
workflow.add_node("planner", planner_node)
workflow.add_node("architect", architect_node)
workflow.add_node("coder", coder_node)
workflow.add_node("tester", tester_node)
workflow.add_node("committer", committer_node)
workflow.add_node("reviewer", reviewer_node)

# Add Edges
workflow.set_entry_point("repo_prep")
workflow.add_edge("repo_prep", "planner")
workflow.add_edge("planner", "architect")
workflow.add_edge("architect", "coder")
workflow.add_edge("coder", "tester")

# Conditional Loop
workflow.add_conditional_edges(
    "tester",
    should_retry,
    {
        "coder": "coder",
        "committer": "committer"
    }
)

workflow.add_edge("committer", "reviewer")
workflow.add_edge("reviewer", END)

# Compile (Checkpointer will be injected at runtime in tasks.py)
agent_graph = workflow.compile()
