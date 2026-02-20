from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.coder import coder_node
from app.agents.nodes.tester import tester_node
from app.agents.nodes.manager import repo_prep_node, committer_node
from app.agents.nodes.orchestrator import strategy_node, scheduler_node, completion_check_node
from app.agents.nodes.react import react_node

def route_next_node(state: AgentState):
    """
    Priority B Orchestration Logic:
    Decides whether to continue to coder, exit, or loop.
    """
    status = state.get("status")
    
    if status == "all_tasks_scheduled":
         return "completion_checker"
    
    if status == "task_scheduled":
         return "coder"
         
    if status == "starting":
         return "repo_prep"
         
    if status == "workspace_ready":
         return "planner"
         
    if status == "planning_complete":
         return "strategy"
         
    if status == "strategy_selected":
         return "scheduler"
         
    if status == "changes_applied":
         return "tester"
         
    if status == "testing_failed":
         # In 10-step loop, failures trigger Coder again (Reflector logic is inside Tester)
         return "coder"

    if status == "testing_complete":
         return "committer"
         
    if status == "mission_success":
         return END
         
    return END

# Define Graph
workflow = StateGraph(AgentState)

# Add Nodes (Priority B 10-Step Components)
workflow.add_node("repo_prep", repo_prep_node)
workflow.add_node("planner", planner_node)
workflow.add_node("strategy", strategy_node)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("reasoner", react_node)
workflow.add_node("coder", coder_node)
workflow.add_node("tester", tester_node)
workflow.add_node("committer", committer_node)
workflow.add_node("completion_checker", completion_check_node)

# Priority B Orchestration Edges
workflow.set_entry_point("repo_prep")

workflow.add_edge("repo_prep", "planner")
workflow.add_edge("planner", "strategy")
workflow.add_edge("strategy", "scheduler")

# Scheduler Logic: Reasoner, Coder, or Completion Checker
def schedule_gate(state: AgentState):
    if state.get("status") != "task_scheduled":
        return "completion_checker"
    if state.get("strategy") == "react-mode":
        return "reasoner"
    return "coder"

workflow.add_conditional_edges(
    "scheduler",
    schedule_gate,
    {
        "coder": "coder",
        "reasoner": "reasoner",
        "completion_checker": "completion_checker"
    }
)

workflow.add_edge("reasoner", "coder")

workflow.add_edge("coder", "tester")

# Tester Logic: Retry Coder or proceed to Commit
workflow.add_conditional_edges(
    "tester",
    lambda s: "coder" if s.get("status") == "testing_failed" else "committer",
    {
        "coder": "coder",
        "committer": "committer"
    }
)

# Committer Logic: Loops back to Scheduler to see if more tasks remain
workflow.add_edge("committer", "scheduler")

# Completion Checker: End if success, else re-plan (Self-Correction)
workflow.add_conditional_edges(
    "completion_checker",
    lambda s: END if s.get("status") == "mission_success" else "planner",
    {
        "planner": "planner",
        END: END
    }
)

# Compile
agent_graph = workflow.compile()
