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

## Phase 7: OCR & Field Extraction Pipeline

### Pipeline Flow

```text
Verification (Status: PENDING)
        ↓
POST /api/verifications/{id}/process (JWT Auth)
        ↓
Status updated to PROCESSING
        ↓
Load Stored Image (uploads/images/<uuid>.<ext>)
        ↓
Pillow Image Preprocessing (Grayscale, Resize, Contrast, Sharpness)
        ↓
Tesseract OCR Text Extraction
        ↓
Verification.ocr_raw_text updated
        ↓
Structured Field Extraction (Legal Metrology regex heuristics)
        ↓
Persist ExtractedField records (with confidence 0.0-1.0 and source text)
        ↓
Status updated to COMPLETED (or FAILED on error)
        ↓
Return VerificationRead
```

### Supported Extracted Fields

| Field Name | Description | Example Extracted Value |
| :--- | :--- | :--- |
| `mrp` | Maximum Retail Price | `299.00` |
| `net_quantity` | Net Quantity & Unit | `500 g` |
| `quantity_unit` | Isolated Measurement Unit | `g`, `ml`, `kg`, `pcs` |
| `batch_number` | Batch / Lot Identification | `B-2024/09A` |
| `manufacturing_date` | Manufacturing / Packaging Date | `15/08/2024` |
| `import_date` | Importation Date | `10/2024` |
| `country_of_origin` | Country of Origin Declaration | `India` |
| `manufacturer` | Name and Address of Manufacturer | `HealthFoods India Ltd, Bangalore` |
| `importer` | Name and Address of Importer | `Global Imports Ltd, Mumbai` |
| `customer_care_details`| Consumer Care Email / Phone / Address | `care@brandfoods.com / 1800-111-2222` |
| `product_name` | Declared Name of Commodity | `Crunchy Almond Granola` |
| `brand_name` | Brand / Trademark Identifier | `NutriBite` |

---

## API Endpoints

### Authentication
- `POST /api/auth/login`: Authenticate with email/password to obtain JWT Bearer token.
- `GET /api/auth/me`: Retrieve current authenticated user profile.

### Verification & Processing
- `POST /api/verifications/upload`: Upload packaged product image (`multipart/form-data`) -> `201 Created`.
- `POST /api/verifications/{id}/process`: Run OCR and field extraction pipeline on uploaded image -> `200 OK`.
- `GET /api/verifications/{id}/fields`: Retrieve all structured fields extracted for a verification -> `200 OK`.

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

Run the complete 96-test verification suite:

```bash
pytest -v
```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
