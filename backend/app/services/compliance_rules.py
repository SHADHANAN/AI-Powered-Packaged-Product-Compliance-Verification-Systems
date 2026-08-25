from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from app.models.enums import ComplianceStatus, Severity
from app.utils.compliance_validators import (
    ALLOWED_UNITS,
    validate_customer_care_details,
    validate_date_format,
    validate_mrp,
    validate_quantity_and_unit,
    validate_required_text,
)


@dataclass
class RuleEvaluationResult:
    """Outcome of a single compliance rule evaluation."""

    rule_code: str
    rule_name: str
    status: ComplianceStatus
    severity: Severity
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class ComplianceRule:
    """Definition of a Legal Metrology packaged commodity compliance rule."""

    rule_code: str
    rule_name: str
    description: str
    severity: Severity
    required_fields: List[str]
    evaluate: Callable[[Dict[str, str]], RuleEvaluationResult]


# ----------------------------------------------------------------------
# RULE DEFINITIONS
# ----------------------------------------------------------------------

def eval_mrp_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate Maximum Retail Price (MRP) declaration (Legal Metrology Packaged Commodities Rule 6)."""
    mrp_raw = fields.get("mrp")
    is_valid, parsed_mrp, msg = validate_mrp(mrp_raw)

    if not mrp_raw:
        return RuleEvaluationResult(
            rule_code="LM-MRP-001",
            rule_name="Mandatory MRP Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Maximum Retail Price (MRP) is not declared on the package label.",
            expected_value="Positive numeric price declaration (e.g. MRP Rs. 250.00)",
            actual_value=None,
            recommendation="Ensure 'MRP Rs. XX.XX (inclusive of all taxes)' is prominently printed on the principal display panel.",
        )
    elif not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-MRP-001",
            rule_name="Mandatory MRP Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message=f"Invalid MRP declaration: {msg}",
            expected_value="Valid positive numeric value",
            actual_value=mrp_raw,
            recommendation="Format MRP as a valid positive number with applicable currency symbol.",
        )
    return RuleEvaluationResult(
        rule_code="LM-MRP-001",
        rule_name="Mandatory MRP Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Valid MRP declared: Rs. {msg}",
        expected_value="Valid positive numeric price",
        actual_value=mrp_raw,
    )


def eval_net_quantity_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate Net Quantity declaration."""
    qty_raw = fields.get("net_quantity")
    is_valid_qty, is_valid_unit, num_val, unit, msg = validate_quantity_and_unit(qty_raw, fields.get("quantity_unit"))

    if not qty_raw:
        return RuleEvaluationResult(
            rule_code="LM-QTY-001",
            rule_name="Mandatory Net Quantity Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Net quantity declaration is missing from the package label.",
            expected_value="Numeric quantity with unit (e.g. Net Qty: 500 g)",
            actual_value=None,
            recommendation="Declare net quantity prominently with standard measurement unit on the package.",
        )
    elif not is_valid_qty:
        return RuleEvaluationResult(
            rule_code="LM-QTY-001",
            rule_name="Mandatory Net Quantity Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message=f"Invalid net quantity declaration: {msg}",
            expected_value="Positive numeric quantity",
            actual_value=qty_raw,
            recommendation="Ensure net quantity is a positive non-zero quantity.",
        )
    return RuleEvaluationResult(
        rule_code="LM-QTY-001",
        rule_name="Mandatory Net Quantity Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Valid net quantity declared: {msg}",
        expected_value="Valid positive numeric quantity",
        actual_value=qty_raw,
    )


