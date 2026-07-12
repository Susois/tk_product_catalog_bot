from app.crawler import find_tiktok_url


def test_find_tiktok_url() -> None:
    assert find_tiktok_url("xem https://vt.tiktok.com/ABC123 nhé") == "https://vt.tiktok.com/ABC123"


def test_find_tiktok_url_strips_punctuation() -> None:
    assert find_tiktok_url("(https://www.tiktok.com/view/product/123).") == "https://www.tiktok.com/view/product/123"


def test_find_tiktok_url_rejects_other_hosts() -> None:
    assert find_tiktok_url("https://example.com/product") is None
