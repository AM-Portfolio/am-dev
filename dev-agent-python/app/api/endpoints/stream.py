from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
import redis.asyncio as redis
import asyncio

router = APIRouter()

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    # Connect to Redis (Async)
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"logs:{job_id}")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
        await r.close()