def eval_quantity_unit_validity(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate standard Legal Metrology measurement units."""
    qty_raw = fields.get("net_quantity")
    unit_raw = fields.get("quantity_unit")
    is_valid_qty, is_valid_unit, num_val, unit, msg = validate_quantity_and_unit(qty_raw, unit_raw)

    if not qty_raw and not unit_raw:
        return RuleEvaluationResult(
            rule_code="LM-UNIT-001",
            rule_name="Approved Measurement Unit Check",
            status=ComplianceStatus.FAIL,
            severity=Severity.MEDIUM,
            message="Measurement unit is missing because net quantity was not declared.",
            expected_value=f"One of standard units: {', '.join(sorted(list(ALLOWED_UNITS)[:8]))}...",
            actual_value=None,
            recommendation="Use standard SI / metric units of weight, volume, length, or piece count.",
        )
    elif not is_valid_unit:
        return RuleEvaluationResult(
            rule_code="LM-UNIT-001",
            rule_name="Approved Measurement Unit Check",
            status=ComplianceStatus.WARNING,
            severity=Severity.MEDIUM,
            message=f"Non-standard measurement unit detected: '{unit or unit_raw}'",
            expected_value="Approved metric / SI unit (g, kg, ml, l, pcs, etc.)",
            actual_value=unit or unit_raw,
            recommendation="Standardize the declared unit to approved Legal Metrology units (e.g. 'g', 'kg', 'ml', 'l', 'pieces').",
        )
    return RuleEvaluationResult(
        rule_code="LM-UNIT-001",
        rule_name="Approved Measurement Unit Check",
        status=ComplianceStatus.PASS,
        severity=Severity.MEDIUM,
        message=f"Standard approved unit declared: '{unit}'",
        expected_value="Approved metric / SI unit",
        actual_value=unit,
    )


def eval_product_name_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate generic / commodity product name declaration."""
    name_raw = fields.get("product_name")
    is_valid, val = validate_required_text(name_raw, min_length=2)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-NAME-001",
            rule_name="Product Name / Commodity Declaration",
            status=ComplianceStatus.WARNING,
            severity=Severity.MEDIUM,
            message="Generic or specific commodity name was not clearly identified.",
            expected_value="Generic name of packaged commodity",
            actual_value=name_raw,
            recommendation="Ensure product / commodity name is distinctly printed on the main display area.",
        )
    return RuleEvaluationResult(
        rule_code="LM-NAME-001",
        rule_name="Product Name / Commodity Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.MEDIUM,
        message=f"Product name declared: '{val}'",
        expected_value="Commodity name declaration",
        actual_value=val,
    )


def eval_brand_name_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate brand / trademark declaration."""
    brand_raw = fields.get("brand_name")
    is_valid, val = validate_required_text(brand_raw, min_length=2)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-BRAND-001",
            rule_name="Brand Name / Trademark Declaration",
            status=ComplianceStatus.WARNING,
            severity=Severity.LOW,
            message="Brand or trademark name was not explicitly identified in extracted label fields.",
            expected_value="Brand or manufacturer trademark",
            actual_value=brand_raw,
            recommendation="Ensure brand name or trademark is identifiable on the label.",
        )
    return RuleEvaluationResult(
        rule_code="LM-BRAND-001",
        rule_name="Brand Name / Trademark Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.LOW,
        message=f"Brand name declared: '{val}'",
        expected_value="Brand / trademark declaration",
        actual_value=val,
    )


def eval_manufacturer_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate manufacturer name and address declaration."""
    mfr_raw = fields.get("manufacturer")
    is_valid, val = validate_required_text(mfr_raw, min_length=5)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-MFR-001",
            rule_name="Manufacturer Details Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.CRITICAL,
            message="Manufacturer name and address details are missing or incomplete.",
            expected_value="Name and complete address of the manufacturer / packer",
            actual_value=mfr_raw,
            recommendation="Print 'Manufactured by / Packed by: [Name & Address]' clearly on the package.",
        )
    return RuleEvaluationResult(
        rule_code="LM-MFR-001",
        rule_name="Manufacturer Details Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.CRITICAL,
        message=f"Manufacturer details declared: '{val}'",
        expected_value="Manufacturer name and address",
        actual_value=val,
    )


def eval_importer_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate importer details for imported products."""
    imp_raw = fields.get("importer")
    imp_date_raw = fields.get("import_date")
    country_raw = fields.get("country_of_origin")

    # If the product has import date or country of origin other than domestic, importer is required
    is_imported = bool(imp_date_raw or (country_raw and "india" not in country_raw.lower()))

    if not is_imported and not imp_raw:
        return RuleEvaluationResult(
            rule_code="LM-IMP-001",
            rule_name="Importer Declaration Check",
            status=ComplianceStatus.NOT_APPLICABLE,
            severity=Severity.HIGH,
            message="Importer details not required for domestic non-imported commodity.",
            expected_value="N/A for domestic goods",
            actual_value=None,
        )

    is_valid, val = validate_required_text(imp_raw, min_length=4)
    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-IMP-001",
            rule_name="Importer Declaration Check",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Imported commodity must declare name and complete address of importer.",
            expected_value="Name and address of importer",
            actual_value=imp_raw,
            recommendation="Include 'Imported and Packaged by: [Name & Address]' on imported commodities.",
        )
    return RuleEvaluationResult(
        rule_code="LM-IMP-001",
        rule_name="Importer Declaration Check",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Importer details declared: '{val}'",
        expected_value="Importer details declaration",
        actual_value=val,
    )


def eval_country_of_origin(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate country of origin declaration."""
    coo_raw = fields.get("country_of_origin")
    is_valid, val = validate_required_text(coo_raw, min_length=2)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-COO-001",
            rule_name="Country of Origin Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Country of origin is missing from label declaration.",
            expected_value="Country of origin (e.g. Made in India, Country of Origin: USA)",
            actual_value=coo_raw,
            recommendation="Include 'Country of Origin: [Country]' conspicuously on the label.",
        )
    return RuleEvaluationResult(
        rule_code="LM-COO-001",
        rule_name="Country of Origin Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Country of origin declared: '{val}'",
        expected_value="Country of origin declaration",
        actual_value=val,
    )


