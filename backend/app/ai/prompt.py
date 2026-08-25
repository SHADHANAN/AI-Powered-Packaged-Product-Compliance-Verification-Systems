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
