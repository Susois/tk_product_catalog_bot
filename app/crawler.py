from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, unquote_plus, urlparse

from playwright.async_api import Page, async_playwright

from .models import Product

TIKTOK_URL_RE = re.compile(r"https?://(?:[\w.-]+\.)?tiktok\.com/\S+", re.IGNORECASE)
PRICE_RE = re.compile(r"(?:₫|đ|VND)\s*[\d.,]+|[\d.,]+\s*(?:₫|đ|VND)", re.IGNORECASE)


def find_tiktok_url(text: str) -> str | None:
    match = TIKTOK_URL_RE.search(text)
    return match.group(0).rstrip(".,);]>") if match else None


def _walk_json(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key.lower(), child
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _first_json_value(data: Any, keys: set[str]) -> Any:
    for key, value in _walk_json(data):
        if key in keys and isinstance(value, (str, int, float)) and str(value).strip():
            return value
    return None


def _price_from_json(data: Any) -> str:
    direct = _first_json_value(
        data,
        {"formatted_price", "formatted_sale_price", "sale_price_text", "price_text", "display_price"},
    )
    if direct:
        return str(direct)
    for key, value in _walk_json(data):
        if key in {"sale_price", "min_price", "price"}:
            if isinstance(value, dict):
                amount = value.get("price_str") or value.get("amount") or value.get("value")
                if amount:
                    return str(amount)
            elif isinstance(value, (str, int, float)) and str(value).strip():
                return str(value)
    return ""


def _images_from_json(data: Any) -> list[str]:
    found: list[str] = []
    for key, value in _walk_json(data):
        if key in {"url", "image_url", "origin_url", "thumb_url"} and isinstance(value, str):
            if value.startswith("http") and any(host in value for host in ("ibyteimg.com", "tiktokcdn", "ibytedtos")):
                found.append(value)
        if key in {"url_list", "image_urls"} and isinstance(value, list):
            found.extend(item for item in value if isinstance(item, str) and item.startswith("http"))
    return list(dict.fromkeys(found))


async def _meta(page: Page, property_name: str) -> str:
    locator = page.locator(f'meta[property="{property_name}"], meta[name="{property_name}"]').first
    return (await locator.get_attribute("content") or "").strip() if await locator.count() else ""


async def _extract_page_json(page: Page) -> list[Any]:
    payloads: list[Any] = []
    scripts = page.locator('script[type="application/json"], script[id*="SIGI"], script[id*="UNIVERSAL"]')
    for index in range(min(await scripts.count(), 20)):
        raw = (await scripts.nth(index).text_content() or "").strip()
        if not raw or raw[0] not in "[{":
            continue
        try:
            payloads.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return payloads


async def _extract_product(page: Page, source_url: str) -> Product:
    resolved_url = page.url
    product_id_match = re.search(r"/product/(\d+)", resolved_url)
    product = Product(
        source_url=source_url,
        resolved_url=resolved_url,
        product_id=product_id_match.group(1) if product_id_match else "",
        name=await _meta(page, "og:title"),
        image_urls=[value for value in [await _meta(page, "og:image")] if value],
    )

    for data in await _extract_page_json(page):
        product.name = product.name or str(
            _first_json_value(data, {"product_name", "product_title", "title", "name"}) or ""
        )
        product.price = product.price or _price_from_json(data)
        product.image_urls.extend(_images_from_json(data))

    if not product.name:
        for selector in ('h1', '[data-e2e*="product-title"]', '[class*="ProductTitle"]'):
            locator = page.locator(selector).first
            if await locator.count() and (text := (await locator.text_content() or "").strip()):
                product.name = text
                break

    if not product.price:
        selectors = ('[data-e2e*="price"]', '[class*="Price"]', '[class*="price"]')
        for selector in selectors:
            locator = page.locator(selector)
            for index in range(min(await locator.count(), 20)):
                text = (await locator.nth(index).text_content() or "").strip()
                if match := PRICE_RE.search(text):
                    product.price = match.group(0)
                    break
            if product.price:
                break

    if not product.price:
        body_text = await page.locator("body").inner_text()
        if match := PRICE_RE.search(body_text):
            product.price = match.group(0)

    product.image_urls = list(dict.fromkeys(url for url in product.image_urls if url))
    return product


async def crawl_product(
    source_url: str,
    profile_dir: Path,
    headless: bool = False,
    captcha_wait_seconds: int = 180,
) -> Product:
    profile_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(profile_dir),
            channel="chrome",
            headless=headless,
            locale="vi-VN",
            viewport={"width": 1440, "height": 1000},
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(source_url, wait_until="domcontentloaded", timeout=90_000)
            await page.wait_for_timeout(4_000)

            deadline = time.monotonic() + captcha_wait_seconds
            product = await _extract_product(page, source_url)
            while (not product.name or not product.price) and time.monotonic() < deadline:
                await asyncio.sleep(3)
                product = await _extract_product(page, source_url)
                if headless:
                    break

            body_text = (await page.locator("body").inner_text()).lower()
            captcha_visible = any(
                marker in body_text
                for marker in ("verify to continue", "drag the puzzle", "xác minh để tiếp tục")
            )
            if captcha_visible and headless:
                raise RuntimeError("TikTok yêu cầu CAPTCHA. Chạy setup_browser.py trước hoặc đặt HEADLESS=false.")

            if not product.name:
                parsed = parse_qs(urlparse(page.url).query)
                if "og_info" in parsed:
                    try:
                        info = json.loads(unquote_plus(parsed["og_info"][0]))
                        product.name = info.get("title", "")
                        product.image_urls = product.image_urls or [info.get("image", "")]
                    except (json.JSONDecodeError, TypeError):
                        pass
            if not product.name:
                raise RuntimeError("Không đọc được tên sản phẩm. Hãy kiểm tra CAPTCHA/cửa sổ Chrome.")
            if not product.price:
                product.price = "Không đọc được giá"
            return product
        finally:
            await context.close()
