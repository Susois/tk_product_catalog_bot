from openpyxl import load_workbook

from app.excel import append_product
from app.models import Product


def test_append_product_without_system_timezone_database(tmp_path) -> None:
    output = tmp_path / "products.xlsx"
    product = Product(
        source_url="https://vt.tiktok.com/example",
        resolved_url="https://www.tiktok.com/view/product/123",
        product_id="123",
        name="Sản phẩm thử nghiệm",
        price="10.000 ₫",
    )

    append_product(output, product)

    sheet = load_workbook(output)["Sản phẩm TikTok"]
    assert sheet["B2"].value == "123"
    assert sheet["C2"].value == "Sản phẩm thử nghiệm"
    assert sheet["D2"].value == "10.000 ₫"
