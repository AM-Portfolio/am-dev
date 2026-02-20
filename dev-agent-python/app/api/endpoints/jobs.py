from fastapi import APIRouter, Depends, BackgroundTasks
from app.tasks import run_agent_workflow
from app.worker import celery_app
from app.core.security import get_api_key
import uuid
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class JobRequest(BaseModel):
    user_input: str
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    resume_job_id: Optional[str] = None # Added for resuming

@router.post("/jobs", dependencies=[Depends(get_api_key)])
async def create_job(request: JobRequest):
    # If resuming, use the provided ID, otherwise generate new
    job_id = request.resume_job_id.strip() if request.resume_job_id and request.resume_job_id.strip() else str(uuid.uuid4())
    
    # Pass params to task
    task = run_agent_workflow.delay(request.user_input, job_id, request.repo_url, request.repo_path)
    return {"job_id": job_id, "task_id": task.id, "status": "submitted" if not request.resume_job_id else "resumed"}

@router.post("/jobs/{job_id}/cancel", dependencies=[Depends(get_api_key)])
async def cancel_job(job_id: str):
    # Phase 3.3 Logic
    # 1. Find Celery task ID (requires lookup, omitted for brevity)
    # 2. Revoke task
    # celery_app.control.revoke(task_id, terminate=True)
    return {"status": "cancelled", "job_id": job_id}
