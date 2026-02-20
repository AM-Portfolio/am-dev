# Local Development Guide

This guide provides the commands to run the **Python Backend (API & Worker)** and the **Flutter Frontend (UI)** locally, without using Docker for the application code.

**Note:** You still need a running Redis instance. You can run it via Docker or install it locally.

## Prerequisites

1.  **Python 3.10+**: Ensure `python` and `pip` are installed.
2.  **Flutter SDK**: Ensure `flutter` is locally installed and in your PATH.
3.  **Redis**:
    *   **Option A (Docker)**: Run `docker-compose -f infra/docker-compose.yml up -d`
    *   **Option B (Local)**: Install Redis on Windows (e.g., via Memurai or WSL) running on `localhost:6379`.

---

## 1. Python Backend (API & Worker)

Open a terminal in: `dev-agent-product/dev-agent-python`

### Clean Build & Run (First Time or After Updates)
*Installs dependencies, sets environment variables, and starts the API server.*

```powershell
cd "dev-agent-python"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Set environment variables (PowerShell)
$env:REDIS_URL="redis://localhost:6379/0"; $env:API_KEY="godmode-v1"; $env:OPENAI_API_KEY="your-key-here"
# Run API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Only (API)
*Assumes dependencies are installed.*

```powershell
cd "dev-agent-python"
.\venv\Scripts\Activate.ps1
$env:REDIS_URL="redis://localhost:6379/0"; $env:API_KEY="godmode-v1"; $env:OPENAI_API_KEY="your-key-here"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Worker (Background Tasks)
*Open a **NEW** terminal. Required for processing agent tasks.*

```powershell
cd "dev-agent-python"
.\venv\Scripts\Activate.ps1
$env:REDIS_URL="redis://localhost:6379/0"; $env:API_KEY="godmode-v1"; $env:OPENAI_API_KEY="your-key-here"
# Run Celery Worker (Pool: solo is better for Windows dev)
celery -A app.worker worker --loglevel=info --pool=solo -Q agent_queue
```

---

## 2. Flutter Frontend (UI)

Open a terminal in: `dev-agent-product/dev-agent-ui`

### Clean Build & Run
*Cleans cache, installs dependencies, and launches the app.*

```powershell
cd "dev-agent-ui"
flutter clean
flutter pub get
flutter run -d chrome
```

### Run Only
*Launches the app immediately.*

```powershell
cd "dev-agent-ui"
flutter run -d chrome
```

---

## 3. Run Everything Together

You will need **3 separate terminals**.
**Ensure all terminals are started at the root directory:** `C:\Users\MKU257\Kairos Repos\BCM`

**Terminal 1: Infrastructure (Redis)**
```powershell
cd "dev-agent-product"
docker-compose -f infra/docker-compose.yml up -d
```

**Terminal 2: Python API + Worker**
*(Combined for simplicity. ONLY run this if you have already run the "Clean Build & Run" step above to create the venv)*
```powershell
cd "dev-agent-product/dev-agent-python"
# IF VENV MISSING: python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
.\venv\Scripts\Activate.ps1
$env:REDIS_URL="redis://localhost:6379/0"; 
Start-Process -NoNewWindow -FilePath "celery" -ArgumentList "-A app.worker worker --loglevel=info --pool=solo -Q agent_queue"
uvicorn app.main:app --reload --port 8000
```

**Terminal 3: Flutter UI**
```powershell
cd "dev-agent-product/dev-agent-ui"
flutter run -d chrome
```
