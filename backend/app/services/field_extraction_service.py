import re
from typing import Any, Dict, List

from app.utils.logging import get_logger

logger = get_logger("app.services.field_extraction")


def clean_snippet(text: str) -> str:
    """Normalize whitespace and strip stray symbols."""
    return re.sub(r"\s+", " ", text).strip()


def extract_fields_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Extract structured packaged product fields from raw OCR text using regex heuristics.
    
    Returns a list of dictionary representations of ExtractedField items.
    """
    if not raw_text or not raw_text.strip():
        logger.info("Empty OCR text provided for field extraction")
        return []

    extracted: List[Dict[str, Any]] = []
    seen_fields = set()

    def add_field(field_name: str, field_value: str, confidence: float, source_text: str):
        if field_name not in seen_fields and field_value and field_value.strip():
            seen_fields.add(field_name)
            extracted.append({
                "field_name": field_name,
                "field_value": clean_snippet(field_value),
                "confidence": round(confidence, 2),
                "source_text": clean_snippet(source_text),
            })

    # 1. Maximum Retail Price (MRP)
    mrp_match = re.search(
        r"(?:M\.?R\.?P\.?|MAX(?:IMUM)?\s*RETAIL\s*PRICE|PRICE|MRP\s*\(INCL\.\s*ALL\s*TAXES\))\s*[:\.-]?\s*(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        raw_text,
        re.IGNORECASE,
    )
    if mrp_match:
        add_field(
            field_name="mrp",
            field_value=mrp_match.group(1),
            confidence=0.95,
            source_text=mrp_match.group(0),
        )

    # 2. Net Quantity & Quantity Unit
    net_qty_match = re.search(
        r"(?:NET\s*(?:QTY|QUANTITY|WT|WEIGHT|CONTENTS?)|NET\s*VOL(?:UME)?)\s*[:\.-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)",
        raw_text,
        re.IGNORECASE,
    )
    if net_qty_match:
        qty_num = net_qty_match.group(1)
        qty_unit = net_qty_match.group(2).lower()
        add_field(
            field_name="net_quantity",
            field_value=f"{qty_num} {qty_unit}",
            confidence=0.90,
            source_text=net_qty_match.group(0),
        )
        add_field(
            field_name="quantity_unit",
            field_value=qty_unit,
            confidence=0.90,
            source_text=net_qty_match.group(0),
        )

    # 3. Batch Number / Lot Number
    batch_match = re.search(
        r"(?:BATCH\s*(?:NO|NUM|NUMBER)?|B\.?\s*NO\.?|LOT\s*(?:NO|NUM|NUMBER)?|LOT)\s*[:\.-]?\s*([A-Za-z0-9\-\/]+)",
        raw_text,
        re.IGNORECASE,
    )
    if batch_match:
        add_field(
            field_name="batch_number",
            field_value=batch_match.group(1),
            confidence=0.88,
            source_text=batch_match.group(0),
        )

    # 4. Manufacturing Date
    mfg_match = re.search(
        r"(?:MFG\s*(?:DATE|DT|ON)?|MFD\s*(?:DATE|DT|ON)?|MFD\.?|MANUFACTURED\s*(?:ON|DATE)?|PKD\s*(?:DATE|DT|ON)?|PKD\.?|PACKED\s*(?:ON|DATE)?)\s*[:\.-]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[0-9]{1,2}[\/\-\.][0-9]{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.\-\/]*[0-9]{2,4})",
        raw_text,
        re.IGNORECASE,
    )
    if mfg_match:
        add_field(
            field_name="manufacturing_date",
            field_value=mfg_match.group(1),
            confidence=0.85,
            source_text=mfg_match.group(0),
        )

    # 5. Import Date
    imp_date_match = re.search(
        r"(?:IMPORT\s*(?:DATE|DT|ON)?|IMPORTED\s*(?:ON|DATE)?)\s*[:\.-]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[0-9]{1,2}[\/\-\.][0-9]{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.\-\/]*[0-9]{2,4})",
        raw_text,
        re.IGNORECASE,
    )
    if imp_date_match:
        add_field(
            field_name="import_date",
            field_value=imp_date_match.group(1),
            confidence=0.85,
            source_text=imp_date_match.group(0),
        )

    # 6. Country of Origin
    country_match = re.search(
        r"(?:COUNTRY\s*OF\s*ORIGIN|MADE\s*IN|PRODUCT\s*OF|ORIGIN)\s*[:\.-]?\s*([A-Za-z\s]+?)(?:\n|\r|\.|,|$|;|Mfg)",
        raw_text,
        re.IGNORECASE,
    )
    if country_match:
        country_val = country_match.group(1).strip()
        if len(country_val) > 2:
            add_field(
                field_name="country_of_origin",
                field_value=country_val,
                confidence=0.85,
                source_text=country_match.group(0),
            )

    # 7. Manufacturer
    mfr_match = re.search(
        r"(?:MFD(?:\s*BY|\.)?|MANUFACTURED\s*(?:AND\s*PACKED\s*)?BY|PRODUCED\s*BY)\s*[:\.-]?\s*([^\n\r]+)",
        raw_text,
        re.IGNORECASE,
    )
    if mfr_match:
        add_field(
            field_name="manufacturer",
            field_value=mfr_match.group(1),
            confidence=0.85,
            source_text=mfr_match.group(0),
        )

    # 8. Importer
    importer_match = re.search(
        r"(?:IMPORTED\s*(?:AND\s*PACKED\s*)?BY|IMPORTER|IMP\.\s*BY)\s*[:\.-]?\s*([^\n\r]+)",
        raw_text,
        re.IGNORECASE,
    )
    if importer_match:
        add_field(
            field_name="importer",
            field_value=importer_match.group(1),
            confidence=0.85,
            source_text=importer_match.group(0),
        )

    # 9. Customer Care Details
    care_match = re.search(
        r"(?:CUSTOMER\s*CARE|CONSUMER\s*CARE|HELPLINE|FEEDBACK|CONTACT\s*US|TOLL\s*FREE|CARE\s*LINE)\s*[:\.-]?\s*([^\n\r]+)",
        raw_text,
        re.IGNORECASE,
    )
    if care_match:
        add_field(
            field_name="customer_care_details",
            field_value=care_match.group(1),
            confidence=0.85,
            source_text=care_match.group(0),
        )

    # 10. Product Name
    prod_name_match = re.search(
        r"(?:PRODUCT\s*(?:NAME)?|ITEM\s*(?:NAME)?|COMMODITY)\s*[:\.-]?\s*([^\n\r]+)",
        raw_text,
        re.IGNORECASE,
    )
    if prod_name_match:
        add_field(
            field_name="product_name",
            field_value=prod_name_match.group(1),
            confidence=0.80,
            source_text=prod_name_match.group(0),
        )

    # 11. Brand Name
    brand_match = re.search(
        r"(?:BRAND\s*(?:NAME)?|TRADEMARK|TM)\s*[:\.-]?\s*([A-Za-z0-9\s&]+)",
        raw_text,
        re.IGNORECASE,
    )
    if brand_match:
        add_field(
            field_name="brand_name",
            field_value=brand_match.group(1),
            confidence=0.80,
            source_text=brand_match.group(0),
        )

    logger.info(f"Extracted {len(extracted)} structured fields from OCR text")
    return extracted
