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

---

## Entity Relationship Overview

```text
User (Inspector/Admin)
 │
 ├── AuditLog (1..N Verification Lifecycle Events)
 │
 └── Verification
       │
       ├── Product (Packaged Commodity)
       ├── ExtractedField (1..N OCR Extracted Key-Values)
       ├── ComplianceCheck (1..N Rule Evaluation Results)
       ├── Report (1..N Generated Export Documents)
       └── AuditLog (1..N Verification Lifecycle Events)
```

---

## Phase 9 Step 1: Compliance Report & Audit Trail

### Structured Report Content
A generated compliance report provides an aggregated snapshot of:
- **Metadata**: Report ID, Verification ID, Generation timestamp, Verification status (`COMPLETED`).
- **Product Details**: Generic product name, brand, manufacturer, country of origin, net quantity, MRP, batch number.
- **Inspector Identity**: Sanitized inspector profile (ID, name, email, role - zero credential leakage).
- **Summary**: Total rules evaluated, passed, failed, warning, and not-applicable counts with the overall percentage score.
- **Extracted Fields**: Structured key-values with confidence and OCR source text.
- **Rules & Violations**: Complete evaluation outcomes with affected fields, expected vs detected values, and corrective recommendations.

### Audit Trail Events
The system automatically logs chronological lifecycle events for every verification run:
1. `IMAGE_UPLOADED`: Stored image binary with size and sanitized filename.
2. `OCR_PROCESSED`: Completed text extraction with character count.
3. `FIELDS_EXTRACTED`: Extracted structured Legal Metrology label fields.
4. `COMPLIANCE_CHECKED`: Evaluated regulatory compliance rules with score.
5. `REPORT_GENERATED`: Generated structured audit-ready compliance report.

---

## API Endpoints

### Authentication
- `POST /api/auth/login`: Authenticate with email/password to obtain JWT Bearer token.
- `GET /api/auth/me`: Retrieve current authenticated user profile.

### Verification, OCR, Compliance & Reports
- `POST /api/verifications/upload`: Upload packaged product image (`multipart/form-data`) -> `201 Created`.
- `POST /api/verifications/{id}/process`: Run OCR and field extraction pipeline on uploaded image -> `200 OK`.
- `GET /api/verifications/{id}/fields`: Retrieve all structured fields extracted for a verification -> `200 OK`.
- `POST /api/verifications/{id}/compliance`: Evaluate compliance rules and calculate overall score -> `200 OK`.
- `GET /api/verifications/{id}/compliance`: Retrieve evaluated rule check results and summary -> `200 OK`.
- `POST /api/verifications/{id}/report`: Generate/regenerate structured compliance report -> `200 OK`.
- `GET /api/verifications/{id}/report`: Retrieve the latest generated compliance report -> `200 OK`.
- `GET /api/verifications/{id}/audit-logs`: Retrieve chronological audit events for verification -> `200 OK`.

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

Run the complete 117-test verification suite:

```bash
pytest -v
```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
