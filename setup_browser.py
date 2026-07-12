from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from app.config import load_settings


def find_chrome() -> Path:
    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError("Không tìm thấy Google Chrome. Hãy cài Chrome hoặc thêm chrome.exe vào PATH.")


def main() -> None:
    settings = load_settings(require_token=False)
    profile_dir = settings.browser_profile_dir
    profile_dir.mkdir(parents=True, exist_ok=True)
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.tiktok.com/login"

    command = [
        str(find_chrome()),
        f"--user-data-dir={profile_dir}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]

    print(f"Đang mở Chrome với profile: {profile_dir}")
    print("Hãy đăng nhập TikTok và đợi trang xác nhận đăng nhập hoàn tất.")
    print("Sau đó ĐÓNG TOÀN BỘ cửa sổ Chrome vừa mở. Script sẽ tự kết thúc và lưu session.")
    process = subprocess.Popen(command)
    exit_code = process.wait()
    if exit_code not in (0, None):
        raise RuntimeError(f"Chrome kết thúc với mã lỗi {exit_code}")
    print("Đã đóng Chrome. Session đăng nhập đã được lưu vào browser profile.")


if __name__ == "__main__":
    main()
