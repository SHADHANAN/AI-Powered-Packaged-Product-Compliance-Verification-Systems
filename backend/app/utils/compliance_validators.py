import re
from typing import Optional, Set, Tuple

# Standard Legal Metrology approved measurement units
ALLOWED_UNITS: Set[str] = {
    "g", "gm", "gms", "gram", "grams",
    "kg", "kgs", "kilogram", "kilograms",
    "mg", "milligram", "milligrams",
    "ml", "mls", "milliliter", "millilitre", "milliliters", "millilitres",
    "l", "lt", "ltr", "liter", "litre", "liters", "litres",
    "m", "meter", "metre", "meters", "metres",
    "cm", "centimeter", "centimetre",
    "mm", "millimeter", "millimetre",
    "u", "unit", "units", "n", "num", "number", "pc", "pcs", "piece", "pieces",
    "count", "capsules", "tablets", "sachets", "wipes", "sheets",
}


def clean_str(val: Optional[str]) -> str:
    """Normalize input string."""
    if not val:
        return ""
    return str(val).strip()


def validate_required_text(value: Optional[str], min_length: int = 2) -> Tuple[bool, str]:
    """Validate that text is present and has meaningful length."""
    val = clean_str(value)
    if not val:
        return False, "Value is missing or empty"
    if len(val) < min_length:
        return False, f"Value '{val}' is too short (min {min_length} characters required)"
    return True, val


def validate_mrp(value: Optional[str]) -> Tuple[bool, Optional[float], str]:
    """Validate that MRP is present, numeric, and positive."""
    val = clean_str(value)
    if not val:
        return False, None, "MRP is not declared on label"

    # Strip currency signs, 'Rs', 'INR', '/=', 'only'
    cleaned = re.sub(r"(?:rs\.?|inr|₹|\/=|only|\(incl.*?\))", "", val, flags=re.IGNORECASE).strip()
    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    if not match:
        return False, None, f"Could not parse numeric price from '{val}'"

    try:
        numeric_val = float(match.group(1))
        if numeric_val <= 0:
            return False, numeric_val, f"MRP must be greater than 0, found '{numeric_val}'"
        return True, numeric_val, f"{numeric_val:.2f}"
    except (ValueError, TypeError):
        return False, None, f"Invalid MRP format '{val}'"


def validate_quantity_and_unit(
    quantity_str: Optional[str],
    unit_str: Optional[str] = None,
) -> Tuple[bool, bool, Optional[float], Optional[str], str]:
    """Validate net quantity numeric value and standard unit of measurement.
    
    Returns: (is_quantity_valid, is_unit_valid, numeric_val, parsed_unit, message)
    """
    qty_text = clean_str(quantity_str)
    if not qty_text:
        return False, False, None, None, "Net quantity is not declared"

    # Extract number and unit
    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?", qty_text)
    if not match:
        return False, False, None, None, f"Cannot parse numeric net quantity from '{qty_text}'"

    try:
        num_val = float(match.group(1))
        if num_val <= 0:
            return False, False, num_val, None, "Net quantity must be greater than 0"
    except (ValueError, TypeError):
        return False, False, None, None, f"Invalid number in quantity '{qty_text}'"

    found_unit = clean_str(unit_str) or (match.group(2) if match.group(2) else "")
    found_unit_lower = found_unit.lower()

    is_unit_valid = found_unit_lower in ALLOWED_UNITS
    msg = f"Quantity: {num_val} {found_unit}".strip()
    return True, is_unit_valid, num_val, found_unit, msg


def validate_date_format(date_str: Optional[str]) -> Tuple[bool, str]:
    """Validate date format for mfg/import/packaging dates."""
    val = clean_str(date_str)
    if not val:
        return False, "Date is not declared"

    # Supported: DD/MM/YYYY, MM/YYYY, DD-MM-YYYY, Month Year, etc.
    patterns = [
        r"^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$",
        r"^\d{1,2}[\/\-\.]\d{4}$",
        r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.\-\/]*\d{2,4}$",
    ]
    for pattern in patterns:
        if re.search(pattern, val, flags=re.IGNORECASE):
            return True, val

    return False, f"Unrecognized date format '{val}' (expected DD/MM/YYYY, MM/YYYY, or Month/Year)"


def validate_customer_care_details(care_str: Optional[str]) -> Tuple[bool, str]:
    """Validate customer care contains contact details (email, phone, helpline, address)."""
    val = clean_str(care_str)
    if not val:
        return False, "Consumer care details are missing"

    # Check for presence of email or phone number or postal/contact address
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", val))
    has_phone = bool(re.search(r"(?:\+?\d{1,4}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}|\b1800[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", val))
    has_text = len(val) >= 5

    if has_email or has_phone or has_text:
        return True, val

    return False, f"Incomplete customer care info: '{val}'"
