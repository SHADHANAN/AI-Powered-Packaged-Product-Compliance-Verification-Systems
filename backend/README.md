# AI-Powered Packaged Product Compliance Verification System - Backend

Production-oriented FastAPI backend foundation for verifying packaged product regulatory compliance.

---

## Overview (Phase 1)

Phase 1 provides the foundational architecture for the backend application:
- Modular, scalable architecture organized by layer (`api`, `services`, `schemas`, `models`, `utils`).
- Configuration management using `pydantic-settings` and `.env` environment variables.
- Configurable Cross-Origin Resource Sharing (CORS) support.
- Centralized structured application logging.
- Global exception handling returning consistent and secure JSON responses.
- Interactive OpenAPI / Swagger UI (`/docs`) and ReDoc (`/redoc`) API documentation.
- Automated testing setup with `pytest` and `fastapi.testclient.TestClient`.

---

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & lifecycle
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── api/
│   │   ├── __init__.py          # API router aggregation
│   │   └── health.py            # Health check endpoint router
│   ├── services/
│   │   └── __init__.py          # Business logic services placeholder
│   ├── schemas/
│   │   ├── __init__.py          # Pydantic schemas index
│   │   ├── common.py            # Common response & error schemas
│   │   └── health.py            # Health check schemas
│   ├── models/
│   │   └── __init__.py          # Database models placeholder
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py        # Custom exceptions & global handlers
│       └── logging.py           # Structured application logging
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and TestClient setup
│   └── test_health.py           # Unit and integration test suite
├── requirements.txt             # Project dependencies
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

---

## Prerequisites

- **Python**: Version 3.10 or higher
- **pip**: Package installer for Python

---

## Environment Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

### Configuration Options

| Variable | Description | Default |
| :--- | :--- | :--- |
| `APP_NAME` | Name of the application | `AI-Powered Packaged Product Compliance Verification System` |
| `APP_VERSION` | Current backend version | `1.0.0` |
| `APP_DESCRIPTION` | API description displayed in docs | `Production-oriented API backend for...` |
| `ENVIRONMENT` | Environment name (`development`, `production`, `testing`) | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `API_PREFIX` | Base prefix for all API routes | `/api` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` |
| `HOST` | Host address to bind the server | `0.0.0.0` |
| `PORT` | Port number to bind the server | `8000` |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using python module runner:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Available Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root endpoint identifying service status and API version |
| `GET` | `/api/health` | Health-check endpoint returning service health status |
| `GET` | `/docs` | Interactive Swagger UI API documentation |
| `GET` | `/redoc` | Interactive ReDoc API documentation |
| `GET` | `/api/openapi.json` | OpenAPI 3.1 specification schema |

### Sample Responses

#### `GET /api/health`
```json
{
  "status": "healthy",
  "service": "product-compliance-backend"
}
```

#### `GET /`
```json
{
  "message": "AI-Powered Packaged Product Compliance Verification System is running",
  "app_name": "AI-Powered Packaged Product Compliance Verification System",
  "version": "1.0.0",
  "environment": "development",
  "docs_url": "/docs"
}
```

---

## Running Automated Tests

Run the test suite using `pytest`:

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```
