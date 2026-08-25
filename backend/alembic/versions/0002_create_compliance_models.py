"""create compliance database models

Revision ID: 0002_create_compliance_models
Revises: 0001_initial_schema
Create Date: 2026-08-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_create_compliance_models"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="inspector", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    # 2. products table
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=True),
        sa.Column("brand_name", sa.String(length=255), nullable=True),
        sa.Column("manufacturer", sa.String(length=500), nullable=True),
        sa.Column("importer", sa.String(length=500), nullable=True),
        sa.Column("country_of_origin", sa.String(length=100), nullable=True),
        sa.Column("net_quantity", sa.String(length=100), nullable=True),
        sa.Column("quantity_unit", sa.String(length=50), nullable=True),
        sa.Column("batch_number", sa.String(length=100), nullable=True),
        sa.Column("manufacturing_date", sa.Date(), nullable=True),
        sa.Column("import_date", sa.Date(), nullable=True),
        sa.Column("mrp", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("customer_care_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_product_name", "products", ["product_name"], unique=False)
    op.create_index("ix_products_brand_name", "products", ["brand_name"], unique=False)

    # 3. verifications table
    op.create_table(
        "verifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("inspector_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("source_image_path", sa.String(length=1000), nullable=False),
        sa.Column("ocr_raw_text", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("overall_score >= 0.0 AND overall_score <= 100.0", name="ck_verification_overall_score"),
        sa.ForeignKeyConstraint(["inspector_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verifications_id", "verifications", ["id"], unique=False)
    op.create_index("ix_verifications_product_id", "verifications", ["product_id"], unique=False)
    op.create_index("ix_verifications_inspector_id", "verifications", ["inspector_id"], unique=False)
    op.create_index("ix_verifications_status", "verifications", ["status"], unique=False)
    op.create_index("ix_verifications_status_created_at", "verifications", ["status", "created_at"], unique=False)

    # 4. extracted_fields table
    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("verification_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_extracted_field_confidence"),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extracted_fields_id", "extracted_fields", ["id"], unique=False)
    op.create_index("ix_extracted_fields_verification_id", "extracted_fields", ["verification_id"], unique=False)
    op.create_index("ix_extracted_fields_field_name", "extracted_fields", ["field_name"], unique=False)
    op.create_index("ix_extracted_fields_verification_field_name", "extracted_fields", ["verification_id", "field_name"], unique=False)

    # 5. compliance_checks table
    op.create_table(
        "compliance_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("verification_id", sa.Uuid(), nullable=False),
        sa.Column("rule_code", sa.String(length=100), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("actual_value", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compliance_checks_id", "compliance_checks", ["id"], unique=False)
    op.create_index("ix_compliance_checks_verification_id", "compliance_checks", ["verification_id"], unique=False)
    op.create_index("ix_compliance_checks_rule_code", "compliance_checks", ["rule_code"], unique=False)
    op.create_index("ix_compliance_checks_status", "compliance_checks", ["status"], unique=False)
    op.create_index("ix_compliance_checks_severity", "compliance_checks", ["severity"], unique=False)
    op.create_index("ix_compliance_checks_verification_rule", "compliance_checks", ["verification_id", "rule_code"], unique=False)
    op.create_index("ix_compliance_checks_status_severity", "compliance_checks", ["status", "severity"], unique=False)

    # 6. reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("verification_id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_id", "reports", ["id"], unique=False)
    op.create_index("ix_reports_verification_id", "reports", ["verification_id"], unique=False)


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("compliance_checks")
    op.drop_table("extracted_fields")
    op.drop_table("verifications")
    op.drop_table("products")
    op.drop_table("users")
