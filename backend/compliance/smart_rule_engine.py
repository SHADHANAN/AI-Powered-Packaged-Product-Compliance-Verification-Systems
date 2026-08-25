"""Smart Compliance Rule Engine for Legal Metrology Verification.

A fully dynamic, metadata-driven rule engine supporting rule versions, weights,
priorities, sectoral categories, effective dates, dependency graphs, and execution telemetry.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
import logging
from pathlib import Path
import re
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from compliance.explanation import ViolationExplanationEngine, get_explanation_engine
from compliance.recommendation import RecommendationEngine, get_recommendation_engine
from compliance.rules import DEFAULT_RULES_PATH, get_rules_list
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

# Priority sorting weights (Lower value = higher evaluation order)
PRIORITY_ORDER = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}

DEFAULT_FIELD_ALIASES: Dict[str, List[str]] = {
    "product_name": ["product_name", "generic_name", "common_name", "commodity_name", "item_name", "name", "brand_name"],
    "manufacturer_name": ["manufacturer_name", "manufacturer", "packer_name", "packer", "importer_name", "importer", "manufactured_by", "packed_by", "imported_by", "company_name"],
    "complete_address": ["complete_address", "manufacturer_address", "packer_address", "importer_address", "address", "physical_address", "factory_address", "office_address"],
    "net_quantity": ["net_quantity", "quantity", "net_qty", "net_weight", "net_volume", "net_content", "weight", "volume"],
    "mrp": ["mrp", "maximum_retail_price", "price", "retail_price", "unit_sale_price"],
    "mfg_date": ["mfg_date", "packing_date", "date_of_manufacture", "manufacturing_date", "date_of_packing", "mfg", "pkd_date", "pkd", "import_date", "date_of_import"],
    "customer_care": ["customer_care", "customer_care_details", "consumer_care", "consumer_complaint", "helpline", "toll_free", "grievance_contact", "contact_details", "customer_support"],
    "country_of_origin": ["country_of_origin", "origin_country", "country_of_manufacture", "origin", "made_in", "country_origin"],
    "importer_details": ["importer_details", "importer", "importer_name", "importer_address", "imported_by", "imported_by_name", "importer_identity"],
    "expiry_date": ["expiry_date", "best_before", "use_by", "exp_date", "exp", "use_before", "shelf_life", "expiry"],
    "technical_specs": ["technical_specs", "model_number", "model_name", "model", "voltage", "power_rating", "specs", "rating", "specifications"],
}

STANDARD_UNITS = {
    "g", "gm", "gms", "gram", "grams", "kg", "kgs", "kilogram", "kilograms", "mg", "milligram", "milligrams",
    "ml", "millilitre", "millilitres", "milliliter", "milliliters", "l", "ltr", "ltrs", "liter", "liters", "litre", "litres", "cl",
    "m", "metre", "metres", "meter", "meters", "cm", "centimetre", "centimeters", "mm", "millimetre",
    "sq m", "sq cm", "sq mm", "sqm", "sqcm", "m2", "cm2", "cu m", "cu cm", "m3", "cm3",
    "n", "u", "unit", "units", "piece", "pieces", "pc", "pcs", "nos", "no", "number", "numbers", "item", "items", "count", "ct", "tablets", "capsules", "sachets", "wipes", "sheets",
}

DOMESTIC_ORIGIN_KEYWORDS = {"india", "in", "bharat", "domestic"}

ValidatorFunc = Callable[[Any, Dict[str, Any], Dict[str, Any]], Tuple[ValidationStatus, str, Optional[str]]]


@dataclass
class RuleExecutionLog:
    """Execution telemetry record for a single compliance rule validation."""

    rule_id: str
    rule_name: str
    category: str
    priority: str
    status: str
    execution_time_ms: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Standard Type Validators (Generic & Reusable)
# ---------------------------------------------------------------------------

def _is_empty_or_placeholder(value: Any) -> bool:
    if value is None:
        return True
    val_str = str(value).strip().lower()
    return val_str in {"", "none", "null", "n/a", "na", "-", "--", "undefined", "not declared", "not available"}


def validate_required(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Field")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"Mandatory declaration '{rule_name}' is missing.", rule.get("recommendation")

    return ValidationStatus.PASS, f"{rule_name} is declared: '{value}'.", None


def validate_quantity(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Net Quantity")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z\s²³/\^0-9]+)?", val_str)
    if not match:
        return ValidationStatus.FAIL, f"Invalid quantity format '{val_str}'. Must include positive number and metric unit.", rule.get("recommendation")

    num_part, unit_part = match.groups()
    try:
        qty_num = float(num_part)
        if qty_num <= 0:
            return ValidationStatus.FAIL, f"Net quantity '{val_str}' must be strictly greater than zero.", rule.get("recommendation")
    except ValueError:
        return ValidationStatus.FAIL, f"Unparseable net quantity: '{num_part}'.", rule.get("recommendation")

    if unit_part:
        clean_unit = unit_part.strip().lower()
        if clean_unit in STANDARD_UNITS or any(clean_unit.startswith(u) for u in STANDARD_UNITS):
            return ValidationStatus.PASS, f"Net quantity validly declared as '{val_str}' with approved unit '{clean_unit}'.", None
        else:
            return ValidationStatus.WARNING, f"Net quantity unit '{clean_unit}' in '{val_str}' may not be a standard Legal Metrology SI unit.", rule.get("recommendation")

    return ValidationStatus.PASS, f"Net quantity declared: '{qty_num}'.", None


def validate_currency(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Maximum Retail Price")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()
    clean_val = val_str.replace(",", "")
    match = re.search(r"(\d+(?:\.\d{1,2})?)", clean_val)
    if not match:
        return ValidationStatus.FAIL, f"Invalid MRP declaration '{val_str}'. A valid numeric price in INR is required.", rule.get("recommendation")

    price = float(match.group(1))
    if price <= 0:
        return ValidationStatus.FAIL, f"MRP amount '{val_str}' must be greater than zero.", rule.get("recommendation")

    return ValidationStatus.PASS, f"MRP validly declared as '{val_str}' (Amount: ₹{price:.2f}).", None


def validate_date(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Date")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()
    date_patterns = [
        r"^(0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})$",
        r"^(20\d{2})[/\-\.](0?[1-9]|1[0-2])$",
        r"^(0?[1-9]|[12]\d|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})$",
        r"^(20\d{2})[/\-\.](0?[1-9]|1[0-2])[/\-\.](0?[1-9]|[12]\d|3[01])$",
        r"(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[,\s\-\/]+(20\d{2}|\d{2})$",
        r"(?i)^(20\d{2})[,\s\-\/]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*$",
        r"(?i)^[0-9]{1,2}[/\-\s]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[/\-\s]+(20\d{2}|\d{2})$",
    ]

    for pat in date_patterns:
        if re.search(pat, val_str):
            return ValidationStatus.PASS, f"{rule_name} validly declared as '{val_str}'.", None

    return ValidationStatus.WARNING, f"{rule_name} '{val_str}' is present but could not be parsed into a standard date format.", rule.get("recommendation")


def validate_address(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Complete Address")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()
    if len(val_str) < 6:
        return ValidationStatus.WARNING, f"Declared address '{val_str}' is too brief for postal communication.", rule.get("recommendation")

    return ValidationStatus.PASS, f"{rule_name} declared: '{val_str}'.", None


def validate_contact(value: Any, rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[ValidationStatus, str, Optional[str]]:
    rule_name = rule.get("rule_name", "Customer Care Details")
    mandatory = rule.get("mandatory", True)

    if _is_empty_or_placeholder(value):
        status = ValidationStatus.FAIL if mandatory else ValidationStatus.WARNING
        return status, rule.get("failure_message") or f"{rule_name} declaration is missing.", rule.get("recommendation")

    val_str = str(value).strip()
    has_phone = bool(re.search(r"(?:1800|\+?\d[\d\s\-]{6,14}\d)", val_str))
    has_email = bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", val_str))
    has_keywords = any(k in val_str.lower() for k in ["care", "toll free", "helpline", "support", "complaint", "feedback", "email", "tel", "phone"])

    if has_phone or has_email or has_keywords or len(val_str) >= 8:
        return ValidationStatus.PASS, f"{rule_name} validly declared: '{val_str}'.", None

    return ValidationStatus.WARNING, f"Customer care details '{val_str}' may be incomplete.", rule.get("recommendation")


# ---------------------------------------------------------------------------
# Smart Rule Engine Implementation
# ---------------------------------------------------------------------------

class SmartRuleEngine:
    """Smart Rule Engine for Legal Metrology Packaged Commodities Verification.

    Features:
    - Completely dynamic JSON rule ingestion
    - Rule versioning, priorities, weights, categories, and effective date filtering
    - Declarative dependency and scope evaluation
    - Detailed execution timing logs and audit telemetry
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        custom_weights: Optional[Dict[str, float]] = None,
        field_aliases: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Initialize the Smart Rule Engine."""
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self.confidence_threshold = confidence_threshold
        self.field_aliases = field_aliases or DEFAULT_FIELD_ALIASES

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

        self._sort_rules_by_priority()
        logger.info("SmartRuleEngine loaded %d rules from %s.", len(self.rules), self.rules_path)

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load and parse dynamic rules JSON."""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rule configuration file not found at: {self.rules_path}")

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("rules", [])
        except Exception as exc:
            logger.error("Failed to load rules from %s: %s", self.rules_path, exc)
            raise

    def _sort_rules_by_priority(self) -> None:
        """Sort rules dynamically based on priority."""
        def _get_sort_key(rule: Dict[str, Any]) -> int:
            pri = str(rule.get("priority", "medium")).lower()
            return PRIORITY_ORDER.get(pri, 3)

        self.rules.sort(key=_get_sort_key)

    def register_validator(self, validation_type: str, validator_func: ValidatorFunc) -> None:
        """Register or override a custom validation type dynamically."""
        self._validators[validation_type.lower()] = validator_func
        logger.info("Registered smart validator for type '%s'", validation_type)

    def extract_field_and_confidence(
        self,
        field_name: str,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Optional[float]]:
        """Retrieve field value and OCR confidence dynamically."""
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

            if hasattr(raw_val, "field_value") or hasattr(raw_val, "confidence"):
                return getattr(raw_val, "field_value", None), getattr(raw_val, "confidence", None)

            conf = confidences_map.get(key_name)
            if conf is not None:
                try:
                    conf = float(conf)
                except (ValueError, TypeError):
                    conf = None
            return raw_val, conf

        if field_name in product_data:
            return _unpack_val_conf(product_data[field_name], field_name)

        lower_data = {str(k).strip().lower(): (k, v) for k, v in product_data.items()}
        if field_name.lower() in lower_data:
            orig_k, val = lower_data[field_name.lower()]
            return _unpack_val_conf(val, orig_k)

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

        for key in ["is_imported", "imported"]:
            if key in ctx and str(ctx[key]).strip().lower() in {"true", "1", "yes"}:
                return True
            if key in product_data and str(product_data[key]).strip().lower() in {"true", "1", "yes"}:
                return True

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

        coo_val, _ = self.extract_field_and_confidence("country_of_origin", product_data, context)
        if coo_val is not None and str(coo_val).strip():
            if str(coo_val).strip().lower() not in DOMESTIC_ORIGIN_KEYWORDS:
                return True
            return False

        if any(k in product_data for k in ["importer", "importer_name", "importer_details", "import_date"]):
            return True

        return False

    def get_active_product_scopes(
        self,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Set[str]:
        """Extract the complete set of applicable category scopes for the product."""
        scopes: Set[str] = {"all"}
        ctx = context or {}

        if self.is_imported_product(product_data, context):
            scopes.add("imported")
        else:
            scopes.add("domestic")

        for source in [ctx, product_data]:
            for key in ["product_category", "category", "categories", "product_type", "commodity_type", "sector"]:
                if key in source and source[key] is not None:
                    raw_val = source[key]
                    if isinstance(raw_val, (list, tuple, set)):
                        for item in raw_val:
                            if item is not None:
                                scopes.add(str(item).strip().lower())
                    elif isinstance(raw_val, str):
                        for part in re.split(r"[,;/|]", raw_val):
                            clean_part = part.strip().lower()
                            if clean_part:
                                scopes.add(clean_part)

        return scopes

    def check_rule_dependencies(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        evaluated_results: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Verify if all rule dependencies are satisfied."""
        deps = rule.get("dependencies", [])
        if not deps:
            return True

        active_scopes = self.get_active_product_scopes(product_data, context)
        prev_results = evaluated_results or {}

        for dep in deps:
            if isinstance(dep, str):
                # Depends on another rule being PASS or evaluated
                if dep in prev_results and prev_results[dep] == ValidationStatus.FAIL.value:
                    return False
            elif isinstance(dep, dict):
                dep_type = dep.get("type", "scope")
                if dep_type == "scope":
                    req = dep.get("requires")
                    if req and str(req).lower() not in active_scopes:
                        return False
                    req_any = dep.get("requires_any", [])
                    if req_any and not any(str(x).lower() in active_scopes for x in req_any):
                        return False
                elif dep_type == "rule":
                    parent_rule = dep.get("rule_id")
                    expected_status = dep.get("status")
                    if parent_rule and expected_status and prev_results.get(parent_rule) != expected_status:
                        return False

        return True

    def is_rule_applicable(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        evaluated_results: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Verify category applicability, dependencies, and effective dates."""
        # 1. Effective date check
        effective_date_str = rule.get("effective_date")
        if effective_date_str:
            try:
                eff_date = date.fromisoformat(effective_date_str)
                if eff_date > date.today():
                    return False
            except ValueError:
                pass

        # 2. Scope / Category applicability
        applicable_to = rule.get("applicable_to", "all")
        active_scopes = self.get_active_product_scopes(product_data, context)

        if isinstance(applicable_to, (list, tuple, set)):
            clean_targets = {str(x).strip().lower() for x in applicable_to if x is not None}
            if "all" not in clean_targets and not (clean_targets & active_scopes):
                return False
        else:
            app_str = str(applicable_to).strip().lower()
            if app_str != "all" and app_str not in active_scopes:
                return False

        # 3. Dependencies check
        if not self.check_rule_dependencies(rule, product_data, context, evaluated_results):
            return False

        return True

    def validate_rule(
        self,
        rule: Dict[str, Any],
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        evaluated_results: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, Any], RuleExecutionLog]:
        """Validate a single dynamic rule and record execution telemetry."""
        start_time = time.perf_counter()

        rule_id = rule.get("rule_id", "UNKNOWN")
        rule_name = rule.get("rule_name", "Unknown Rule")
        field = rule.get("field", "")
        category = rule.get("category", "General")
        priority = rule.get("priority", "Medium")
        validation_type = str(rule.get("validation_type", "required")).strip().lower()

        # Applicability & dependency evaluation
        if not self.is_rule_applicable(rule, product_data, context, evaluated_results):
            applicable_to = rule.get("applicable_to", "")
            elapsed = (time.perf_counter() - start_time) * 1000.0

            res = RuleEvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                status=ValidationStatus.NOT_APPLICABLE,
                message=f"Rule is not applicable to current product category (scope: {applicable_to}).",
                recommendation=None,
                field=field,
            ).to_dict()

            log_entry = RuleExecutionLog(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                priority=priority,
                status=ValidationStatus.NOT_APPLICABLE.value,
                execution_time_ms=elapsed,
                message=res["message"],
            )
            return res, log_entry

        # Extract value & confidence
        value, confidence = self.extract_field_and_confidence(field, product_data, context)

        # Dispatch validator dynamically
        validator = self._validators.get(validation_type, self._validators["required"])
        base_status, base_msg, base_rec = validator(value, rule, context or {})

        # Status evaluation factoring OCR confidence & readability
        final_status, final_msg, final_rec = self.status_evaluator.evaluate_status(
            base_status=base_status,
            base_message=base_msg,
            base_recommendation=base_rec,
            field_value=value,
            confidence=confidence,
            rule=rule,
            context=context,
        )

        elapsed = (time.perf_counter() - start_time) * 1000.0

        res = RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            status=final_status,
            message=final_msg,
            recommendation=final_rec,
            confidence=confidence,
            field=field,
            actual_value=value,
        ).to_dict()

        log_entry = RuleExecutionLog(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            priority=priority,
            status=final_status.value if isinstance(final_status, ValidationStatus) else str(final_status),
            execution_time_ms=elapsed,
            message=final_msg,
        )
        return res, log_entry

    def validate(
        self,
        product_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the smart compliance verification pipeline against product data."""
        overall_start = time.perf_counter()

        results: List[Dict[str, Any]] = []
        execution_logs: List[Dict[str, Any]] = []
        evaluated_statuses: Dict[str, str] = {}

        passed = 0
        failed = 0
        warnings = 0
        not_applicable = 0

        for rule in self.rules:
            result, exec_log = self.validate_rule(rule, product_data, context, evaluated_statuses)
            results.append(result)
            execution_logs.append(exec_log.to_dict())

            status = result.get("status")
            evaluated_statuses[rule.get("rule_id", "")] = status

            if status == ValidationStatus.PASS.value:
                passed += 1
            elif status == ValidationStatus.FAIL.value:
                failed += 1
            elif status == ValidationStatus.WARNING.value:
                warnings += 1
            elif status == ValidationStatus.NOT_APPLICABLE.value:
                not_applicable += 1

        # Calculate scoring, risk, explanations, and recommendations
        score_report = self.scorer.calculate_score(results)
        explanations = self.explanation_engine.generate_explanations(results)
        recommendations = self.recommendation_engine.generate_recommendations(results)

        total_elapsed = (time.perf_counter() - overall_start) * 1000.0

        report = {
            "overall_status": score_report["overall_status"],
            "compliance_score": score_report["compliance_score"],
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
            "execution_logs": execution_logs,
            "total_execution_time_ms": round(total_elapsed, 2),
        }

        return report


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_smart_engine: Optional[SmartRuleEngine] = None


def get_smart_rule_engine() -> SmartRuleEngine:
    """Return a singleton instance of SmartRuleEngine."""
    global _default_smart_engine
    if _default_smart_engine is None:
        _default_smart_engine = SmartRuleEngine()
    return _default_smart_engine


def validate_smart_compliance(
    product_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute dynamic smart rule compliance verification."""
    engine = get_smart_rule_engine()
    return engine.validate(product_data, context)
