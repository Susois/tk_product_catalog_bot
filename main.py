import logging

from app.bot import build_application
from app.config import load_settings


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    # Telegram long polling performs an HTTP request every few seconds. Keep
    # routine 200 responses out of the console while preserving real errors.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    build_application(load_settings()).run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