def eval_batch_number_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate Batch / Lot / Lot number declaration."""
    batch_raw = fields.get("batch_number")
    is_valid, val = validate_required_text(batch_raw, min_length=2)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-BATCH-001",
            rule_name="Batch / Lot Number Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.MEDIUM,
            message="Batch number, lot number, or lot identification code is missing.",
            expected_value="Batch / Lot number (e.g. Batch: B-2024/09A)",
            actual_value=batch_raw,
            recommendation="Clearly print batch number or lot identifier on package.",
        )
    return RuleEvaluationResult(
        rule_code="LM-BATCH-001",
        rule_name="Batch / Lot Number Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.MEDIUM,
        message=f"Batch number declared: '{val}'",
        expected_value="Batch / lot identifier",
        actual_value=val,
    )


def eval_mfg_date_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate date of manufacture / packaging declaration."""
    mfg_raw = fields.get("manufacturing_date")
    is_valid, val = validate_date_format(mfg_raw)

    if not mfg_raw:
        return RuleEvaluationResult(
            rule_code="LM-MFG-001",
            rule_name="Manufacturing / Packing Date Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Month and year of manufacture or packing is not declared.",
            expected_value="Date of manufacture/packing (e.g. MFD: 10/2024)",
            actual_value=None,
            recommendation="Print 'Mfg Date: MM/YYYY' or 'Packed on: DD/MM/YYYY' on package.",
        )
    elif not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-MFG-001",
            rule_name="Manufacturing / Packing Date Declaration",
            status=ComplianceStatus.WARNING,
            severity=Severity.HIGH,
            message=f"Date format warning: {val}",
            expected_value="Standard date format (DD/MM/YYYY or MM/YYYY)",
            actual_value=mfg_raw,
            recommendation="Standardize date format to MM/YYYY or DD/MM/YYYY.",
        )
    return RuleEvaluationResult(
        rule_code="LM-MFG-001",
        rule_name="Manufacturing / Packing Date Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Manufacturing date declared: '{val}'",
        expected_value="Date of manufacture/packing",
        actual_value=val,
    )


