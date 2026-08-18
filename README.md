# Job Queue API

🌐 **Languages:** English | [Português](README.pt.md)

🔗 **Live demo:** https://job-queue-api-wcex.onrender.com/

FastAPI API for registering jobs in PostgreSQL and processing them through a Python worker. The main flow is:

- the API receives a payload and saves a record in `jobs`;
- the worker queries jobs in `pending` status;
- the worker updates the status to `running` and then to `done` or `failed`;
- the API allows checking the history and the final result of each job.

## Features

- Creating jobs via REST API;
- Individual lookup by ID;
- Listing with filtering by status and limit;
- Asynchronous worker loop to process the queue;
- PostgreSQL database in a container via Docker Compose;
- Ready-to-run environment with `docker compose up --build`.

## Project structure

- `app/main.py`: initializes the FastAPI application;
- `app/routers/health.py`: API healthcheck;
- `app/routers/jobs.py`: endpoints for creating, querying, and listing jobs;
- `app/database.py`: PostgreSQL connection using environment variables;
- `worker.py`: process that handles pending jobs;
- `sql/create_tables.sql`: initial database schema;
- `entrypoint.py`: supervisor process that starts the API and worker together in the same container (used in production/deployment);
- `docker-compose.yml`: orchestration for PostgreSQL and the API (worker embedded via `entrypoint.py`);
- `Dockerfile`: application image.

## Requirements

- Docker
- Docker Compose
- Python 3.11+ for local execution (optional)

## Environment configuration

Create a `.env` file in the project root with the variables below:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=jobqueue
DB_USER=postgres
DB_PASSWORD=1234
```

These variables are used by both the API and the worker. PostgreSQL exposes port `5433` on the host machine to avoid conflicts with other local instances.

## Running with Docker Compose

From the project root, run:

```bash
docker compose up --build
```

This command starts the services:

- `db`: PostgreSQL with automatic schema initialization from `sql/create_tables.sql`;
- `api`: FastAPI application, which also starts the worker internally via `entrypoint.py`.

**Important:** Before testing the endpoints, an API key must be inserted into the database. See the detailed instructions in the **Authentication flow** section below.

### Useful URLs

- API: http://localhost:8000
- Healthcheck: http://localhost:8000/health/
- PostgreSQL: localhost:5433

To stop everything:

```bash
docker compose down
```

If you also want to remove the database volume:

```bash
docker compose down -v
```

## Running locally (without Docker)

Create and activate the virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

In Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal, start the worker:

```bash
python worker.py
```

## Endpoints

### Root

The root endpoint redirects to the Swagger docs at `/docs`.

```bash
curl -L http://localhost:8000/
```

### Healthcheck

```bash
curl http://localhost:8000/health/
```

### Create job

```bash
curl -X POST http://localhost:8000/jobs/ \
  -H "Content-Type: application/json" \
  -H "x-api-key: MINHA_API_KEY" \
  -d '{"payload": {"teste": true, "valor": 123}}'
```

Expected response from FastAPI:

```json
{
  "job_id": 1,
  "status": "pending"
}
```

### Get a job by ID

```bash
curl http://localhost:8000/jobs/1
```

### List jobs

```bash
curl "http://localhost:8000/jobs/?status=pending&limit=10"
```

## Authentication and processing flow

1. The client sends the `x-api-key` in the header.
2. The `get_current_client` dependency validates the key against `clients.api_key`.
3. The route uses the authenticated `client_id` to register the job.
4. The worker selects pending jobs.
5. The record is set to `running`.
6. The processing executes the job logic.
7. The record ends as `done` or `failed`.

This prevents any client from sending an arbitrary `client_id` in the body and creating jobs on behalf of another client.

Before calling protected endpoints, make sure the `clients` table contains at least one client row with a valid API key, for example:

```sql
INSERT INTO clients (name, api_key, rpm_limit)
VALUES ('demo', 'MINHA_API_KEY', 1000);
```

Without this, requests will return `401` because the authentication dependency checks `clients.api_key` before creating a job.

## Notes

- The project does not use RabbitMQ, Celery, or any other external queue; the queue is implemented in PostgreSQL.
- The worker polls the database in a loop and processes the available jobs.
- The `sql/create_tables.sql` file is mounted in the PostgreSQL container and executed automatically on startup.
