# AI-Powered Packaged Product Compliance Verification System - Backend

Production-ready FastAPI backend for automated packaged product Legal Metrology regulatory compliance verification.

---

## 1. System Architecture

```text
                               +----------------------------------------+
                               |     Client Application (React/Next)     |
                               +----------------------------------------+
                                                   |
                                                   | HTTPS + Bearer JWT
                                                   v
+---------------------------------------------------------------------------------------------------+
| FastAPI Backend Gateway                                                                           |
|                                                                                                   |
|  [Security Headers Middleware]   [CORS Middleware]   [Global Exception & Disclosure Handlers]     |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | Authentication & Authorization Layer                                                        |  |
|  |  * JWT Bearer Verification (`get_current_user`) -> 401 Unauthorized                         |  |
|  |  * Role-Based Access Control (`require_admin`, `require_inspector`, `require_viewer`) -> 403|  |
|  |  * Resource-Level Ownership Validation (`verify_verification_ownership`) -> 403             |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | Image Upload & Sanitization Pipeline                                                        |  |
|  |  * MIME & Extension Validation (JPEG, PNG, WebP)                                            |  |
|  |  * Deep Binary Inspection (Pillow `Image.verify()`)                                          |  |
|  |  * UUID Filename Sanitization & Path Traversal Defenses                                    |  |
|  |  * Atomic Rollback & File Cleanup on Failure                                                |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | OCR & Field Extraction Engine                                                               |  |
|  |  * Deterministic Grayscale & Contrast Preprocessing                                         |  |
|  |  * Tesseract OCR Text Recognition                                                           |  |
|  |  * Legal Metrology Regex Heuristic Pattern Extraction                                       |  |
|  |  * Structured `ExtractedField` Persistence                                                  |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | Legal Metrology Compliance Rule Engine (12 Rules)                                           |  |
|  |  * MRP, Net Qty, Units, Mfr, Importer, Origin, Batch, Mfg/Import Dates, Consumer Care, Name   |  |
|  |  * Severity-Weighted Scoring (0-100%)                                                       |  |
|  |  * Structured `ComplianceCheck` Persistence & Actionable Recommendations                    |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | Report Generation & Publication-Grade PDF Export                                            |  |
|  |  * Structured JSON Report Serialization                                                      |  |
|  |  * ReportLab Platypus Two-Pass PDF Generation (`NumberedCanvas`)                            |  |
|  |  * High-Contrast & Grayscale-Safe Badges, Headers/Footers, Dynamic Page Count                 |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | Immutable Chronological Audit Trail                                                         |  |
|  |  * Lifecycle Events: UPLOADED -> OCR -> EXTRACTED -> CHECKED -> REPORT -> PDF_EXPORTED      |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |    PostgreSQL Database (SQLAlchemy 2)  |
                               +----------------------------------------+
```

---

## 2. Directory & Package Structure

