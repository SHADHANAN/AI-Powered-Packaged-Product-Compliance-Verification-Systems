# AI-Powered Packaged Product Compliance Verification System - Backend

Production-oriented FastAPI backend for automated packaged product Legal Metrology regulatory compliance verification.

---

## Architecture Overview

- **Phase 1 (Foundation)**: Modular structure, Pydantic settings, structured logging, global exception handling, OpenAPI & ReDoc documentation.
- **Phase 2 (Database Foundation)**: PostgreSQL integration with SQLAlchemy 2.x, psycopg driver, Alembic migrations, connection health checks.
- **Phase 3 (Database Models)**: Comprehensive SQLAlchemy 2.x typed models, constraints, relationships, indexes, Pydantic schemas, and Alembic migrations.
- **Phase 4 (CRUD Services & API Routers)**: Clean service layer with repository/service pattern, thin routers, transactional rollback, cascade deletion handling.
- **Phase 5 (Security & JWT Auth)**: Argon2id password hashing, JWT Bearer authentication (`POST /api/auth/login`, `GET /api/auth/me`), `get_current_user` dependency.
- **Phase 6 (Image Upload Pipeline)**: Authenticated multi-format product image upload, binary validation, path-traversal prevention, atomic file rollback, and verification record creation.
- **Phase 7 (OCR & Field Extraction Pipeline)**: Deterministic image preprocessing with Pillow, pluggable Tesseract OCR extraction with graceful local fallback, Legal Metrology regex extraction heuristics, and persistent `ExtractedField` storage.
- **Phase 8 (Compliance Rule Engine)**: Deterministic Legal Metrology rule evaluation engine, severity weighting, automated score calculation (0-100%), violation/recommendation generation, and persistent `ComplianceCheck` storage.
- **Phase 9 Step 1 (Compliance Reports & Audit Trail)**: Audit-ready structured compliance report generation, idempotency handling, and comprehensive chronological verification audit logging.
- **Phase 9 Step 2 (PDF Compliance Report Export)**: Publication-grade PDF document rendering using ReportLab Platypus, dynamic two-pass page numbering, running headers/footers, grayscale readability, streaming download endpoint, and zero credential leakage.
- **Phase 9 Step 3 (Authorization, API Hardening & Production Readiness)**: Resource-level authorization, role-based access control (RBAC), security headers middleware, CORS origin validation, JWT verification hardening, error disclosure defenses, and production configuration validation.

---

## API Security & Authorization Model

```text
Client
  ↓
HTTP Security Headers Middleware (X-Frame-Options, X-Content-Type-Options, etc.)
  ↓
CORS Origin Filtering (Strict in production, local in dev)
  ↓
JWT Authentication (get_current_user) -> 401 on missing/invalid/expired/inactive
  ↓
Role Authorization (require_roles / require_inspector / require_admin) -> 403 on insufficient role
  ↓
Resource Authorization (verify_verification_ownership) -> 403 on cross-inspector access
  ↓
Input & File Binary Validation (Pillow verification, UUID naming, size limits)
  ↓
Service Layer (Transactional rollback, sanitization)
  ↓
Database / OCR / Compliance / Reports / PDF Export
```

### User Roles & Permissions
- **`ADMIN` (`admin`)**: Complete system-wide administrative oversight. Can manage users, products, all verifications, compliance checks, reports, and audit logs.
- **`INSPECTOR` (`inspector`)**: Authorized inspection personnel. Can upload product labels, trigger OCR processing, evaluate Legal Metrology compliance rules, generate reports, and export PDFs for assigned verifications.
- **`VIEWER` (`viewer`)**: Read-only oversight user. Can view authorized verification reports, compliance summaries, and audit logs. Cannot upload images, run pipeline processing, or trigger evaluations.

### Resource Ownership Rules
- **Inspector Isolation**: An `INSPECTOR` can only inspect, process, evaluate, report on, and view audit trails for verifications assigned to them (or unassigned). Attempting to access another inspector's verification UUID returns `HTTP 403 Forbidden`.
- **Admin Oversight**: An `ADMIN` has overarching permissions across all verifications.
- **Viewer Access**: `VIEWER` users can only read authorized verification data and are blocked from pipeline mutation endpoints (`HTTP 403 Forbidden`).

### 401 Unauthorized vs 403 Forbidden Consistency
- **`HTTP 401 Unauthorized`**:
  - Missing `Authorization: Bearer <token>` header.
  - Expired, malformed, or signature-tampered JWT.
  - Inactive user account (`is_active == False`).
  - Non-existent user associated with token.
- **`HTTP 403 Forbidden`**:
  - Authenticated user with insufficient role (e.g. `VIEWER` attempting image upload or rule evaluation).
  - Authenticated user attempting to access/modify a verification or user account owned by someone else.

---

## Security Hardening & Defenses

