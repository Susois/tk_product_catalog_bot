from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Alignment, Font, PatternFill
from PIL import Image

from .models import Product

HEADERS = ["Thời gian", "Mã sản phẩm", "Tên sản phẩm", "Giá", "Tiền tệ", "Ảnh", "Link gốc", "Link TikTok Shop"]
VIETNAM_TIMEZONE = timezone(timedelta(hours=7))


def _new_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sản phẩm TikTok"
    sheet.append(HEADERS)
    fill = PatternFill("solid", fgColor="1F4E78")
    for cell in sheet[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center")
    widths = {"A": 20, "B": 22, "C": 65, "D": 20, "E": 12, "F": 24, "G": 40, "H": 55}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A2"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def _download_image(url: str, image_dir: Path, product_id: str) -> Path | None:
    if not url:
        return None
    image_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", product_id or "product")
    target = image_dir / f"{safe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    try:
        response = httpx.get(url, follow_redirects=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        target.write_bytes(response.content)
        with Image.open(target) as image:
            image.verify()
        return target
    except (httpx.HTTPError, OSError):
        target.unlink(missing_ok=True)
        return None


def append_product(path: Path, product: Product) -> Path:
    if not path.exists():
        _new_workbook(path)
    workbook = load_workbook(path)
    sheet = workbook["Sản phẩm TikTok"]
    row = sheet.max_row + 1
    sheet.append([
        datetime.now(VIETNAM_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
        product.product_id,
        product.name,
        product.price,
        product.currency,
        product.image_urls[0] if product.image_urls else "",
        product.source_url,
        product.resolved_url,
    ])
    sheet.row_dimensions[row].height = 110
    for cell in sheet[row]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)

    image_path = _download_image(
        product.image_urls[0] if product.image_urls else "",
        path.parent / "product-images",
        product.product_id,
    )
    if image_path:
        image = ExcelImage(str(image_path))
        image.width = 140
        image.height = 140
        sheet.add_image(image, f"F{row}")
        sheet[f"F{row}"] = ""
    workbook.save(path)
    return path
