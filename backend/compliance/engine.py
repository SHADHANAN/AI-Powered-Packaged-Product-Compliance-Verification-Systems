"""Compliance Rule Engine for Packaged Commodity Compliance Verification.

Dynamic validation engine that loads Legal Metrology rules configuration and
validates structured product information without hardcoding field-specific checks.
"""
from __future__ import annotations

from enum import Enum
import json
import logging
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# Default path to Legal Metrology rules configuration
DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "legal_metrology_rules.json"


class ValidationStatus(str, Enum):
    """Status outcomes for individual compliance rule checks."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class OverallStatus(str, Enum):
    """Overall compliance outcome for a packaged commodity report."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"


# Common aliases mapping extracted OCR keys to canonical rule fields
DEFAULT_FIELD_ALIASES: Dict[str, List[str]] = {
    "product_name": [
        "product_name",
        "generic_name",
        "common_name",
        "commodity_name",
        "item_name",
        "name",
        "brand_name",
    ],
    "manufacturer_name": [
        "manufacturer_name",
        "manufacturer",
        "packer_name",
        "packer",
        "importer_name",
        "importer",
        "manufactured_by",
        "packed_by",
        "imported_by",
        "company_name",
    ],
    "complete_address": [
        "complete_address",
        "manufacturer_address",
        "packer_address",
        "importer_address",
        "address",
        "physical_address",
        "factory_address",
        "office_address",
    ],
    "net_quantity": [
        "net_quantity",
        "quantity",
        "net_qty",
        "net_weight",
        "net_volume",
        "net_content",
        "weight",
        "volume",
    ],
    "mrp": [
        "mrp",
        "maximum_retail_price",
        "price",
        "retail_price",
        "unit_sale_price",
    ],
    "mfg_date": [
        "mfg_date",
        "packing_date",
        "date_of_manufacture",
        "manufacturing_date",
        "date_of_packing",
        "mfg",
        "pkd_date",
        "pkd",
        "import_date",
        "date_of_import",
    ],
    "customer_care": [
        "customer_care",
        "customer_care_details",
        "consumer_care",
        "consumer_complaint",
        "helpline",
        "toll_free",
        "grievance_contact",
        "contact_details",
        "customer_support",
    ],
    "country_of_origin": [
        "country_of_origin",
        "origin_country",
        "country_of_manufacture",
        "origin",
        "made_in",
        "country_origin",
    ],
}

# Standard Metric & SI Units recognized under Legal Metrology (Packaged Commodities) Rules, 2011
STANDARD_UNITS = {
    # Weight / Mass
    "g", "gm", "gms", "gram", "grams", "kg", "kgs", "kilogram", "kilograms", "mg", "milligram", "milligrams",
    # Volume
    "ml", "millilitre", "millilitres", "milliliter", "milliliters", "l", "ltr", "ltrs", "liter", "liters", "litre", "litres", "cl",
    # Length / Area / Volume
    "m", "metre", "metres", "meter", "meters", "cm", "centimetre", "centimeters", "mm", "millimetre",
    "sq m", "sq cm", "sq mm", "sqm", "sqcm", "m2", "cm2", "cu m", "cu cm", "m3", "cm3",
    # Count / Number
    "n", "u", "unit", "units", "piece", "pieces", "pc", "pcs", "nos", "no", "number", "numbers", "item", "items", "count", "ct", "tablets", "capsules", "sachets", "wipes", "sheets",
}

# Set of domestic indicators
DOMESTIC_ORIGIN_KEYWORDS = {"india", "in", "bharat", "domestic"}


# ---------------------------------------------------------------------------
# Validator Registry & Type Validators
# ---------------------------------------------------------------------------

ValidatorFunc = Callable[[Any, Dict[str, Any], Dict[str, Any]], Tuple[ValidationStatus, str, Optional[str]]]


def _is_empty_or_placeholder(value: Any) -> bool:
    """Check if an extracted value is empty, None, or a placeholder."""
    if value is None:
        return True
    val_str = str(value).strip().lower()
    return val_str in {"", "none", "null", "n/a", "na", "-", "--", "undefined", "not declared", "not available"}


