# AI-Powered Packaged Product Compliance Verification System - Backend

Production-oriented FastAPI backend foundation for verifying packaged product regulatory compliance.

---

## Architecture Overview

- **Phase 1 (Foundation)**: Modular structure, Pydantic settings, structured logging, global exception handling, OpenAPI & ReDoc documentation.
- **Phase 2 (Database Foundation)**: PostgreSQL integration with SQLAlchemy 2.x, psycopg driver, Alembic migrations, connection health checks, and Docker Compose PostgreSQL service.
- **Phase 3 (Database Models)**: Comprehensive SQLAlchemy 2.x typed models, constraints, relationships, indexes, Pydantic schemas, and Alembic migrations.

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

### Models Summary

1. **`User`** (`users`): Represents system users, inspectors, and administrators.
   - Primary key: UUID `id`
   - Unique indexed `email`
   - Secure `password_hash`
   - `role`: Enum (`admin`, `inspector`, `viewer`)
   - `is_active`: Boolean
   - Timestamps: `created_at`, `updated_at`

2. **`Product`** (`products`): Represents the packaged commodity under inspection.
   - Primary key: UUID `id`
   - Nullable OCR-tolerant fields: `product_name`, `brand_name`, `manufacturer`, `importer`, `country_of_origin`, `net_quantity`, `quantity_unit`, `batch_number`, `manufacturing_date`, `import_date`, `mrp` (Decimal/Numeric), `customer_care_details`
   - Timestamps: `created_at`, `updated_at`

3. **`Verification`** (`verifications`): Represents an inspection/verification attempt.
   - Primary key: UUID `id`
   - Foreign keys: `product_id` -> `products.id`, `inspector_id` -> `users.id`
   - `status`: Enum (`pending`, `processing`, `completed`, `failed`)
   - `overall_score`: Float with CheckConstraint (0.0 to 100.0)
   - `source_image_path`: Location of uploaded package image
   - `ocr_raw_text`: Raw extracted text
   - Timestamps: `created_at`, `updated_at`, `completed_at`

4. **`ExtractedField`** (`extracted_fields`): Normalized OCR key-value pairs and evidence.
   - Primary key: UUID `id`
   - Foreign key: `verification_id` -> `verifications.id` (ON DELETE CASCADE)
   - `field_name`: String (e.g. `mrp`, `net_quantity`, `brand_name`)
   - `field_value`: Extracted textual value
   - `confidence`: Float with CheckConstraint (0.0 to 1.0)
   - `source_text`: Snippet / evidence text from OCR
   - Timestamps: `created_at`, `updated_at`

5. **`ComplianceCheck`** (`compliance_checks`): Legal Metrology rule evaluation outcomes.
   - Primary key: UUID `id`
   - Foreign key: `verification_id` -> `verifications.id` (ON DELETE CASCADE)
   - `rule_code`: String (e.g. `LM_MRP_DECLARATION`)
   - `rule_name`: String (e.g. `Mandatory MRP Declaration Check`)
   - `status`: Enum (`pass`, `fail`, `warning`, `not_applicable`)
   - `severity`: Enum (`low`, `medium`, `high`, `critical`)
   - `message`, `expected_value`, `actual_value`, `recommendation`
   - Timestamps: `created_at`, `updated_at`

6. **`Report`** (`reports`): Exported verification reports.
   - Primary key: UUID `id`
   - Foreign key: `verification_id` -> `verifications.id` (ON DELETE CASCADE)
   - `report_type`: Enum (`pdf`, `excel`)
   - `file_path`: Storage location of generated file
   - `generated_at`: Timestamp

---

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & lifecycle
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── database.py              # SQLAlchemy 2.x engine, SessionLocal, get_db
│   ├── api/
│   │   ├── __init__.py          # API router aggregation
│   │   └── health.py            # Health check & DB health endpoints
│   ├── services/
│   │   └── __init__.py          # Business logic services placeholder
│   ├── schemas/
│   │   ├── __init__.py          # Pydantic schemas index
│   │   ├── common.py            # Common response & error schemas
│   │   ├── health.py            # Health check schemas
│   │   ├── user.py              # User validation schemas
│   │   ├── product.py           # Product validation schemas
│   │   ├── verification.py      # Verification validation schemas
│   │   ├── extracted_field.py   # ExtractedField validation schemas
│   │   ├── compliance_check.py  # ComplianceCheck validation schemas
│   │   └── report.py            # Report validation schemas
│   ├── models/
│   │   ├── __init__.py          # Database models package index
│   │   ├── base.py              # DeclarativeBase, UUIDPrimaryKeyMixin, TimestampMixin
│   │   ├── enums.py             # Centralized enums
│   │   ├── user.py              # User model
│   │   ├── product.py           # Product model
│   │   ├── verification.py      # Verification model
│   │   ├── extracted_field.py   # ExtractedField model
│   │   ├── compliance_check.py  # ComplianceCheck model
│   │   └── report.py            # Report model
│   └── utils/
│       ├── __init__.py
│       ├── exceptions.py        # Custom exceptions & global handlers
│       └── logging.py           # Structured application logging
├── alembic/
│   ├── versions/
│   │   ├── 0001_initial_schema.py           # Initial baseline migration
│   │   └── 0002_create_compliance_models.py # Compliance database models migration
│   ├── env.py                  # Alembic runtime environment (dynamic DB URL & Base)
│   ├── script.py.mako          # Migration template
│   └── README
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and TestClient setup
│   ├── test_database.py         # Database engine & Alembic tests
│   ├── test_models.py           # Models, constraints, ORM relationships & schemas tests
│   └── test_health.py           # Health endpoints and API tests
├── alembic.ini                  # Alembic migration configuration
├── requirements.txt             # Project dependencies
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

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

- **Generate SQL script without connecting (Offline mode)**:
  ```bash
  alembic upgrade head --sql
  ```

---

## Running Automated Tests

Run the complete test suite:

```bash
pytest -v
```

---

## Running the Application

Start the development server with hot reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
