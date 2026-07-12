from app.catalog import ProductRegistry, classify_product, normalize_url
from app.models import Product


def test_classify_womens_clothing() -> None:
    assert classify_product("Áo sơ mi nữ tay dài") == "quan_ao_nu"
    assert classify_product("Đầm nữ dự tiệc") == "quan_ao_nu"


def test_classify_underwear_before_general_clothing() -> None:
    assert classify_product("Áo ngực nữ không gọng") == "do_lot_nu"
    assert classify_product("Quần lót nữ cotton") == "do_lot_nu"


def test_classify_shoes_and_accessories() -> None:
    assert classify_product("Giày sneaker nữ đế cao") == "giay_dep"
    assert classify_product("Ốp lưng điện thoại chống sốc") == "phu_kien_linh_tinh"


def test_normalize_url_removes_tracking_query() -> None:
    assert normalize_url("http://VT.TIKTOK.COM/ABC/?utm_source=x") == "https://vt.tiktok.com/ABC"


def test_registry_persists_urls_and_product_ids(tmp_path) -> None:
    path = tmp_path / "registry.json"
    registry = ProductRegistry(path)
    registry.register(
        Product(
            source_url="https://vt.tiktok.com/ABC?tracking=1",
            resolved_url="https://www.tiktok.com/view/product/123?foo=bar",
            product_id="123",
            name="Test",
        )
    )
    registry.save()

    loaded = ProductRegistry(path)
    assert loaded.contains_url("https://vt.tiktok.com/ABC?other=value")
    assert loaded.contains_product("123")
