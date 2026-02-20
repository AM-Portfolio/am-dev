from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import jobs, stream
from app.core.logging_config import setup_logging
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure API logging
setup_logging(log_file="agent_api.log")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
# Allow all origins for local development to fix WebSocket connection issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(jobs.router, prefix=settings.API_V1_STR, tags=["jobs"])
app.include_router(stream.router, tags=["stream"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

# OpenTelemetry (Phase 3.4)
FastAPIInstrumentor.instrument_app(app)
