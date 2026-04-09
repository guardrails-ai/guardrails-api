# Guardrails API

A FastAPI server that hosts [Guardrails AI](https://github.com/guardrails-ai/guardrails) in your own environment, providing OpenAI-compatible endpoints for applying guards to LLM interactions.

## Installation

**Requirements:** Python 3.10–3.13

```bash
pip install guardrails-api
```

For development:

```bash
git clone https://github.com/guardrails-ai/guardrails-api.git
cd guardrails-api
pip install -e ".[dev]"
```

## Quick Start

### 1. Install Guardrails Hub validators

```bash
guardrails hub install hub://guardrails/detect_pii
```

### 2. Set up your guards

**Option A — Config file (in-memory, no database required)**

Create a `config.py` that defines your guards:

```python
from guardrails import Guard
from guardrails.hub import DetectPII

guard = Guard(name="pii-guard")
guard.use(DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER"]))
```

Add any additional server settings to your `.env` file:

```bash
PORT=8000
GUARDRAILS_LOG_LEVEL=INFO
```

Guards are loaded at startup and the API is read-only. Suitable for local development and static deployments.

**Option B — PostgreSQL (persistent, full CRUD)**

Add database credentials to your `.env` file using individual variables:

```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=guardrails
PGUSER=postgres
PGPASSWORD=password
```

Or a single connection URL:

```bash
DB_URL=postgresql://postgres:password@localhost:5432/guardrails
```

When a database is configured, schema migrations run automatically on startup and guards can be created, updated, and deleted via the API.

### 3. Start the server

```bash
guardrails-api start --env .env
```

The server will be available at `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health-check`

## CLI Reference

### `guardrails-api start`

Start the API server.

```
guardrails-api start [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--env` | `.env` | Path to environment file |
| `--config` | `""` | Path to config file defining guards |
| `--port` | `8000` | Port to listen on |
| `--middleware` | `""` | Path to middleware file |
| `--env-override` | `False` | Override existing env vars with values from `--env` |

**Examples:**

```bash
# Basic startup
guardrails-api start

# Custom port and config
guardrails-api start --port 9000 --config ./my_guards.py

# Custom env file with override
guardrails-api start --env ./production.env --env-override
```

### `guardrails-api db upgrade`

Upgrade the database schema (PostgreSQL only).

```
guardrails-api db upgrade [REVISION] [OPTIONS]
```

| Argument/Option | Default | Description |
|-----------------|---------|-------------|
| `revision` | `head` | Target revision |
| `--env` | `.env` | Path to environment file |
| `--env-override` | `False` | Override existing env vars |

```bash
guardrails-api db upgrade
guardrails-api db upgrade abc123ef
```

### `guardrails-api db downgrade`

Downgrade the database schema (PostgreSQL only).

```
guardrails-api db downgrade [REVISION] [OPTIONS]
```

| Argument/Option | Default | Description |
|-----------------|---------|-------------|
| `revision` | `-1` | Target revision (use `-1` to roll back one step) |
| `--env` | `.env` | Path to environment file |
| `--env-override` | `False` | Override existing env vars |

```bash
guardrails-api db downgrade
guardrails-api db downgrade -2
```

### `guardrails-api --version`

Print the installed version.

```bash
guardrails-api --version
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HOST` | `http://localhost` | Host address |
| `GUARDRAILS_LOG_LEVEL` | `INFO` | Log level for Guardrails |
| `LOGLEVEL` | `INFO` | Application log level |
| `GUARDRAILS_API_KEY` | — | API key for authenticating requests |
| `APP_ENVIRONMENT` | `local` | Deployment environment label |

### PostgreSQL (optional)

By default the server uses in-memory storage. To enable persistence, set database connection variables:

```bash
# Individual variables
PGHOST=localhost
PGPORT=5432
PGDATABASE=guardrails
PGUSER=postgres
PGPASSWORD=password

# Or a full connection URL
DB_URL=postgresql://postgres:password@localhost:5432/guardrails

# Optional connection extras
DB_EXTRAS=?sslmode=verify-ca
PG_POOL_SIZE=5
PG_POOL_MAX_OVERFLOW=10
PG_POOL_TIMEOUT=30
```

When `PGHOST` (or `DB_URL`) is set, the server will automatically run schema migrations on startup and enable full CRUD operations on guards via the API.

### Custom Middleware

Pass a middleware file to register custom Starlette middleware:

```python
# middleware.py
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # add custom auth logic here
        return await call_next(request)
```

```bash
guardrails-api start --middleware middleware.py
```

## Running in Production

For production, run directly with uvicorn or gunicorn:

```bash
# uvicorn
uvicorn --factory 'guardrails_api.app:create_app' --host 0.0.0.0 --port 8000 --workers 4

# gunicorn
gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 "guardrails_api.app:create_app()"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health-check` | Server health status |
| `GET` | `/guards` | List all guards |
| `POST` | `/guards` | Create a guard (requires PostgreSQL) |
| `GET` | `/guards/{guard_name}` | Get a guard by name |
| `PUT` | `/guards/{guard_name}` | Update a guard (requires PostgreSQL) |
| `DELETE` | `/guards/{guard_name}` | Delete a guard (requires PostgreSQL) |
| `POST` | `/guards/{guard_name}/validate` | Run validation against a guard |
| `POST` | `/guards/{guard_name}/openai/v1/chat/completions` | OpenAI ChatCompletion compatiable endpoint for guarded LLM interactions. |

## Storage Modes

**In-memory (default):** Guards are loaded from `config.py` at startup. The API is read-only — guards cannot be created or updated via the API.

**PostgreSQL:** Full CRUD via the API. Guards defined in `config.py` are seeded on startup. Schema migrations run automatically.
