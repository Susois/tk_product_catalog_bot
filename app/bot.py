from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .catalog import (
    CATEGORY_LABELS,
    ProductRegistry,
    bootstrap_registry_from_excels,
    category_excel_path,
    classify_product,
)
from .config import Settings
from .crawler import crawl_product, find_tiktok_url
from .excel import append_product

LOGGER = logging.getLogger(__name__)


class TikTokBot:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.processing_lock = asyncio.Lock()
        self.registry = ProductRegistry(settings.product_registry)
        bootstrap_registry_from_excels(settings.output_excel.parent, self.registry)

    def _authorized(self, update: Update) -> bool:
        user = update.effective_user
        return bool(user and (not self.settings.allowed_user_ids or user.id in self.settings.allowed_user_ids))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if not self._authorized(update) or not update.message:
            return
        await update.message.reply_text("Gửi link sản phẩm TikTok Shop. Bot sẽ crawl thông tin và trả lại file Excel.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if not update.message or not self._authorized(update):
            return
        url = find_tiktok_url(update.message.text or "")
        if not url:
            await update.message.reply_text("Không tìm thấy link TikTok hợp lệ trong tin nhắn.")
            return

        status = await update.message.reply_text("Đang mở TikTok và đọc thông tin sản phẩm...")
        try:
            async with self.processing_lock:
                if self.registry.contains_url(url):
                    await status.edit_text("Link này đã xuất hiện trước đó, bot đã bỏ qua và không crawl lại.")
                    return

                product = await crawl_product(
                    url,
                    self.settings.browser_profile_dir,
                    self.settings.headless,
                    self.settings.captcha_wait_seconds,
                )

                if self.registry.contains_product(product.product_id):
                    self.registry.register(product)
                    self.registry.save()
                    await status.edit_text("Sản phẩm này đã tồn tại với một link khác, bot đã bỏ qua.")
                    return

                category = classify_product(product.name)
                output_path = category_excel_path(self.settings.output_excel, category)
                excel_path = await asyncio.to_thread(append_product, output_path, product)
                self.registry.register(product)
                self.registry.save()

            await status.edit_text(
                f"Đã lấy: {product.name}\nGiá: {product.price}\nPhân loại: {CATEGORY_LABELS[category]}"
            )
            with excel_path.open("rb") as excel_file:
                await update.message.reply_document(excel_file, filename=excel_path.name)
        except Exception as error:
            LOGGER.exception("Failed to process %s", url)
            await status.edit_text(f"Không thể xử lý sản phẩm: {error}")


def build_application(settings: Settings) -> Application:
    bot = TikTokBot(settings)
    application = Application.builder().token(settings.telegram_token).build()
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    return application
