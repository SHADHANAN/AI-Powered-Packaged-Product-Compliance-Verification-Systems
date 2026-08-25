import re
from typing import Any, Dict, List

from app.services.extraction_service.normalizer import normalize_ocr_text
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

    raw_text = normalize_ocr_text(raw_text)

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
        # 1. Maximum Retail Price (MRP)
    # Supports common label/currency variations:
    # MRP: Rs. 120
    # M.R.P. ₹120/-
    # Maximum Retail Price: INR 120
    # MRP (Incl. All Taxes): 120
    mrp_match = re.search(
        r"""
        (?:
            M\.?\s*R\.?\s*P\.?
            |
            MAX(?:IMUM)?\s+RETAIL\s+PRICE
        )
        (?:\s*\([^)]*\))?
        \s*[:.\-]?\s*
        (?:RS\.?|INR|₹)?
        \s*
        ([0-9]+(?:\.[0-9]{1,2})?)
        \s*(?:/-)?
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if mrp_match:
        add_field(
            field_name="mrp",
            field_value=mrp_match.group(1),
            confidence=0.96,
            source_text=mrp_match.group(0),
        )

    # 2. Net Quantity & Quantity Unit
        # 2. Net Quantity & Quantity Unit
    # Supports: 500 g, 500G, 0.5 kg, 500 ml, 1 L, 250mg, etc.
    net_qty_match = re.search(
        r"""
        (?:
            NET\s*
            (?:
                QTY|QUANTITY|WT|WEIGHT|CONTENTS?|VOL(?:UME)?
            )
        )
        \s*[:.\-]?\s*
        ([0-9]+(?:\.[0-9]+)?)
        \s*
        (gms|kgs|gm|kg|mg|litres|litre|ltr|ml|cl|g|l)
        
        \b
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if net_qty_match:
        qty_num = net_qty_match.group(1)
        qty_unit = net_qty_match.group(2).lower()

        # Keep the original unit in the extracted value.
        # This preserves OCR/source information such as "gms".
        normalized_unit = {
                 "kgs": "kg",
    "gm": "g",
    "gms": "g",
    "ltr": "l",
    "litre": "l",
    "litres": "l",
}.get(qty_unit, qty_unit)

        add_field(
            field_name="net_quantity",
            field_value=f"{qty_num} {net_qty_match.group(2)}",
            confidence=0.95,
            source_text=net_qty_match.group(0),
        )

        add_field(
            field_name="quantity_unit",
            field_value=net_qty_match.group(2).lower(),
            confidence=0.95,
            source_text=net_qty_match.group(0),
        )

    # 3. Batch Number / Lot Number
        # 3. Batch Number / Lot Number
    # Supports values such as:
    # BATCH NO: B-2024/09A
    # BATCH NUMBER ABC123
    # LOT NO: L-45/2026
    batch_match = re.search(
        r"""
        (?:
            BATCH\s*(?:NO|NUM|NUMBER)?
            |B\.?\s*NO\.?
            |LOT\s*(?:NO|NUM|NUMBER)?
        )
        \s*[:.\-]?\s*
        ([A-Za-z0-9][A-Za-z0-9._/\-]*)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if batch_match:
        add_field(
            field_name="batch_number",
            field_value=batch_match.group(1),
            confidence=0.94,
            source_text=batch_match.group(0),
        )

    # 4. Manufacturing Date
        # 4. Manufacturing Date
    mfg_match = re.search(
        r"""
        (?:
            MFG\s*(?:DATE|DT|ON)?
            |MFD\s*(?:DATE|DT|ON)?
            |MANUFACTURED\s*(?:ON|DATE)?
            |PKD\s*(?:DATE|DT|ON)?
            |PACKED\s*(?:ON|DATE)?
            |PACKING\s*DATE
        )
        \s*[:.\-]?\s*
        (
            [0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}
            |
            [0-9]{1,2}[\/\-\.][0-9]{4}
            |
            (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
            [a-z]*[\s.\-/]*[0-9]{2,4}
        )
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if mfg_match:
        add_field(
            field_name="manufacturing_date",
            field_value=mfg_match.group(1),
            confidence=0.93,
            source_text=mfg_match.group(0),
        )
    # 5. Import Date
        # 5. Import Date
    imp_date_match = re.search(
        r"""
        (?:
            IMPORT\s*(?:DATE|DT|ON)?
            |IMPORTED\s*(?:ON|DATE)?
            |DATE\s*OF\s*IMPORT
        )
        \s*[:.\-]?\s*
        (
            [0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}
            |
            [0-9]{1,2}[\/\-\.][0-9]{4}
            |
            (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
            [a-z]*[\s.\-/]*[0-9]{2,4}
        )
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if imp_date_match:
        add_field(
            field_name="import_date",
            field_value=imp_date_match.group(1),
            confidence=0.93,
            source_text=imp_date_match.group(0),
        )

    # 6. Country of Origin
        # 6. Country of Origin
    country_match = re.search(
        r"""
        (?:
            COUNTRY\s*OF\s*ORIGIN
            |MADE\s*IN
            |PRODUCT\s*OF
            |ORIGIN
        )
        \s*[:.\-]?\s*
        ([A-Za-z][A-Za-z\s.&'-]*?)
        (?=\n|\r|[.;,]|MFG|MFD|PKD|BATCH|LOT|$)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if country_match:
        country_val = clean_snippet(country_match.group(1))

        if len(country_val) > 2:
            add_field(
                field_name="country_of_origin",
                field_value=country_val,
                confidence=0.92,
                source_text=country_match.group(0),
            )

    # 7. Manufacturer
        # 7. Manufacturer
    mfr_match = re.search(
        r"""
        (?:
            MFD(?:\s*BY|\.)?
            |MANUFACTURED\s*(?:AND\s*PACKED\s*)?BY
            |PRODUCED\s*BY
            |MANUFACTURER
        )
        \s*[:.\-]?\s*
        ([^\n\r]+)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if mfr_match:
        manufacturer_value = clean_snippet(mfr_match.group(1))

        add_field(
            field_name="manufacturer",
            field_value=manufacturer_value,
            confidence=0.90,
            source_text=mfr_match.group(0),
        )

        # Preserve a likely address when it appears after the manufacturer.
        address_match = re.search(
            r"(?:ADDRESS|ADDR\.?)\s*[:.\-]?\s*([^\n\r]+)",
            manufacturer_value,
            re.IGNORECASE,
        )

        if address_match:
            add_field(
                field_name="manufacturer_address",
                field_value=address_match.group(1),
                confidence=0.82,
                source_text=address_match.group(0),
            )

    # 8. Importer
        # 8. Importer
    importer_match = re.search(
        r"""
        (?:
            IMPORTED\s*(?:AND\s*PACKED\s*)?BY
            |IMPORTER
            |IMP\.?\s*BY
        )
        \s*[:.\-]?\s*
        ([^\n\r]+)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if importer_match:
        importer_value = clean_snippet(importer_match.group(1))

        add_field(
            field_name="importer",
            field_value=importer_value,
            confidence=0.90,
            source_text=importer_match.group(0),
        )

        address_match = re.search(
            r"(?:ADDRESS|ADDR\.?)\s*[:.\-]?\s*([^\n\r]+)",
            importer_value,
            re.IGNORECASE,
        )

        if address_match:
            add_field(
                field_name="importer_address",
                field_value=address_match.group(1),
                confidence=0.82,
                source_text=address_match.group(0),
            )

    # 9. Customer Care Details
        # 9. Customer Care Details
    care_match = re.search(
        r"""
        (?:
            CUSTOMER\s*CARE
            |CONSUMER\s*CARE
            |HELPLINE
            |FEEDBACK
            |CONTACT\s*US
            |TOLL\s*FREE
            |CARE\s*LINE
        )
        \s*[:.\-]?\s*
        ([^\n\r]+)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if care_match:
        care_value = clean_snippet(care_match.group(1))

        add_field(
            field_name="customer_care_details",
            field_value=care_value,
            confidence=0.92,
            source_text=care_match.group(0),
        )

    # 10. Product Name
       # 10. Product Name
    prod_name_match = re.search(
        r"""
        (?:
            PRODUCT\s*(?:NAME)?
            |ITEM\s*(?:NAME)?
            |COMMODITY
        )
        \s*[:.\-]?\s*
        ([^\n\r]+)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if prod_name_match:
        product_name = clean_snippet(prod_name_match.group(1))

        add_field(
            field_name="product_name",
            field_value=product_name,
            confidence=0.88,
            source_text=prod_name_match.group(0),
        )

    # 11. Brand Name
        # 11. Brand Name
    brand_match = re.search(
        r"""
        (?:
            BRAND\s*(?:NAME)?
            |TRADEMARK
            |TM
        )
        \s*[:.\-]?\s*
        ([A-Za-z0-9][A-Za-z0-9\s&.'-]*)
        """,
        raw_text,
        re.IGNORECASE | re.VERBOSE,
    )

    if brand_match:
        brand_value = clean_snippet(brand_match.group(1))

        add_field(
            field_name="brand_name",
            field_value=brand_value,
            confidence=0.88,
            source_text=brand_match.group(0),
        )

    logger.info(f"Extracted {len(extracted)} structured fields from OCR text")
    return extracted
