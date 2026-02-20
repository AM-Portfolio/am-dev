# Running the Dev Agent Product

This project is separated into two parts: infrastructure (Redis) and application (API, Worker, UI).
This separation allows you to keep persistent services running while restarting the application code frequently.

## Prerequisites

Ensure you are in the `dev-agent-product` directory:
```bash
cd dev-agent-product
```

## 1. Infrastructure (Redis)

The infrastructure services are defined in `infra/docker-compose.yml`.

### Start Infrastructure
This creates the shared network `agent_network` and starts Redis.
```bash
docker-compose -f infra/docker-compose.yml up -d
```

### Stop Infrastructure
```bash
docker-compose -f infra/docker-compose.yml down
```

## 2. Application (API, Worker, UI)

The application services are defined in the main `docker-compose.yml`.

### Build and Run Application
To build the images and start the services:
```bash
docker-compose up --build
```
Or to run in background:
```bash
docker-compose up -d --build
```

### Run Only (Without Rebuilding)
If you have already built the images:
```bash
docker-compose up
```

### Build Only
To just build the images without starting:
```bash
docker-compose build
```

### Stop Application
```bash
docker-compose down
```

## Full Workflow Example

1. Start Redis (do this once):
   ```bash
   docker-compose -f infra/docker-compose.yml up -d
   ```

2. Develop and run application (repeat as needed):
   ```bash
   # Run app (logs in terminal)
   docker-compose up
   ```

3. When finished:
   ```bash
   # Stop app
   docker-compose down
   
   # Stop infra (optional)
   docker-compose -f infra/docker-compose.yml down
   ```
