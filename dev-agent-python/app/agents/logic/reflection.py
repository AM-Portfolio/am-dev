from app.agents.wrapper import codex
from app.agents.logic.token_monitor import token_monitor

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """
    Analyzes task outcomes and generates strategic hypotheses for the next action.
    """
    
    def reflect(self, state: Dict, observation: str) -> Tuple[str, str]:
        """
        Ingests state and logs to produce (hypothesis, next_action).
        """
        job_id = state.get("job_id", "unknown")
        logger.info(f"REFLECTION: Ingesting observation for job {job_id}...")
        
        prompt = (
            f"Context: You are an autonomous agent reflecting on a task failure.\n"
            f"Mission: {state.get('user_input')}\n"
            f"Current Plan: {state.get('plan')}\n"
            f"Observation (Error/Logs): {observation}\n\n"
            f"GOAL: Analyze why it failed and propose a fix.\n"
            f"Format your response as a JSON object:\n"
            f"AGENT_JSON_START: {{\"hypothesis\": \"...\", \"next_action\": \"...\"}}\n"
        )
        
        expected_schema = {
            "type": "object",
            "properties": {
                "hypothesis": {"type": "string"},
                "next_action": {"type": "string"}
            },
            "required": ["hypothesis", "next_action"]
        }
        
        # Call LLM for reflection
        stdout, stderr, code = codex.run_prompt(
            prompt, 
            expected_schema=expected_schema,
            approval="never"
        )
        
        # Track reflection cost
        token_monitor.log_usage(job_id, len(prompt)//4, len(stdout)//4)
        
        if code == 0:
            import re
            json_match = re.search(r"AGENT_JSON_START:\s*(\{.*?\})", stdout, re.MULTILINE)
            if json_match:
                res = json.loads(json_match.group(1))
                return res["hypothesis"], res["next_action"]
                
        return "Unknown failure cause", "Retry original strategy with caution"

reflection_engine = ReflectionEngine()
