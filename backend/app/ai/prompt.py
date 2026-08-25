"""AI Prompts and templates for compliance verification."""
import json
from typing import Any, Dict, List

COMPLIANCE_SYSTEM_PROMPT = """You are an expert Legal Metrology compliance verification assistant.
Your task is to evaluate the compliance of a packaged product based on its extracted label fields.

You MUST evaluate the product against the following registered Legal Metrology rules:
{rules_json}

Extracted Label Fields (Input):
{fields_json}

For each rule, determine if the product passes, warnings, fails, or is not applicable.
Return a structured JSON list containing the evaluation of EACH rule. Each element of the JSON list MUST adhere exactly to this schema:
- rule_code (string, must match the registered rule_code exactly, e.g. "LM-MRP-001")
- rule_name (string, must match the registered rule_name exactly)
- status (string, MUST be exactly one of: "PASS", "FAIL", "WARNING", "NOT_APPLICABLE")
- severity (string, MUST match the rule's registered severity, e.g. "CRITICAL", "HIGH", "MEDIUM", "LOW")
- message (string, explanation of the evaluation result)
- expected_value (string or null, expected format or value requirement for the rule)
- actual_value (string or null, the actual value extracted from the label)
- recommendation (string or null, recommended action if status is "FAIL" or "WARNING")

Do not generate any formatting, explanation, or notes outside the valid JSON array output. Do not wrap the JSON output in markdown backticks (like ```json ... ```). Output ONLY raw JSON.
"""

def format_compliance_prompt(fields: Dict[str, str], rules: List[Any]) -> str:
    """Format compliance prompt by inserting rules and fields."""
    rules_data = []
    for r in rules:
        rules_data.append({
            "rule_code": r.rule_code,
            "rule_name": r.rule_name,
            "description": r.description,
            "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            "required_fields": r.required_fields
        })
    
    rules_json = json.dumps(rules_data, indent=2)
    fields_json = json.dumps(fields, indent=2)
    
    return COMPLIANCE_SYSTEM_PROMPT.format(
        rules_json=rules_json,
        fields_json=fields_json
    )


OCR_INTERPRETATION_SYSTEM_PROMPT = """You are an expert AI data extraction assistant.
Your task is to analyze raw OCR text from a product package label and refine the values extracted by a deterministic regex engine.

Raw OCR Text:
{raw_text}

Deterministic Regex Extractions:
{deterministic_extractions}

Review the deterministic extractions and the raw OCR text. Provide AI assistance to:
1. Resolve ambiguous OCR fields (e.g., misread letters or symbols like 'l' vs '1', 'O' vs '0', 's' vs '5').
2. Format/normalize values:
   - mrp: extract only the numeric value (e.g., "Rs 199/-" -> "199.00", "250.00" -> "250.00").
   - net_quantity: normalize unit (e.g., "500 gms" -> "500 g", "0.5 kg" -> "0.5 kg").
   - quantity_unit: standard lowercase SI unit or abbreviation (e.g., "gms" -> "g", "kg" -> "kg").
   - manufacturing_date / import_date: normalize to MM/YYYY format (e.g., "07/26" -> "07/2026", "Jan 2024" -> "01/2024").
   - manufacturer / importer: clean up company name and remove address if it was concatenated, ensuring name is distinct.
3. Identify low-confidence or poorly formatted fields.
4. Set status to "NEEDS_REVIEW" and lower confidence if a field is highly ambiguous, badly smudged, or conflicting. Do NOT guess when confidence is low.
5. NEVER invent or fabricate missing information. If a field is not present in the OCR text, do not assume or invent values; keep its value as null and status as "UNRESOLVED".

Return a structured JSON list of interpreted fields. Each item MUST have:
- field (string, field name matching the deterministic fields: e.g. "mrp", "net_quantity", "quantity_unit", "batch_number", "manufacturing_date", "import_date", "country_of_origin", "manufacturer", "manufacturer_address", "importer", "importer_address", "customer_care_details", "product_name", "brand_name")
- original_ocr_value (string or null, the original regex/OCR value)
- interpreted_value (string or null, the normalized/corrected value)
- confidence (float between 0.0 and 1.0)
- evidence (string or null, the exact text/snippet from the OCR text)
- short_reason (string, short explanation of interpretation or why review is needed)
- status (string, must be one of: "COMPLETED", "NEEDS_REVIEW", "UNRESOLVED")

Do not generate any formatting, explanation, or notes outside the valid JSON array output. Do not wrap the JSON output in markdown backticks (like ```json ... ```). Output ONLY raw JSON.
"""


def format_ocr_interpretation_prompt(raw_text: str, deterministic_extractions: List[Dict[str, Any]]) -> str:
    """Format prompt for AI-assisted OCR field interpretation."""
    ext_json = json.dumps(deterministic_extractions, indent=2)
    return OCR_INTERPRETATION_SYSTEM_PROMPT.format(
        raw_text=raw_text,
        deterministic_extractions=ext_json
    )


COMPLIANCE_EXPLANATION_SYSTEM_PROMPT = """You are an expert Legal Metrology compliance verification assistant.
Your task is to generate a clear, human-readable, and professional compliance explanation for a packaged product based on its deterministic compliance results.

You MUST adhere strictly to the following rules:
1. Use the provided deterministic compliance status and rule check results as the absolute source of truth.
2. If the deterministic compliance status is "COMPLIANT", you MUST describe the product as compliant. You must NOT independently declare it "NON_COMPLIANT" or invent any violations.
3. You must NOT invent any laws, regulations, penalties, violations, or missing fields. Only reference the rules and fields provided.
4. Keep the explanation professional, concise, and focused on helping the inspector understand the status.

Deterministic Compliance Results:
- Status: {compliance_status}
- Overall Score: {overall_score}%
- Violations / Warnings:
{violations_list}

Extracted Label Fields and Evidence:
{fields_list}

Generate a clear, human-readable compliance explanation. Do not include markdown code block formatting or other conversational text outside the explanation.
"""


def format_compliance_explanation_prompt(
    compliance_status: str,
    overall_score: float,
    violations_list: str,
    fields_list: str,
) -> str:
    """Format prompt for AI-generated compliance explanation."""
    return COMPLIANCE_EXPLANATION_SYSTEM_PROMPT.format(
        compliance_status=compliance_status,
        overall_score=overall_score,
        violations_list=violations_list,
        fields_list=fields_list,
    )
