"""Compliance Rule Engine for Packaged Commodity Compliance Verification.

Dynamic validation engine that loads Legal Metrology rules configuration and
validates structured product information using an intelligent four-state validation model
(PASS, WARNING, FAIL, NOT_APPLICABLE) and weighted scoring engine.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from compliance.explanation import ViolationExplanationEngine, get_explanation_engine
from compliance.recommendation import RecommendationEngine, get_recommendation_engine
from compliance.scorer import ComplianceScorer, get_compliance_scorer
from compliance.status import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    ComplianceStatus,
    OverallComplianceStatus,
    OverallStatus,
    RuleEvaluationResult,
    StatusEvaluator,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

# Default path to Legal Metrology rules configuration
DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "legal_metrology_rules.json"


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
    "importer_details": [
        "importer_details",
        "importer",
        "importer_name",
        "importer_address",
        "imported_by",
        "imported_by_name",
        "importer_identity",
    ],
    "expiry_date": [
        "expiry_date",
        "best_before",
        "use_by",
        "exp_date",
        "exp",
        "use_before",
        "shelf_life",
        "expiry",
    ],
    "technical_specs": [
        "technical_specs",
        "model_number",
        "model_name",
        "model",
        "voltage",
        "power_rating",
        "specs",
        "rating",
        "specifications",
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
                f"Net quantity unit '{clean_unit}' in '{val_str}' may not be a standard Legal Metrology SI unit. Manual verification recommended.",
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
        f"{rule_name} '{val_str}' is present but could not be parsed into a standard MM/YYYY or Month YYYY format. Manual verification recommended.",
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
            f"Declared address '{val_str}' is too brief and may not provide sufficient location details for postal communication. Manual verification recommended.",
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
    extracted from OCR or manual inputs using an intelligent four-state validation
    model (PASS, WARNING, FAIL, NOT_APPLICABLE) and weighted scoring engine.
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
        field_aliases: Optional[Dict[str, List[str]]] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize the Compliance Engine.

        Args:
            rules_path: Optional path to JSON rules file. Defaults to legal_metrology_rules.json.
            rules_data: Optional list of rule dictionaries (overrides file loading).
            field_aliases: Optional custom field aliases mapping.
            confidence_threshold: Default OCR confidence threshold (0.0 to 1.0).
            custom_weights: Optional rule weights overrides.
        """
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self.field_aliases = field_aliases or DEFAULT_FIELD_ALIASES
        self.confidence_threshold = confidence_threshold
        self.status_evaluator = StatusEvaluator(default_confidence_threshold=confidence_threshold)
        self.scorer = ComplianceScorer(rules_path=self.rules_path, custom_weights=custom_weights)
        self.explanation_engine = ViolationExplanationEngine(rules_path=self.rules_path, rules_data=rules_data)
        self.recommendation_engine = RecommendationEngine(rules_path=self.rules_path, rules_data=rules_data)

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

        logger.info("ComplianceEngine initialized with %d rules (Confidence threshold: %.2f).", len(self.rules), self.confidence_threshold)

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

    def extract_field_and_confidence(
        self,
        field_name: str,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Optional[float]]:
        """Dynamically retrieve field value and OCR confidence from product_data or context.

        Supports:
        - Plain key-value mapping: `{"product_name": "ABC Tea"}`
        - Object with value & confidence: `{"mrp": {"value": "₹120", "confidence": 0.65}}`
        - Context confidences dictionary: `context={"confidences": {"mrp": 0.65}}`

        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        ctx = context or {}
        confidences_map = ctx.get("confidences") or ctx.get("field_confidences") or {}

        def _unpack_val_conf(raw_val: Any, key_name: str) -> Tuple[Any, Optional[float]]:
            if isinstance(raw_val, dict):
                val = raw_val.get("value") or raw_val.get("field_value") or raw_val.get("text")
                conf = raw_val.get("confidence") or raw_val.get("score")
                if conf is not None:
                    try:
                        conf = float(conf)
                    except (ValueError, TypeError):
                        conf = None
                return val, conf
            
            # Check if raw_val has attribute confidence/field_value
            if hasattr(raw_val, "field_value") or hasattr(raw_val, "confidence"):
                val = getattr(raw_val, "field_value", None)
                conf = getattr(raw_val, "confidence", None)
                return val, conf

            # Check context confidence map
            conf = confidences_map.get(key_name)
            if conf is not None:
                try:
                    conf = float(conf)
                except (ValueError, TypeError):
                    conf = None
            return raw_val, conf

        # 1. Direct match
        if field_name in product_data:
            return _unpack_val_conf(product_data[field_name], field_name)

        # 2. Case-insensitive direct match
        lower_data = {str(k).strip().lower(): (k, v) for k, v in product_data.items()}
        if field_name.lower() in lower_data:
            orig_k, val = lower_data[field_name.lower()]
            return _unpack_val_conf(val, orig_k)

        # 3. Alias matches
        aliases = self.field_aliases.get(field_name, [])
        for alias in aliases:
            if alias in product_data:
                return _unpack_val_conf(product_data[alias], alias)
            alias_lower = alias.lower()
            if alias_lower in lower_data:
                orig_k, val = lower_data[alias_lower]
                return _unpack_val_conf(val, orig_k)

        return None, None

    def is_imported_product(self, product_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """Determine whether the product is imported based on origin, categories, or flags."""
        ctx = context or {}

        # 1. Check explicit flags in context or product_data
        for key in ["is_imported", "imported"]:
            if key in ctx:
                val = ctx[key]
                return str(val).strip().lower() in {"true", "1", "yes"}
            if key in product_data:
                val = product_data[key]
                return str(val).strip().lower() in {"true", "1", "yes"}

        # 2. Check product_category / product_type / category for 'imported' or 'domestic'
        for key in ["product_category", "product_type", "category", "categories"]:
            raw_cat = ctx.get(key) or product_data.get(key)
            if raw_cat:
                if isinstance(raw_cat, list):
                    cat_list = [str(x).strip().lower() for x in raw_cat]
                    if "imported" in cat_list:
                        return True
                    if "domestic" in cat_list:
                        return False
                else:
                    cat_str = str(raw_cat).strip().lower()
                    if "imported" in cat_str:
                        return True
                    if "domestic" in cat_str:
                        return False

        # 3. Check country of origin value
        coo_val, _ = self.extract_field_and_confidence("country_of_origin", product_data, context)
        if coo_val is not None and str(coo_val).strip():
            origin_clean = str(coo_val).strip().lower()
            if origin_clean not in DOMESTIC_ORIGIN_KEYWORDS:
                return True
            return False

        # 4. Check presence of importer name/address/details
        if (
            "importer" in product_data
            or "importer_name" in product_data
            or "importer_details" in product_data
            or "import_date" in product_data
        ):
            return True

        # Default assumption: domestic unless declared imported
        return False

    def get_active_product_scopes(
        self,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Set[str]:
        """Extract the complete set of applicable category scopes for the product.

        Resolves general, origin-based ('imported'/'domestic'), and sector-specific
        categories ('food', 'beverage', 'cosmetic', 'electronics', 'medicine', etc.).
        """
        scopes: Set[str] = {"all"}
        ctx = context or {}

        # 1. Resolve Origin Scope
        if self.is_imported_product(product_data, context):
            scopes.add("imported")
        else:
            scopes.add("domestic")

        # 2. Resolve Sector & Custom Categories
        for source in [ctx, product_data]:
            for key in ["product_category", "category", "categories", "product_type", "commodity_type", "sector"]:
                if key in source and source[key] is not None:
                    raw_val = source[key]
                    if isinstance(raw_val, (list, tuple, set)):
                        for item in raw_val:
                            if item is not None:
                                scopes.add(str(item).strip().lower())
                    elif isinstance(raw_val, str):
                        # Split by comma, slash, or semicolon if multiple categories provided
                        for part in re.split(r"[,;/|]", raw_val):
                            clean_part = part.strip().lower()
                            if clean_part:
                                scopes.add(clean_part)

        return scopes

    def is_rule_applicable(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a rule is applicable to the current product category and origin."""
        applicable_to = rule.get("applicable_to", "all")
        active_scopes = self.get_active_product_scopes(product_data, context)

        # Handle list of applicable categories
        if isinstance(applicable_to, (list, tuple, set)):
            clean_targets = {str(x).strip().lower() for x in applicable_to if x is not None}
            if "all" in clean_targets:
                return True
            return bool(clean_targets & active_scopes)

        # Handle single string category
        app_str = str(applicable_to).strip().lower()
        if app_str == "all":
            return True

        return app_str in active_scopes

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
            context: Optional contextual parameters (e.g. confidence_threshold).

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
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                status=ValidationStatus.NOT_APPLICABLE,
                message=f"Rule is not applicable (applies only to '{applicable_to}' commodities).",
                recommendation=None,
                field=field,
            ).to_dict()

        # Dynamically retrieve value & confidence
        value, confidence = self.extract_field_and_confidence(field, product_data, context)

        # Dispatch validator by type
        validator = self._validators.get(validation_type, self._validators["required"])
        base_status, base_msg, base_rec = validator(value, rule, context or {})

        # Intelligent status evaluation factoring confidence and readability
        final_status, final_msg, final_rec = self.status_evaluator.evaluate_status(
            base_status=base_status,
            base_message=base_msg,
            base_recommendation=base_rec,
            field_value=value,
            confidence=confidence,
            rule=rule,
            context=context,
        )

        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            status=final_status,
            message=final_msg,
            recommendation=final_rec,
            confidence=confidence,
            field=field,
            actual_value=value,
        ).to_dict()

    def validate(
        self,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute all dynamic compliance rules against the given product data.

        Args:
            product_data: Extracted product fields dictionary.
            context: Optional contextual dictionary (e.g. is_imported, confidence_threshold).

        Returns:
            Complete validation report with compliance_score, overall_status, risk_level,
            results, passed, failed, warnings, and not_applicable counts.
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

        # Calculate weighted scoring & risk assessment
        score_report = self.scorer.calculate_score(results)
        explanations = self.explanation_engine.generate_explanations(results)
        recommendations = self.recommendation_engine.generate_recommendations(results)

        report = {
            "compliance_score": score_report["compliance_score"],
            "overall_status": score_report["overall_status"],
            "risk_level": score_report["risk_level"],
            "total_applicable_weight": score_report["total_applicable_weight"],
            "earned_weight": score_report["earned_weight"],
            "results": results,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "not_applicable": not_applicable,
            "breakdown": score_report["breakdown"],
            "explanations": explanations,
            "recommendations": recommendations,
        }

        logger.info(
            "Validation complete: Score: %.1f%% (%s, Risk: %s) [Passed: %d, Failed: %d, Warnings: %d, N/A: %d]",
            report["compliance_score"],
            report["overall_status"],
            report["risk_level"],
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


def get_compliance_engine(confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> ComplianceEngine:
    """Return a singleton instance of ComplianceEngine."""
    global _default_engine
    if _default_engine is None or _default_engine.confidence_threshold != confidence_threshold:
        _default_engine = ComplianceEngine(confidence_threshold=confidence_threshold)
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
