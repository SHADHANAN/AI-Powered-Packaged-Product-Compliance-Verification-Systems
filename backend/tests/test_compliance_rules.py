from app.models.enums import ComplianceStatus, Severity
from app.services.compliance_rules import (
    eval_batch_number_declaration,
    eval_brand_name_declaration,
    eval_country_of_origin,
    eval_customer_care_declaration,
    eval_import_date_declaration,
    eval_importer_declaration,
    eval_manufacturer_declaration,
    eval_mfg_date_declaration,
    eval_mrp_declaration,
    eval_net_quantity_declaration,
    eval_product_name_declaration,
    eval_quantity_unit_validity,
)


def test_mrp_rule_evaluation():
    """Test MRP rule validation with valid, invalid, and missing values."""
    # Valid MRP
    res_valid = eval_mrp_declaration({"mrp": "249.00"})
    assert res_valid.status == ComplianceStatus.PASS
    assert res_valid.severity == Severity.HIGH
    assert "249.00" in res_valid.message

    # Invalid MRP (0 or negative)
    res_zero = eval_mrp_declaration({"mrp": "0.00"})
    assert res_zero.status == ComplianceStatus.FAIL

    # Invalid non-numeric text
    res_invalid = eval_mrp_declaration({"mrp": "free"})
    assert res_invalid.status == ComplianceStatus.FAIL

    # Missing MRP
    res_missing = eval_mrp_declaration({})
    assert res_missing.status == ComplianceStatus.FAIL
    assert res_missing.recommendation is not None


def test_net_quantity_and_unit_rules():
    """Test Net Quantity and Approved Unit rules."""
    # Valid quantity and standard unit
    res_qty = eval_net_quantity_declaration({"net_quantity": "500 g", "quantity_unit": "g"})
    res_unit = eval_quantity_unit_validity({"net_quantity": "500 g", "quantity_unit": "g"})
    assert res_qty.status == ComplianceStatus.PASS
    assert res_unit.status == ComplianceStatus.PASS

    # Non-standard unit -> WARNING
    res_warn_unit = eval_quantity_unit_validity({"net_quantity": "2 baskets", "quantity_unit": "baskets"})
    assert res_warn_unit.status == ComplianceStatus.WARNING

    # Missing quantity -> FAIL
    res_missing_qty = eval_net_quantity_declaration({})
    assert res_missing_qty.status == ComplianceStatus.FAIL


def test_manufacturer_rule():
    """Test manufacturer name and address rule."""
    res_pass = eval_manufacturer_declaration({"manufacturer": "Nestle India Ltd, Industrial Area, Moga"})
    assert res_pass.status == ComplianceStatus.PASS
    assert res_pass.severity == Severity.CRITICAL

    res_fail = eval_manufacturer_declaration({})
    assert res_fail.status == ComplianceStatus.FAIL


def test_importer_and_origin_rules():
    """Test Importer and Country of Origin rules."""
    # Domestic product without import details -> importer NOT_APPLICABLE
    res_domestic = eval_importer_declaration({"country_of_origin": "India"})
    assert res_domestic.status == ComplianceStatus.NOT_APPLICABLE

    # Imported product with importer declared -> PASS
    res_imported_pass = eval_importer_declaration({
        "country_of_origin": "Germany",
        "importer": "Global Brand Importers Pvt Ltd, Mumbai",
    })
    assert res_imported_pass.status == ComplianceStatus.PASS

    # Imported product missing importer -> FAIL
    res_imported_fail = eval_importer_declaration({
        "country_of_origin": "USA",
        "import_date": "10/2024",
    })
    assert res_imported_fail.status == ComplianceStatus.FAIL

    # Country of Origin present -> PASS
    res_coo = eval_country_of_origin({"country_of_origin": "India"})
    assert res_coo.status == ComplianceStatus.PASS

    # Country of Origin missing -> FAIL
    res_coo_fail = eval_country_of_origin({})
    assert res_coo_fail.status == ComplianceStatus.FAIL


def test_batch_number_and_dates_rules():
    """Test Batch, Mfg Date, and Import Date rules."""
    # Batch Number
    assert eval_batch_number_declaration({"batch_number": "B-2024/09"}).status == ComplianceStatus.PASS
    assert eval_batch_number_declaration({}).status == ComplianceStatus.FAIL

    # Manufacturing Date
    assert eval_mfg_date_declaration({"manufacturing_date": "10/2024"}).status == ComplianceStatus.PASS
    assert eval_mfg_date_declaration({"manufacturing_date": "InvalidDate"}).status == ComplianceStatus.WARNING
    assert eval_mfg_date_declaration({}).status == ComplianceStatus.FAIL

    # Import Date
    assert eval_import_date_declaration({}).status == ComplianceStatus.NOT_APPLICABLE
    assert eval_import_date_declaration({"importer": "ABC Ltd", "import_date": "11/2024"}).status == ComplianceStatus.PASS


def test_customer_care_rule():
    """Test Consumer Care contact rule."""
    res_pass = eval_customer_care_declaration({"customer_care_details": "care@brand.com / 1800-222-333"})
    assert res_pass.status == ComplianceStatus.PASS

    res_fail = eval_customer_care_declaration({})
    assert res_fail.status == ComplianceStatus.FAIL


def test_product_name_and_brand_rules():
    """Test Product Name and Brand Name rules."""
    assert eval_product_name_declaration({"product_name": "Almond Cookies"}).status == ComplianceStatus.PASS
    assert eval_product_name_declaration({}).status == ComplianceStatus.WARNING

    assert eval_brand_name_declaration({"brand_name": "NutriBite"}).status == ComplianceStatus.PASS
    assert eval_brand_name_declaration({}).status == ComplianceStatus.WARNING
