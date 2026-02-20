import json
import os
import time
import asyncio
import logging
import argparse
from typing import List, Dict
from app.agents.logic.job_controller import job_controller
from app.agents.logic.token_monitor import token_monitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StressTestHarness:
    """
    Automates the execution of multiple autonomous missions and collects performance metrics.
    """
    
    DEFAULT_SUITES = {
        "smoke": [
            {"name": "Small Set-up", "mission": "Create a file named HELLO.md with 'World' inside.", "repo": "test_repo_1"},
            {"name": "Architecture Audit", "mission": "Identify all Python files and list their imports.", "repo": "test_repo_2"}
        ],
        "endurance": [
            {"name": "Auth Core", "mission": "Implement JWT authentication with login/register endpoints.", "repo": "prod_repo_auth"},
            {"name": "Migration", "mission": "Convert this Flask repository to use FastAPI.", "repo": "prod_repo_migration"}
        ]
    }

    def __init__(self, output_dir: str = "stress_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []

    async def run_mission(self, suite_name: str, config: Dict):
        logger.info(f"--- Running Mission: {config['name']} ---")
        start_time = time.time()
        
        # Start the job
        job_id = job_controller.start_job(config["mission"], repo_url=config["repo"])
        
        # Get the initial state
        job_info = job_controller.active_jobs[job_id]
        
        # Execute the real workflow
        try:
            await job_controller.execute_job(job_id, job_info["state"])
            final_job_info = job_controller.active_jobs[job_id]
            final_state = final_job_info["state"]
            
            duration = time.time() - start_time
            tokens_used = token_monitor.get_usage(job_id)
            
            result = {
                "suite": suite_name,
                "mission_name": config["name"],
                "job_id": job_id,
                "duration_s": round(duration, 2),
                "status": final_state.get("status", "unknown"),
                "tokens": tokens_used,
                "risk_score": final_state.get("risk_score", 0)
            }
            self.results.append(result)
            logger.info(f"✅ Mission {config['name']} finished in {duration:.2f}s with {tokens_used} tokens.")
        except Exception as e:
            logger.error(f"❌ Mission {config['name']} crashed: {e}")

    async def run_suite(self, suite_name: str):
        missions = self.DEFAULT_SUITES.get(suite_name, [])
        if not missions:
            logger.error(f"Suite '{suite_name}' not found.")
            return

        logger.info(f"🚀 Starting Stress-Test Suite: {suite_name} ({len(missions)} missions)")
        
        for mission_config in missions:
            await self.run_mission(suite_name, mission_config)

        self.generate_report(suite_name)

    def generate_report(self, suite_name: str):
        report_path = os.path.join(self.output_dir, f"report_{suite_name}_{int(time.time())}.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 Stress-Test Report generated: {report_path}")
        
        print("\n--- STRESS TEST SUMMARY ---")
        print("| Mission | Job ID | Duration | Tokens | Status |")
        print("| :--- | :--- | :--- | :--- | :--- |")
        for r in self.results:
            print(f"| {r['mission_name']} | {r['job_id']} | {r['duration_s']}s | {r['tokens']} | {r['status']} |")
        print("---------------------------\n")

async def main():
    parser = argparse.ArgumentParser(description="Autonomous Agent Stress-Test Harness")
    parser.add_argument("--suite", type=str, default="smoke", help="Suite to run: smoke, endurance")
    args = parser.parse_args()

    harness = StressTestHarness()
    await harness.run_suite(args.suite)

if __name__ == "__main__":
    asyncio.run(main())
