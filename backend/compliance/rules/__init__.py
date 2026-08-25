"""Compliance rules and configuration loader."""
import json
from pathlib import Path
from typing import Any, Dict, List

RULES_FILE_PATH = Path(__file__).parent / "legal_metrology_rules.json"


def load_legal_metrology_rules() -> Dict[str, Any]:
    """Load the Legal Metrology compliance rules JSON configuration."""
    with open(RULES_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_rules_list() -> List[Dict[str, Any]]:
    """Return the list of rule objects from the rules configuration."""
    data = load_legal_metrology_rules()
    return data.get("rules", [])
