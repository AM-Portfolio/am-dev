import redis
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class LogStreamer:
    """
    Publishes log events to Redis for WebSocket consumption.
    """
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def publish_log(self, job_id: str, message: str, level: str = "INFO"):
        # Also log to standard Python logger for persistence
        if level == "ERROR":
            logger.error(f"[JOB {job_id}] {message}")
        elif level == "DEBUG":
            logger.debug(f"[JOB {job_id}] {message}")
        else:
            logger.info(f"[JOB {job_id}] {message}")

        channel = f"logs:{job_id}"
        payload = json.dumps({
            "job_id": job_id,
            "message": message,
            "level": level,
            "timestamp": "TODO" 
        })
        try:
            self.redis.publish(channel, payload)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")

log_streamer = LogStreamer()
