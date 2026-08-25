from app.services.field_extraction_service import extract_fields_from_text


def test_extract_mrp_field():
    """Test extracting Maximum Retail Price in various formats."""
    text1 = "MRP Rs. 149.50 (INCL. OF ALL TAXES)"
    fields1 = extract_fields_from_text(text1)
    mrp1 = next((f for f in fields1 if f["field_name"] == "mrp"), None)
    assert mrp1 is not None
    assert mrp1["field_value"] == "149.50"
    assert 0.0 <= mrp1["confidence"] <= 1.0

    text2 = "MAX RETAIL PRICE: ₹ 399"
    fields2 = extract_fields_from_text(text2)
    mrp2 = next((f for f in fields2 if f["field_name"] == "mrp"), None)
    assert mrp2 is not None
    assert mrp2["field_value"] == "399"


def test_extract_net_quantity_and_unit():
    """Test extracting Net Quantity and Quantity Unit."""
    text = "NET QTY: 750 gms"
    fields = extract_fields_from_text(text)
    qty = next((f for f in fields if f["field_name"] == "net_quantity"), None)
    unit = next((f for f in fields if f["field_name"] == "quantity_unit"), None)
    assert qty is not None
    assert qty["field_value"] == "750 gms"
    assert unit is not None
    assert unit["field_value"] == "gms"


def test_extract_batch_and_dates():
    """Test extracting Batch number, Mfg date, and Import date."""
    text = "BATCH NO: B-2024/09A\nMFG DATE: 10/2024\nIMPORT DATE: 11/2024"
    fields = extract_fields_from_text(text)

    batch = next((f for f in fields if f["field_name"] == "batch_number"), None)
    mfg = next((f for f in fields if f["field_name"] == "manufacturing_date"), None)
    imp = next((f for f in fields if f["field_name"] == "import_date"), None)

    assert batch is not None
    assert batch["field_value"] == "B-2024/09A"
    assert mfg is not None
    assert mfg["field_value"] == "10/2024"
    assert imp is not None
    assert imp["field_value"] == "11/2024"


def test_extract_manufacturer_importer_and_origin():
    """Test extracting Manufacturer, Importer, and Country of Origin."""
    text = (
        "COUNTRY OF ORIGIN: India\n"
        "MFD BY: Organic Foods Pvt. Ltd., Industrial Area, Phase II\n"
        "IMPORTED BY: Global Imports Ltd, Mumbai"
    )
    fields = extract_fields_from_text(text)

    origin = next((f for f in fields if f["field_name"] == "country_of_origin"), None)
    mfr = next((f for f in fields if f["field_name"] == "manufacturer"), None)
    imp = next((f for f in fields if f["field_name"] == "importer"), None)

    assert origin is not None
    assert origin["field_value"] == "India"
    assert mfr is not None
    assert "Organic Foods" in mfr["field_value"]
    assert imp is not None
    assert "Global Imports" in imp["field_value"]


def test_extract_customer_care():
    """Test extracting Consumer Care contact details."""
    text = "CUSTOMER CARE: care@brandfoods.com / 1800-111-2222"
    fields = extract_fields_from_text(text)
    care = next((f for f in fields if f["field_name"] == "customer_care_details"), None)
    assert care is not None
    assert "care@brandfoods.com" in care["field_value"]


def test_extract_multiple_fields_simultaneously():
    """Test extracting complete label information in a realistic scenario."""
    realistic_label = """
    BRAND: NutriBite
    PRODUCT NAME: Crunchy Almond Granola
    NET WEIGHT: 400 g
    MRP (INCL. ALL TAXES): Rs. 299.00
    BATCH NO: NB-400-24
    MFD ON: 15/08/2024
    COUNTRY OF ORIGIN: India
    MFD BY: HealthFoods India Ltd, Bangalore 560001
    CUSTOMER CARE: customercare@nutribite.in
    """
    fields = extract_fields_from_text(realistic_label)
    assert len(fields) >= 7

    extracted_names = {f["field_name"] for f in fields}
    assert "mrp" in extracted_names
    assert "net_quantity" in extracted_names
    assert "batch_number" in extracted_names
    assert "manufacturing_date" in extracted_names
    assert "country_of_origin" in extracted_names
    assert "manufacturer" in extracted_names
    assert "customer_care_details" in extracted_names

    for field in fields:
        assert 0.0 <= field["confidence"] <= 1.0
        assert len(field["field_value"]) > 0
        assert len(field["source_text"]) > 0


def test_empty_or_whitespace_text_handled_gracefully():
    """Ensure empty or nonsense text returns an empty list without errors."""
    assert extract_fields_from_text("") == []
    assert extract_fields_from_text("   \n\t  ") == []
    assert extract_fields_from_text("Random non-label gibberish words") == []

def test_extraction_service_wrapper():
    """Test the public extraction service wrapper."""
    from app.services.extraction_service.service import extract_product_fields

    text = "MRP: Rs. 120 NET QTY: 500 g BRAND: ABC"
    fields = extract_product_fields(text)

    field_names = {field["field_name"] for field in fields}

    assert "mrp" in field_names
    assert "net_quantity" in field_names
    assert "quantity_unit" in field_names
    assert "brand_name" in field_names
def test_fields_to_dict():
    """Test conversion of extracted fields into a keyed dictionary."""
    from app.services.field_extraction_service import (
        extract_fields_from_text,
        fields_to_dict,
    )

    fields = extract_fields_from_text(
        "MRP: Rs. 120 NET QTY: 500 g BRAND: ABC"
    )

    result = fields_to_dict(fields)

    assert result["mrp"]["value"] == "120"
    assert result["net_quantity"]["value"] == "500 g"
    assert result["quantity_unit"]["value"] == "g"
    assert result["brand_name"]["value"] == "ABC"

    assert 0 <= result["mrp"]["confidence"] <= 1