def validate_required(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate that the required field is present and non-empty."""
    rule_name = rule.get("rule_name", "Field")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        msg = rule.get("failure_message") or f"Mandatory declaration '{rule_name}' is missing or empty."
        rec = rule.get("recommendation")
        return status, msg, rec

    return (
        ValidationStatus.PASS,
        f"{rule_name} is declared: '{value}'.",
        None,
    )


def validate_quantity(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate net quantity format and standard Legal Metrology unit symbols."""
    rule_name = rule.get("rule_name", "Net Quantity")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()

    # Pattern extracting numeric value and unit
    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z\s²³/\^0-9]+)?", val_str)
    if not match:
        return (
            ValidationStatus.FAIL,
            f"Invalid quantity format '{val_str}'. Net quantity must contain a positive numeric value and metric unit.",
            rule.get("recommendation") or "Declare net quantity using metric units (e.g., '500 g', '1 L').",
        )

    num_part, unit_part = match.groups()
    try:
        qty_num = float(num_part)
        if qty_num <= 0:
            return (
                ValidationStatus.FAIL,
                f"Net quantity '{val_str}' must be strictly greater than zero.",
                rule.get("recommendation"),
            )
    except ValueError:
        return ValidationStatus.FAIL, f"Unparseable net quantity number: '{num_part}'.", rule.get("recommendation")

    if unit_part:
        clean_unit = unit_part.strip().lower()
        if clean_unit in STANDARD_UNITS or any(clean_unit.startswith(u) for u in STANDARD_UNITS):
            return ValidationStatus.PASS, f"Net quantity validly declared as '{val_str}' with approved unit '{clean_unit}'.", None
        else:
            return (
                ValidationStatus.WARNING,
                f"Net quantity unit '{clean_unit}' in '{val_str}' may not be a standard Legal Metrology SI unit.",
                rule.get("recommendation") or "Use standard metric units such as g, kg, ml, L, or N.",
            )

    return (
        ValidationStatus.PASS,
        f"Net quantity numeric value '{qty_num}' declared.",
        None,
    )


