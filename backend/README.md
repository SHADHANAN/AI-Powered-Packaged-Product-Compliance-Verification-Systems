# AI-Powered Packaged Product Compliance Verification System - Backend

Production-oriented FastAPI backend for automated packaged product Legal Metrology regulatory compliance verification.

---

## Architecture Overview

- **Phase 1 (Foundation)**: Modular structure, Pydantic settings, structured logging, global exception handling, OpenAPI & ReDoc documentation.
- **Phase 2 (Database Foundation)**: PostgreSQL integration with SQLAlchemy 2.x, psycopg driver, Alembic migrations, connection health checks.
- **Phase 3 (Database Models)**: Comprehensive SQLAlchemy 2.x typed models, constraints, relationships, indexes, Pydantic schemas, and Alembic migrations.
- **Phase 4 (CRUD Services & API Routers)**: Clean service layer with repository/service pattern, thin routers, transactional rollback, cascade deletion handling.
- **Phase 5 (Security & JWT Auth)**: Argon2id password hashing, JWT Bearer authentication (`POST /api/auth/login`, `GET /api/auth/me`), `get_current_user` dependency.
- **Phase 6 (Image Upload & Verification Pipeline)**: Authenticated multi-format product image upload, binary validation, path-traversal prevention, atomic file rollback, and verification record creation.

---

## Entity Relationship Overview

```text
User (Inspector/Admin)
 │
 └── Verification
       │
       ├── Product (Packaged Commodity)
       ├── ExtractedField (1..N OCR Extracted Key-Values)
       ├── ComplianceCheck (1..N Rule Evaluation Results)
       └── Report (1..N Generated Export Documents)
```

---

## Phase 6: Image Upload & Verification Pipeline

### Endpoint: `POST /api/verifications/upload`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required (`Authorization: Bearer <JWT>`)
- **Form Parameters**:
  - `file`: Image file binary (`UploadFile`, Required)
  - `product_id`: Optional associated Product UUID (`Form(None)`)
- **Supported Formats**: `JPEG`, `JPG`, `PNG`, `WEBP`
- **Allowed MIME Types**: `image/jpeg`, `image/png`, `image/webp`
- **Maximum File Size**: `10 MB` (Configurable via `MAX_UPLOAD_SIZE_BYTES`)
- **Success Status**: `201 Created` returning `VerificationRead`

### Image Storage & Security Protections
- **Sanitized UUID Storage**: Files are saved as `{uuid4}.{ext}` inside `uploads/images/`, stripping client-supplied names to completely prevent path traversal (`../../`).
- **Binary Integrity Verification**: Validates magic bytes and structural image headers using Pillow to reject corrupted files and non-image payloads disguised with image extensions.
- **Atomic Cleanup**: If database creation or foreign key validation fails, uploaded image files are deleted immediately to avoid orphaned storage artifacts.
- **Protected Storage**: Uploads directory is not exposed as a public static directory.

### Error Responses
- `401 Unauthorized`: Missing, expired, or invalid JWT Bearer token.
- `400 Bad Request`: Empty file (0 bytes), unsupported extension, mismatched MIME type, or corrupted image.
- `413 Payload Too Large`: Uploaded image exceeds 10 MB limit.
- `404 Not Found`: Provided `product_id` does not exist.
- `500 Internal Server Error`: Disk write or storage failure without leaking filesystem internals.

---

## Database Migrations (Alembic)

From the `backend/` directory:

- **Apply all migrations**:
  ```bash
  alembic upgrade head
  ```

- **Roll back the latest migration**:
  ```bash
  alembic downgrade -1
  ```

- **Check current revision**:
  ```bash
  alembic current
  ```

---

## Running Automated Tests

Run the complete test suite across database, models, auth, CRUD, and image upload:

```bash
pytest -v
```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
