from app.services.extraction_service.service import extract_product_fields


def test_ocr_to_structured_field_extraction():
    """Verify the OCR-text to structured-field extraction flow."""
    ocr_text = (
        "M.R.P. : Rs. 199/-\n"
        "NET QTY: 500 gms\n"
        "BATCH NO: B-2026/08A\n"
        "MFD: 07/2026\n"
        "MADE IN INDIA\n"
        "BRAND: Fresh Foods"
    )

    fields = extract_product_fields(ocr_text)

    result = {
        field["field_name"]: field["field_value"]
        for field in fields
    }

    assert result["mrp"] == "199"
    assert result["net_quantity"] == "500 gms"
    assert result["quantity_unit"] == "gms"
    assert result["batch_number"] == "B-2026/08A"
    assert result["manufacturing_date"] == "07/2026"
    assert result["country_of_origin"] == "INDIA"
    assert result["brand_name"] == "Fresh Foods"