def eval_import_date_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate date of import for imported products."""
    imp_date_raw = fields.get("import_date")
    imp_raw = fields.get("importer")
    coo_raw = fields.get("country_of_origin")

    is_imported = bool(imp_raw or (coo_raw and "india" not in coo_raw.lower()))

    if not is_imported and not imp_date_raw:
        return RuleEvaluationResult(
            rule_code="LM-IMPDT-001",
            rule_name="Import Date Declaration",
            status=ComplianceStatus.NOT_APPLICABLE,
            severity=Severity.MEDIUM,
            message="Import date not applicable for domestic non-imported products.",
            expected_value="N/A for domestic goods",
            actual_value=None,
        )

    is_valid, val = validate_date_format(imp_date_raw)
    if not imp_date_raw:
        return RuleEvaluationResult(
            rule_code="LM-IMPDT-001",
            rule_name="Import Date Declaration",
            status=ComplianceStatus.WARNING,
            severity=Severity.MEDIUM,
            message="Month and year of import is recommended for imported packages.",
            expected_value="Import date (e.g. IMPORT DT: 11/2024)",
            actual_value=None,
            recommendation="Include month and year of import on label.",
        )
    elif not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-IMPDT-001",
            rule_name="Import Date Declaration",
            status=ComplianceStatus.WARNING,
            severity=Severity.MEDIUM,
            message=f"Import date format warning: {val}",
            expected_value="Standard date format (MM/YYYY or DD/MM/YYYY)",
            actual_value=imp_date_raw,
            recommendation="Format import date as MM/YYYY.",
        )
    return RuleEvaluationResult(
        rule_code="LM-IMPDT-001",
        rule_name="Import Date Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.MEDIUM,
        message=f"Import date declared: '{val}'",
        expected_value="Date of import",
        actual_value=val,
    )


def eval_customer_care_declaration(fields: Dict[str, str]) -> RuleEvaluationResult:
    """Evaluate consumer care contact details declaration."""
    care_raw = fields.get("customer_care_details")
    is_valid, val = validate_customer_care_details(care_raw)

    if not is_valid:
        return RuleEvaluationResult(
            rule_code="LM-CARE-001",
            rule_name="Consumer Care Details Declaration",
            status=ComplianceStatus.FAIL,
            severity=Severity.HIGH,
            message="Consumer care contact details (telephone/email/postal address) are missing.",
            expected_value="Consumer care helpline number, email, or contact address",
            actual_value=care_raw,
            recommendation="Provide name, address, telephone number and email of person/office to contact in case of consumer complaints.",
        )
    return RuleEvaluationResult(
        rule_code="LM-CARE-001",
        rule_name="Consumer Care Details Declaration",
        status=ComplianceStatus.PASS,
        severity=Severity.HIGH,
        message=f"Consumer care details declared: '{val}'",
        expected_value="Consumer care contact details",
        actual_value=val,
    )


# Registered master rule list
ALL_RULES: List[ComplianceRule] = [
    ComplianceRule(
        rule_code="LM-NAME-001",
        rule_name="Product Name / Commodity Declaration",
        description="Mandatory declaration of the generic or specific name of commodity.",
        severity=Severity.MEDIUM,
        required_fields=["product_name"],
        evaluate=eval_product_name_declaration,
    ),
    ComplianceRule(
        rule_code="LM-BRAND-001",
        rule_name="Brand Name / Trademark Declaration",
        description="Brand name or trademark declaration on package.",
        severity=Severity.LOW,
        required_fields=["brand_name"],
        evaluate=eval_brand_name_declaration,
    ),
    ComplianceRule(
        rule_code="LM-MFR-001",
        rule_name="Manufacturer Details Declaration",
        description="Name and complete address of the manufacturer / packer.",
        severity=Severity.CRITICAL,
        required_fields=["manufacturer"],
        evaluate=eval_manufacturer_declaration,
    ),
    ComplianceRule(
        rule_code="LM-IMP-001",
        rule_name="Importer Declaration Check",
        description="Name and complete address of importer for imported commodities.",
        severity=Severity.HIGH,
        required_fields=["importer"],
        evaluate=eval_importer_declaration,
    ),
    ComplianceRule(
        rule_code="LM-COO-001",
        rule_name="Country of Origin Declaration",
        description="Mandatory country of origin declaration.",
        severity=Severity.HIGH,
        required_fields=["country_of_origin"],
        evaluate=eval_country_of_origin,
    ),
    ComplianceRule(
        rule_code="LM-QTY-001",
        rule_name="Mandatory Net Quantity Declaration",
        description="Declaration of net quantity in terms of standard unit of weight or measure.",
        severity=Severity.HIGH,
        required_fields=["net_quantity"],
        evaluate=eval_net_quantity_declaration,
    ),
    ComplianceRule(
        rule_code="LM-UNIT-001",
        rule_name="Approved Measurement Unit Check",
        description="Validity of measurement units under Legal Metrology standards.",
        severity=Severity.MEDIUM,
        required_fields=["quantity_unit", "net_quantity"],
        evaluate=eval_quantity_unit_validity,
    ),
    ComplianceRule(
        rule_code="LM-MRP-001",
        rule_name="Mandatory MRP Declaration",
        description="Declaration of Maximum Retail Price (MRP) inclusive of all taxes.",
        severity=Severity.HIGH,
        required_fields=["mrp"],
        evaluate=eval_mrp_declaration,
    ),
    ComplianceRule(
        rule_code="LM-BATCH-001",
        rule_name="Batch / Lot Number Declaration",
        description="Batch number, lot number, or lot code identifier.",
        severity=Severity.MEDIUM,
        required_fields=["batch_number"],
        evaluate=eval_batch_number_declaration,
    ),
    ComplianceRule(
        rule_code="LM-MFG-001",
        rule_name="Manufacturing / Packing Date Declaration",
        description="Month and year of manufacture or packaging declaration.",
        severity=Severity.HIGH,
        required_fields=["manufacturing_date"],
        evaluate=eval_mfg_date_declaration,
    ),
    ComplianceRule(
        rule_code="LM-IMPDT-001",
        rule_name="Import Date Declaration",
        description="Month and year of import for imported commodities.",
        severity=Severity.MEDIUM,
        required_fields=["import_date"],
        evaluate=eval_import_date_declaration,
    ),
    ComplianceRule(
        rule_code="LM-CARE-001",
        rule_name="Consumer Care Details Declaration",
        description="Contact details for consumer grievance and feedback.",
        severity=Severity.HIGH,
        required_fields=["customer_care_details"],
        evaluate=eval_customer_care_declaration,
    ),
]
