from app.agents.wrapper import codex
from app.agents.logic.token_monitor import token_monitor

logger = logging.getLogger(__name__)

class CompletionChecker:
    """
    Evaluates whether the mission's acceptance criteria are fully satisfied.
    """
    
    def check(self, state: Dict) -> Tuple[bool, str]:
        """
        Answers: 'Is the mission satisfied?'
        """
        job_id = state.get("job_id", "unknown")
        logger.info(f"VERIFICATION: Running Completion Check for job {job_id}...")
        
        prompt = (
            f"Context: You are a QA inspector evaluating an autonomous dev agent.\n"
            f"Mission: {state.get('user_input')}\n"
            f"Project State: {json.dumps(state.get('project_state', {}))}\n"
            f"Current Strategy: {state.get('strategy')}\n\n"
            f"GOAL: Determine if all architectural and functional goals are met.\n"
            f"Format your response as a JSON object:\n"
            f"AGENT_JSON_START: {{\"satisfied\": true/false, \"explanation\": \"...\"}}\n"
        )
        
        expected_schema = {
            "type": "object",
            "properties": {
                "satisfied": {"type": "boolean"},
                "explanation": {"type": "string"}
            },
            "required": ["satisfied", "explanation"]
        }
        
        # Call LLM for completion check
        stdout, stderr, code = codex.run_prompt(
            prompt, 
            expected_schema=expected_schema,
            approval="never"
        )
        
        # Track verification cost
        token_monitor.log_usage(job_id, len(prompt)//4, len(stdout)//4)
        
        if code == 0:
            import re
            json_match = re.search(r"AGENT_JSON_START:\s*(\{.*?\})", stdout, re.MULTILINE)
            if json_match:
                res = json.loads(json_match.group(1))
                return res["satisfied"], res["explanation"]
                
        return False, "Checker failed to produce a valid response."

completion_checker = CompletionChecker()