```text
backend/
├── alembic/                      # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_initial_models.py
│       ├── 0002_create_compliance_models.py
│       └── 0003_create_audit_logs.py
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic environment configuration & production validators
│   ├── database.py               # SQLAlchemy engine & session factory
│   ├── main.py                   # FastAPI application factory & middleware setup
│   ├── api/                      # Routing & dependency injection layer
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication routes (login, me)
│   │   ├── authorization.py      # RBAC & ownership dependencies
│   │   ├── dependencies.py       # JWT extraction dependency
│   │   ├── health.py             # Health & DB readiness check routes
│   │   ├── users.py              # User management routes
│   │   ├── products.py           # Product catalog routes
│   │   ├── verifications.py      # Verification pipeline routes
│   │   ├── extracted_fields.py   # Extracted field CRUD routes
│   │   ├── compliance_checks.py  # Compliance check CRUD routes
│   │   └── reports.py            # Report metadata CRUD routes
│   ├── models/                   # SQLAlchemy 2.x ORM models
│   │   ├── __init__.py
│   │   ├── base.py               # Declarative base & UUID mixins
│   │   ├── enums.py              # UserRole, VerificationStatus, ComplianceStatus, AuditAction
│   │   ├── user.py               # User account model
│   │   ├── product.py            # Packaged product model
│   │   ├── verification.py       # Verification inspection run model
│   │   ├── extracted_field.py    # OCR extracted field model
│   │   ├── compliance_check.py   # Rule evaluation check model
│   │   ├── report.py             # Export document model
│   │   └── audit_log.py          # Verification audit trail model
│   ├── schemas/                  # Pydantic validation & response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── health.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── verification.py
│   │   ├── extracted_field.py
│   │   ├── compliance_check.py
│   │   ├── report.py
│   │   └── audit_log.py
│   ├── services/                 # Business logic & operational processing
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── image_service.py
│   │   ├── ocr_service.py
│   │   ├── field_extraction_service.py
│   │   ├── verification_pipeline_service.py
│   │   ├── compliance_rules.py
│   │   ├── compliance_engine.py
│   │   ├── report_service.py
│   │   ├── pdf_report_service.py
│   │   ├── audit_service.py
│   │   └── user_service.py
│   └── utils/                    # Shared security, logging & validation helpers
│       ├── __init__.py
│       ├── security.py           # Argon2id hashing & JWT encode/decode
│       ├── file_validation.py    # Binary verification & path sanitization
│       ├── image_processing.py   # Grayscale contrast preprocessing
│       ├── compliance_validators.py
│       ├── exceptions.py         # AppException hierarchy & response handlers
│       └── logging.py            # Structured logging configuration
├── tests/                        # 155+ comprehensive automated tests
│   ├── conftest.py
│   ├── test_api_security.py
│   ├── test_audit_log.py
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_compliance_api.py
│   ├── test_compliance_engine.py
│   ├── test_compliance_rules.py
│   ├── test_crud_integration.py
│   ├── test_database.py
│   ├── test_e2e_pipeline.py
│   ├── test_edge_cases.py
│   ├── test_field_extraction.py
│   ├── test_health.py
│   ├── test_image_upload.py
│   ├── test_models.py
│   ├── test_ocr_service.py
│   ├── test_pdf_report.py
│   ├── test_report_generation.py
│   ├── test_routers.py
│   ├── test_security.py
│   ├── test_services.py
│   └── test_verification_pipeline.py
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## 3. Role-Based Access Control (RBAC) & Ownership

| Role | Hierarchy Level | Permissions |
|---|---|---|
| **`ADMIN`** | System Administrator | Full system oversight. Can view/manage all users, products, verifications, compliance checks, reports, and audit logs. |
| **`INSPECTOR`** | Legal Metrology Inspector | Can upload product images, run OCR processing, trigger compliance evaluations, generate reports, and export PDFs for assigned verifications. Blocked from other inspectors' verifications (`403 Forbidden`). |
| **`VIEWER`** | Read-Only Oversight User | Can view authorized verification reports, compliance summaries, and audit logs. Blocked from mutation/pipeline endpoints (`403 Forbidden`). |

### 401 Unauthorized vs 403 Forbidden
- **`401 Unauthorized`**: Token missing, expired, invalid signature, malformed, or account inactive.
- **`403 Forbidden`**: Valid authenticated user with insufficient permissions or cross-inspector access attempt.

---

## 4. Complete API Endpoint Catalog & Contract

### Authentication
- `POST /api/auth/login`
  - **Auth**: None
  - **Body**: `{"email": "inspector@metrology.gov.in", "password": "Pass123!"}`
  - **Response**: `200 OK` -> `{"access_token": "...", "token_type": "bearer", "user": {...}}`
- `GET /api/auth/me`
  - **Auth**: Bearer JWT
  - **Response**: `200 OK` -> `UserRead`

### Verification Pipeline
- `POST /api/verifications/upload`
  - **Auth**: Bearer JWT (`INSPECTOR` or `ADMIN`)
  - **Content-Type**: `multipart/form-data` (`file`: image binary, `product_id`: optional UUID)
  - **Response**: `201 Created` -> `VerificationRead` (status: `pending`)
- `POST /api/verifications/{id}/process`
  - **Auth**: Bearer JWT (`INSPECTOR` or `ADMIN`, Ownership verified)
  - **Response**: `200 OK` -> `VerificationRead` (status: `completed`)
- `GET /api/verifications/{id}/fields`
  - **Auth**: Bearer JWT (Ownership verified)
  - **Response**: `200 OK` -> `List[ExtractedFieldRead]`
- `POST /api/verifications/{id}/compliance`
  - **Auth**: Bearer JWT (`INSPECTOR` or `ADMIN`, Ownership verified)
  - **Response**: `200 OK` -> `ComplianceSummaryRead` (score: 0-100%, rule checks, violations, recommendations)
- `GET /api/verifications/{id}/compliance`
  - **Auth**: Bearer JWT (Ownership verified)
  - **Response**: `200 OK` -> `ComplianceSummaryRead`
- `POST /api/verifications/{id}/report`
  - **Auth**: Bearer JWT (`INSPECTOR` or `ADMIN`, Ownership verified)
  - **Response**: `200 OK` -> `ComplianceReportData` (structured metadata, summary, checks, violations)
- `GET /api/verifications/{id}/report`
  - **Auth**: Bearer JWT (Ownership verified)
  - **Response**: `200 OK` -> `ComplianceReportData`
- `GET /api/verifications/{id}/report/pdf`
  - **Auth**: Bearer JWT (Ownership verified)
  - **Response**: `200 OK` (`application/pdf`, attachment)
- `GET /api/verifications/{id}/audit-logs`
  - **Auth**: Bearer JWT (Ownership verified)
  - **Response**: `200 OK` -> `List[AuditLogRead]` (chronological audit history)

### Generic Catalog & System Management
- `POST /api/users`, `GET /api/users`, `GET /api/users/{id}`, `DELETE /api/users/{id}`
- `POST /api/products`, `GET /api/products`, `GET /api/products/{id}`, `DELETE /api/products/{id}`
- `POST /api/verifications`, `GET /api/verifications`, `GET /api/verifications/{id}`, `DELETE /api/verifications/{id}`
- `POST /api/extracted-fields`, `GET /api/extracted-fields`, `GET /api/extracted-fields/{id}`, `DELETE /api/extracted-fields/{id}`
- `POST /api/compliance-checks`, `GET /api/compliance-checks`, `GET /api/compliance-checks/{id}`, `DELETE /api/compliance-checks/{id}`
- `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{id}`, `DELETE /api/reports/{id}`
- `GET /api/health`, `GET /api/health/db`

---

## 5. Local Setup & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- PostgreSQL 14+
- Tesseract OCR (Optional: system gracefully falls back if not installed)

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Apply Database Migrations
```bash
alembic upgrade head
```

### 4. Run Automated Test Suite (155 tests)
```bash
pytest -v
```

### 5. Start Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger UI Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

---

## 6. Production Deployment Checklist

1. [x] **Environment Mode**: Set `ENVIRONMENT=production` in production environment.
2. [x] **Secret Keys**: Configure `JWT_SECRET_KEY` with a cryptographically secure random string ($\ge 32$ chars). Default keys are automatically rejected on startup.
3. [x] **CORS Configuration**: Restrict `CORS_ORIGINS` strictly to authorized frontend domains. Wildcard `*` is automatically rejected in production mode.
4. [x] **Database Driver**: Use production connection pool with PostgreSQL (`postgresql+psycopg://`).
5. [x] **Upload Directory**: Mount persistent storage for `UPLOAD_DIR` outside public web server roots.
6. [x] **Security Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `X-XSS-Protection` are enabled globally.
7. [x] **Information Disclosure**: SQL statements, connection credentials, server absolute paths, and Python tracebacks are filtered from API responses.
8. [ ] **Rate Limiting**: Configure reverse proxy (Nginx / Cloudflare / Ingress) or API Gateway with rate limits on `/api/auth/login` (5/min), `/api/verifications/upload` (10/min), and `/api/verifications/{id}/report/pdf` (15/min).
9. [ ] **TLS / HTTPS**: Terminate TLS at the ingress or reverse proxy layer.
