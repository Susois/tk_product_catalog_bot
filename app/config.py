from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    allowed_user_ids: frozenset[int]
    headless: bool
    browser_profile_dir: Path
    output_excel: Path
    product_registry: Path
    captcha_wait_seconds: int


def load_settings(require_token: bool = True) -> Settings:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if require_token and not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in .env")

    raw_ids = os.getenv("ALLOWED_USER_IDS", "")
    allowed_ids = frozenset(int(value.strip()) for value in raw_ids.split(",") if value.strip())
    return Settings(
        telegram_token=token,
        allowed_user_ids=allowed_ids,
        headless=os.getenv("HEADLESS", "false").lower() in {"1", "true", "yes"},
        browser_profile_dir=Path(os.getenv("BROWSER_PROFILE_DIR", "./data/browser-profile")).resolve(),
        output_excel=Path(os.getenv("OUTPUT_EXCEL", "./data/tiktok_products.xlsx")).resolve(),
        product_registry=Path(os.getenv("PRODUCT_REGISTRY", "./data/product_registry.json")).resolve(),
        captcha_wait_seconds=int(os.getenv("CAPTCHA_WAIT_SECONDS", "180")),
    )
