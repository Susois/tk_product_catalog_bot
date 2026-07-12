from openpyxl import load_workbook

from app import excel
from app.models import Product


def test_append_product_downloads_all_images(tmp_path, monkeypatch) -> None:
    output = tmp_path / "products.xlsx"
    downloaded_urls: list[str] = []

    def fake_download(url, image_dir, product_id):
        downloaded_urls.append(url)
        return None

    monkeypatch.setattr(excel, "_download_image", fake_download)
    product = Product(
        source_url="https://vt.tiktok.com/example",
        resolved_url="https://www.tiktok.com/view/product/123",
        product_id="123",
        name="Product with images",
        price="10000 VND",
        image_urls=["https://img.test/1.jpg", "https://img.test/2.jpg", "https://img.test/3.jpg"],
    )

    excel.append_product(output, product)

    sheet = load_workbook(output).active
    assert downloaded_urls == product.image_urls
    assert sheet.max_row == 4
    assert sheet["B2"].value == "123"
    assert sheet["F2"].value == product.image_urls[0]
    assert sheet["F3"].value == product.image_urls[1]
    assert sheet["F4"].value == product.image_urls[2]