def validate_currency(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate Maximum Retail Price (MRP) currency amount."""
    rule_name = rule.get("rule_name", "Maximum Retail Price")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()

    # Extract price numbers
    clean_val = val_str.replace(",", "")
    match = re.search(r"(\d+(?:\.\d{1,2})?)", clean_val)
    if not match:
        return (
            ValidationStatus.FAIL,
            f"Invalid MRP declaration '{val_str}'. A valid numeric price in INR (₹/Rs) is required.",
            rule.get("recommendation") or "Declare MRP explicitly in the format 'MRP ₹ XX.XX (incl. of all taxes)'.",
        )

    price = float(match.group(1))
    if price <= 0:
        return (
            ValidationStatus.FAIL,
            f"MRP amount '{val_str}' must be greater than zero.",
            rule.get("recommendation"),
        )

    return (
        ValidationStatus.PASS,
        f"MRP validly declared as '{val_str}' (Amount: ₹{price:.2f}).",
        None,
    )


def validate_date(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate manufacturing/packing/import date format."""
    rule_name = rule.get("rule_name", "Date")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()

    # Recognized date formats: MM/YYYY, Month YYYY, DD/MM/YYYY, MM-YY, etc.
    date_patterns = [
        r"^(0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})$",  # MM/YYYY or MM/YY
        r"^(20\d{2})[/\-\.](0?[1-9]|1[0-2])$",        # YYYY/MM
        r"^(0?[1-9]|[12]\d|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})$",  # DD/MM/YYYY
        r"^(20\d{2})[/\-\.](0?[1-9]|1[0-2])[/\-\.](0?[1-9]|[12]\d|3[01])$",        # YYYY-MM-DD
        r"(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[,\s\-\/]+(20\d{2}|\d{2})$",  # Aug 2026
        r"(?i)^(20\d{2})[,\s\-\/]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*$",        # 2026 Aug
        r"(?i)^[0-9]{1,2}[/\-\s]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[/\-\s]+(20\d{2}|\d{2})$",  # 15 Aug 2026
    ]

    for pat in date_patterns:
        if re.search(pat, val_str):
            return ValidationStatus.PASS, f"{rule_name} validly declared as '{val_str}'.", None

    return (
        ValidationStatus.WARNING,
        f"{rule_name} '{val_str}' is present but could not be parsed into a standard MM/YYYY or Month YYYY format.",
        rule.get("recommendation") or "Format date as MM/YYYY (e.g., '08/2026') or Month YYYY (e.g., 'Aug 2026').",
    )


def validate_address(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate physical / postal address completeness."""
    rule_name = rule.get("rule_name", "Complete Address")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()

    if len(val_str) < 6:
        return (
            ValidationStatus.WARNING,
            f"Declared address '{val_str}' is too brief and may not provide sufficient location details for postal communication.",
            rule.get("recommendation") or "Provide full address including premises, city, state, and PIN code.",
        )

    return (
        ValidationStatus.PASS,
        f"{rule_name} declared: '{val_str}'.",
        None,
    )


def validate_contact(
    value: Any,
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Tuple[ValidationStatus, str, Optional[str]]:
    """Validate consumer care / contact details (phone, email, address, or helpline)."""
    rule_name = rule.get("rule_name", "Customer Care Details")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()

    # Detect phone number, email address, or helpline keywords
    has_phone = bool(re.search(r"(?:1800|\+?\d[\d\s\-]{6,14}\d)", val_str))
    has_email = bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", val_str))
    has_contact_keywords = any(k in val_str.lower() for k in ["care", "toll free", "helpline", "support", "complaint", "feedback", "email", "tel", "phone"])

    if has_phone or has_email or has_contact_keywords or len(val_str) >= 8:
        return (
            ValidationStatus.PASS,
            f"{rule_name} validly declared: '{val_str}'.",
            None,
        )

    return (
        ValidationStatus.WARNING,
        f"Customer care details '{val_str}' may be incomplete. Recommended to provide both email and phone.",
        rule.get("recommendation") or "Provide reachable phone number and email address for consumer grievance redressal.",
    )


# ---------------------------------------------------------------------------
# Compliance Engine Class
# ---------------------------------------------------------------------------

class ComplianceEngine:
    """Configurable Legal Metrology rule validation engine.

    Loads validation rules dynamically and validates structured product data
    extracted from OCR or manual inputs without hardcoded field conditionals.
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
        field_aliases: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize the Compliance Engine.

        Args:
            rules_path: Optional path to JSON rules file. Defaults to legal_metrology_rules.json.
            rules_data: Optional list of rule dictionaries (overrides file loading).
            field_aliases: Optional custom field aliases mapping.
        """
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self.field_aliases = field_aliases or DEFAULT_FIELD_ALIASES
        self._validators: Dict[str, ValidatorFunc] = {
            "required": validate_required,
            "quantity": validate_quantity,
            "currency": validate_currency,
            "date": validate_date,
            "address": validate_address,
            "contact": validate_contact,
        }

        if rules_data is not None:
            self.rules = rules_data
        else:
            self.rules = self._load_rules()

        logger.info("ComplianceEngine initialized with %d rules.", len(self.rules))

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load and parse rules JSON file."""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules configuration file not found at: {self.rules_path}")

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("rules", [])
        except Exception as exc:
            logger.error("Failed to load rules JSON from %s: %s", self.rules_path, exc)
            raise

    def register_validator(self, validation_type: str, validator_func: ValidatorFunc) -> None:
        """Register or override a validation type function dynamically.

        Args:
            validation_type: Name of validation type (e.g., 'barcode', 'regex').
            validator_func: Callable with signature (value, rule, context) -> (status, message, recommendation).
        """
        self._validators[validation_type.lower()] = validator_func
        logger.info("Registered custom validator for type '%s'", validation_type)

    def extract_field_value(self, field_name: str, product_data: Dict[str, Any]) -> Any:
        """Dynamically retrieve field value from product_data using canonical name and aliases.

        Args:
            field_name: The canonical field name defined in the rule.
            product_data: Extracted product key-value pairs.

        Returns:
            The extracted field value if present, else None.
        """
        # 1. Direct match
        if field_name in product_data:
            return product_data[field_name]

        # 2. Case-insensitive direct match
        lower_data = {str(k).strip().lower(): v for k, v in product_data.items()}
        if field_name.lower() in lower_data:
            return lower_data[field_name.lower()]

        # 3. Alias matches
        aliases = self.field_aliases.get(field_name, [])
        for alias in aliases:
            if alias in product_data:
                return product_data[alias]
            alias_lower = alias.lower()
            if alias_lower in lower_data:
                return lower_data[alias_lower]

        return None

    def is_imported_product(self, product_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """Determine whether the product is imported based on origin or flags."""
        ctx = context or {}

        # 1. Check explicit flags in context or product_data
        for key in ["is_imported", "imported"]:
            if key in ctx:
                val = ctx[key]
                return str(val).strip().lower() in {"true", "1", "yes"}
            if key in product_data:
                val = product_data[key]
                return str(val).strip().lower() in {"true", "1", "yes"}

        # 2. Check product_type
        prod_type = str(ctx.get("product_type") or product_data.get("product_type") or "").strip().lower()
        if prod_type == "imported":
            return True
        if prod_type == "domestic":
            return False

        # 3. Check country of origin value
        coo_val = self.extract_field_value("country_of_origin", product_data)
        if coo_val is not None and str(coo_val).strip():
            origin_clean = str(coo_val).strip().lower()
            if origin_clean not in DOMESTIC_ORIGIN_KEYWORDS:
                return True
            return False

        # 4. Check presence of importer name/address
        if "importer" in product_data or "importer_name" in product_data or "import_date" in product_data:
            return True

        # Default assumption: domestic unless declared imported
        return False

    def is_rule_applicable(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a rule is applicable to the current product."""
        applicable_to = str(rule.get("applicable_to", "all")).strip().lower()

        if applicable_to == "all":
            return True

        is_imported = self.is_imported_product(product_data, context)

        if applicable_to == "imported":
            return is_imported

        if applicable_to == "domestic":
            return not is_imported

        return True

    def validate_rule(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate a single dynamic rule against the product data.

        Args:
            rule: Rule definition dictionary.
            product_data: Extracted OCR fields dictionary.
            context: Optional contextual parameters.

        Returns:
            Dictionary with rule_id, rule_name, status, message, recommendation.
        """
        rule_id = rule.get("rule_id", "UNKNOWN")
        rule_name = rule.get("rule_name", "Unknown Rule")
        field = rule.get("field", "")
        validation_type = str(rule.get("validation_type", "required")).strip().lower()

        # Check applicability
        if not self.is_rule_applicable(rule, product_data, context):
            applicable_to = rule.get("applicable_to", "")
            return {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "status": ValidationStatus.NOT_APPLICABLE.value,
                "message": f"Rule is not applicable (applies only to '{applicable_to}' commodities).",
                "recommendation": None,
            }

        # Dynamically retrieve value
        value = self.extract_field_value(field, product_data)

        # Dispatch validator by type
        validator = self._validators.get(validation_type, self._validators["required"])
        status, msg, rec = validator(value, rule, context or {})

        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "status": status.value if isinstance(status, ValidationStatus) else str(status),
            "message": msg,
            "recommendation": rec,
        }

    def validate(
        self,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute all dynamic compliance rules against the given product data.

        Args:
            product_data: Extracted product fields dictionary.
            context: Optional contextual dictionary (e.g. is_imported, category).

        Returns:
            Complete validation report with overall_status, results, passed, failed,
            warnings, and not_applicable counts.
        """
        results: List[Dict[str, Any]] = []
        passed = 0
        failed = 0
        warnings = 0
        not_applicable = 0

        logger.debug("Validating product data with %d fields against %d rules.", len(product_data), len(self.rules))

        for rule in self.rules:
            result = self.validate_rule(rule, product_data, context)
            results.append(result)

            status = result.get("status")
            if status == ValidationStatus.PASS.value:
                passed += 1
            elif status == ValidationStatus.FAIL.value:
                failed += 1
            elif status == ValidationStatus.WARNING.value:
                warnings += 1
            elif status == ValidationStatus.NOT_APPLICABLE.value:
                not_applicable += 1

        # Determine overall status
        if failed > 0:
            overall_status = OverallStatus.NON_COMPLIANT.value
        elif warnings > 0:
            overall_status = OverallStatus.PARTIALLY_COMPLIANT.value
        else:
            overall_status = OverallStatus.COMPLIANT.value

        report = {
            "overall_status": overall_status,
            "results": results,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "not_applicable": not_applicable,
        }

        logger.info(
            "Validation complete: %s (Passed: %d, Failed: %d, Warnings: %d, N/A: %d)",
            overall_status,
            passed,
            failed,
            warnings,
            not_applicable,
        )
        return report


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

_default_engine: Optional[ComplianceEngine] = None


def get_compliance_engine() -> ComplianceEngine:
    """Return a singleton instance of ComplianceEngine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = ComplianceEngine()
    return _default_engine


def verify_compliance(
    product_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate product data against Legal Metrology rules.

    Args:
        product_data: Structured key-value dictionary of product declarations.
        context: Optional context dictionary.

    Returns:
        Structured compliance report dictionary.
    """
    engine = get_compliance_engine()
    return engine.validate(product_data, context)