### 1. HTTP Security Headers
All API responses automatically include:
- `X-Content-Type-Options: nosniff` (Prevents MIME-type sniffing attacks)
- `X-Frame-Options: DENY` (Prevents clickjacking)
- `Referrer-Policy: no-referrer` (Prevents credential/path leaking in referrer headers)
- `X-XSS-Protection: 1; mode=block` (Enforces legacy browser XSS filters)

### 2. CORS Hardening
- Configurable via `CORS_ORIGINS` environment variable (comma-separated list or array).
- In `production` environment, wildcard `*` is strictly rejected by Pydantic model validation.

### 3. JWT Hardening
- Enforces HMAC algorithms (`HS256`, `HS384`, `HS512`).
- Requires `exp`, `sub`, and `role` claims.
- Never stores passwords, hashes, database strings, or internal secrets in JWT claims.

### 4. File Upload Security
- Strict extension and MIME whitelist (`.jpg`, `.jpeg`, `.png`, `.webp` / `image/jpeg`, `image/png`, `image/webp`).
- Max payload size strictly capped at 10 MB (configurable up to 50 MB with validation).
- Client filename is never trusted: sanitized against path traversal (`../`, `..\`, null bytes) and saved with random UUID filenames.
- Deep binary inspection with Pillow `Image.verify()` ensures fake/malicious file binaries are rejected with `HTTP 400`.

### 5. Information Disclosure Prevention
- Exception handlers intercept `AppException`, `StarletteHTTPException`, `RequestValidationError`, `IntegrityError`, and `SQLAlchemyError`.
- Raw SQL statements, database connection strings, absolute filesystem paths, and Python tracebacks are never exposed to the client.

### 6. Production Configuration Validation
When `ENVIRONMENT=production`:
- Rejects default or weak `JWT_SECRET_KEY` (must be $\ge 32$ characters).
- Rejects wildcard `*` in `CORS_ORIGINS`.
- Validates bounds for token expiration (1-43200 min), upload size (1KB-50MB), and OCR timeout (1-300s).

### 7. Rate Limiting Architecture Recommendations
For production deployment with multiple instances:
- Apply token-bucket or sliding-window rate limiting on compute/auth endpoints:
  - `POST /api/auth/login`: 5 req/min per IP
  - `POST /api/verifications/upload`: 10 req/min per user
  - `POST /api/verifications/{id}/process`: 10 req/min per user
  - `GET /api/verifications/{id}/report/pdf`: 15 req/min per user

---

## API Endpoints

### Authentication
- `POST /api/auth/login`: Authenticate with email/password to obtain JWT Bearer token.
- `GET /api/auth/me`: Retrieve current authenticated user profile.

### Verification, OCR, Compliance, Reports & PDF Export
- `POST /api/verifications/upload`: Upload packaged product image (`multipart/form-data`) -> `201 Created` [Inspector/Admin].
- `POST /api/verifications/{id}/process`: Run OCR and field extraction pipeline -> `200 OK` [Inspector/Admin, Ownership].
- `GET /api/verifications/{id}/fields`: Retrieve all structured fields -> `200 OK` [Authenticated, Ownership].
- `POST /api/verifications/{id}/compliance`: Evaluate compliance rules and calculate score -> `200 OK` [Inspector/Admin, Ownership].
- `GET /api/verifications/{id}/compliance`: Retrieve evaluated rule check results -> `200 OK` [Authenticated, Ownership].
- `POST /api/verifications/{id}/report`: Generate/regenerate structured compliance report -> `200 OK` [Inspector/Admin, Ownership].
- `GET /api/verifications/{id}/report`: Retrieve latest compliance report -> `200 OK` [Authenticated, Ownership].
- `GET /api/verifications/{id}/report/pdf`: Stream publication-grade PDF report -> `200 OK` (`application/pdf`) [Authenticated, Ownership].
- `GET /api/verifications/{id}/audit-logs`: Retrieve chronological audit events -> `200 OK` [Authenticated, Ownership].

### CRUD Endpoints
- `Users`: `POST /api/users`, `GET /api/users`, `GET /api/users/{id}`, `DELETE /api/users/{id}`
- `Products`: `POST /api/products`, `GET /api/products`, `GET /api/products/{id}`, `DELETE /api/products/{id}`
- `Verifications`: `POST /api/verifications`, `GET /api/verifications`, `GET /api/verifications/{id}`, `DELETE /api/verifications/{id}`
- `Extracted Fields`: `POST /api/extracted-fields`, `GET /api/extracted-fields`, `GET /api/extracted-fields/{id}`, `DELETE /api/extracted-fields/{id}`
- `Compliance Checks`: `POST /api/compliance-checks`, `GET /api/compliance-checks`, `GET /api/compliance-checks/{id}`, `DELETE /api/compliance-checks/{id}`
- `Reports`: `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{id}`, `DELETE /api/reports/{id}`
- `Health`: `GET /api/health`, `GET /api/health/db`

---

## Running Automated Tests

Run the complete 147-test verification suite:

```bash
pytest -v
```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
