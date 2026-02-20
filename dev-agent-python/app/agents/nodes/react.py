from app.agents.state import AgentState
from app.agents.wrapper import codex
from app.core.stream import log_streamer
from app.agents.logic.react_guard import react_guard
from app.agents.logic.token_monitor import token_monitor
import logging

logger = logging.getLogger(__name__)

async def react_node(state: AgentState) -> AgentState:
    """
    Implements a ReAct (Reason-Act-Observe) loop for complex missions.
    The node uses the Codex CLI to gather information BEFORE choosing an implementation.
    """
    job_id = state.get("job_id", "unknown")
    repo_path = state.get("repo_path")
    strategy = state.get("strategy")
    
    if strategy != "react-mode":
        return state

    log_streamer.publish_log(job_id, "🧠 ReAct Mode: Dynamic Tool-Use Reasoning initiated.", "INFO")
    
    # Internal ReAct Loop
    observations = []
    
    # max_steps is now managed by react_guard
    while True:
        log_streamer.publish_log(job_id, f"🤔 ReAct: Thinking about the next step...", "DEBUG")
        
        prompt = (
            f"You are the Greater God Reasoner. You are solving: {state['user_input']}\n"
            f"Current Strategy: {strategy}\n"
            f"Previous Observations: {json.dumps(observations)}\n\n"
            f"GOAL: Use tools (ls, grep, cat, find) to understand the codebase. \n"
            f"Format your response as a JSON object:\n"
            f"AGENT_JSON_START: {{\"thought\": \"your reasoning\", \"action\": \"command_to_run\", \"is_final\": false}}\n"
            f"If you have enough info to implement, set \"is_final\": true and provide your final hypothesis summary in \"thought\"."
        )
        
        # Reasoning Step (Read-Only)
        stdout, stderr, code = codex.run_prompt(
            prompt, 
            sandbox="read-only",
            approval="never",
            cwd=repo_path
        )
        
        # Track reasoning cost
        token_monitor.log_usage(job_id, len(prompt)//4, len(stdout)//4)
        
        if code == 0:
            import re
            json_match = re.search(r"AGENT_JSON_START:\s*(\{.*?\})", stdout, re.MULTILINE)
            if json_match:
                res = json.loads(json_match.group(1))
                thought = res.get("thought", "")
                action = res.get("action", "")
                is_final = res.get("is_final", False)
                
                log_streamer.publish_log(job_id, f"💭 Thought: {thought}", "DEBUG")
                
                if is_final:
                    log_streamer.publish_log(job_id, "🎯 ReAct: Reasoning complete.", "SUCCESS")
                    react_guard.reset_task(job_id, "reasoning")
                    return {**state, "reflection_hypothesis": thought, "status": "reasoning_complete"}
                
                if action:
                    # Governance: Guard against loops and over-reasoning
                    if not react_guard.track_action(job_id, "reasoning", action):
                        log_streamer.publish_log(job_id, "🛑 ReAct: Logic gate active. Fallback to implementation.", "WARN")
                        break
                        
                    log_streamer.publish_log(job_id, f"🛠️ Act: Running `{action}`", "INFO")
                    
                    # Execution Step (The "Act")
                    act_stdout, act_stderr, act_code = codex.run_command(
                        action,
                        sandbox="read-only",
                        cwd=repo_path
                    )
                    
                    observations.append({
                        "action": action, 
                        "observation": act_stdout if act_code == 0 else f"Error: {act_stderr}"
                    })
        else:
            log_streamer.publish_log(job_id, "⚠️ ReAct: Prompt failed. Falling back.", "WARN")
            break
            
        if not token_monitor.is_within_budget(job_id):
            log_streamer.publish_log(job_id, "🛑 ReAct: Budget exceeded. Terminating reasoning.", "ERROR")
            break
        
    return {**state, "status": "reasoning_incomplete"}
