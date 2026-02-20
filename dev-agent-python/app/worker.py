from celery import Celery
from app.core.config import settings
from app.core.logging_config import setup_logging
from opentelemetry.instrumentation.celery import CeleryInstrumentor

# Configure logging early (persists worker logs to file)
setup_logging(log_file="agent_worker.log")

celery_app = Celery(
    "dev_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "agent_queue"}
}

# Auto-instrumentation (Phase 3.4)
CeleryInstrumentor().instrument()
