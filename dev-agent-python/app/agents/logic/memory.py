from typing import List, Dict, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class ProjectState:
    """
    Persistent memory for long-horizon autonomous missions.
    """
    def __init__(self, workspace_path: str):
        self.path = os.path.join(workspace_path, ".agent_memory.json")
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load project memory: {e}")
        
        return {
            "stack_choice": None,
            "features_completed": [],
            "pending_tasks": [],
            "architecture_decisions": [],
            "last_success_hash": None,
            "mission_start_context": None
        }

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2)
            logger.debug(f"Project memory persisted to {self.path}")
        except Exception as e:
            logger.error(f"Failed to save project memory: {e}")

    def add_feature(self, name: str, summary: str):
        self.data["features_completed"].append({"name": name, "summary": summary})
        self.save()

    def add_decision(self, logic: str):
        self.data["architecture_decisions"].append(logic)
        self.save()

    def update_tasks(self, tasks: List[str]):
        self.data["pending_tasks"] = tasks
        self.save()

    def set_stack(self, stack: str):
        self.data["stack_choice"] = stack
        self.save()
