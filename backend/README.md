# AI-Powered Packaged Product Compliance Verification System - Backend

Production-oriented FastAPI backend foundation for verifying packaged product regulatory compliance.

---

## Overview

- **Phase 1 (Foundation)**: Modular structure, Pydantic settings, structured logging, global exception handling, OpenAPI & ReDoc documentation.
- **Phase 2 (Database Foundation)**: PostgreSQL integration with SQLAlchemy 2.x, psycopg driver, Alembic migrations, connection health checks, and Docker Compose PostgreSQL service.

---

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & lifecycle
│   ├── config.py                # Pydantic Settings & environment variables (DATABASE_URL)
│   ├── database.py              # SQLAlchemy 2.x engine, SessionLocal, get_db, connection check
│   ├── api/
│   │   ├── __init__.py          # API router aggregation
│   │   └── health.py            # Health check & DB health endpoints
│   ├── services/
│   │   └── __init__.py          # Business logic services placeholder
│   ├── schemas/
│   │   ├── __init__.py          # Pydantic schemas index
│   │   ├── common.py            # Common response & error schemas
│   │   └── health.py            # Service & database health schemas
│   ├── models/
│   │   ├── __init__.py          # Database models package index
│   │   └── base.py              # SQLAlchemy DeclarativeBase
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py        # Custom exceptions & global handlers
│       └── logging.py           # Structured application logging
├── alembic/
│   ├── versions/
│   │   └── 0001_initial_schema.py # Initial baseline migration
│   ├── env.py                  # Alembic runtime environment (dynamic DB URL & Base)
│   ├── script.py.mako          # Migration template
│   └── README
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and TestClient setup
│   ├── test_database.py         # Database, Engine, Session, & Alembic tests
│   └── test_health.py           # Health endpoints and API tests
├── alembic.ini                  # Alembic migration configuration
├── requirements.txt             # Project dependencies
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

---

## Prerequisites

- **Python**: Version 3.10+ (tested with Python 3.12)
- **PostgreSQL**: Version 14+ (or Docker Desktop)
- **pip**: Python package installer

---

## Environment Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

### Configuration Options

| Variable | Description | Default |
| :--- | :--- | :--- |
| `APP_NAME` | Name of the application | `AI-Powered Packaged Product Compliance Verification System` |
| `APP_VERSION` | Current backend version | `1.0.0` |
| `ENVIRONMENT` | Environment mode (`development`, `production`, `testing`) | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `API_PREFIX` | Base prefix for API routes | `/api` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/product_compliance` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:3000,http://localhost:5173` |
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## Running PostgreSQL with Docker

To run the local PostgreSQL database using Docker Compose from the project root:

```bash
docker compose up -d postgres
```

To stop PostgreSQL:
```bash
docker compose down
```

---

## Database Migrations (Alembic)

Alembic is configured to dynamically read `DATABASE_URL` from the application settings without hardcoding credentials in `alembic.ini`.

From the `backend/` directory:

- **Apply all migrations to head**:
  ```bash
  alembic upgrade head
  ```

- **Check current database revision**:
  ```bash
  alembic current
  ```

- **Roll back the previous migration**:
  ```bash
  alembic downgrade -1
  ```

- **Generate SQL without connecting to database (Offline mode)**:
  ```bash
  alembic upgrade head --sql
  ```

- **Create a new auto-generated migration (for future phases)**:
  ```bash
  alembic revision --autogenerate -m "create_users_table"
  ```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Available Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Service root identification |
| `GET` | `/api/health` | Service health status (Phase 1 contract) |
| `GET` | `/api/health/db` | Database connectivity health check |
| `GET` | `/docs` | Interactive Swagger UI API documentation |
| `GET` | `/redoc` | Interactive ReDoc API documentation |
| `GET` | `/api/openapi.json` | OpenAPI specification schema |

---

## Running Automated Tests

Run the complete test suite:

```bash
pytest -v
```
