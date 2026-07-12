# Telegram TikTok Shop crawler

Bot nhận link sản phẩm TikTok Shop, mở trang bằng Chrome profile cố định, lấy tên, giá và ảnh, sau đó thêm một dòng vào Excel và gửi file lại Telegram.

Bot tự chống trùng theo link và mã sản phẩm. Dữ liệu được chia thành bốn file trong thư mục `data`:

- `quan_ao_nu.xlsx`
- `do_lot_nu.xlsx`
- `phu_kien_linh_tinh.xlsx`
- `giay_dep.xlsx`

Lịch sử chống trùng nằm trong `data/product_registry.json`. Khi khởi động, bot cũng quét các file Excel cũ để nhập những sản phẩm đã lưu trước đây vào registry.

## Cài đặt trên Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Tạo bot bằng `@BotFather`, lấy token và điền `TELEGRAM_BOT_TOKEN` trong `.env`. Nên điền Telegram user ID của bạn vào `ALLOWED_USER_IDS` để người khác không dùng bot.

Máy cần cài Google Chrome. Chạy một lần để đăng nhập hoặc vượt CAPTCHA thủ công và lưu session. Script mở Chrome trực tiếp, không qua Playwright:

```powershell
python setup_browser.py
```

Sau khi đăng nhập QR thành công, hãy đợi TikTok hiển thị tài khoản rồi **đóng toàn bộ cửa sổ Chrome vừa mở**. Không cần nhấn Enter trong terminal; script sẽ tự kết thúc sau khi Chrome đóng và lưu session.

Nếu CAPTCHA chỉ xuất hiện ở trang sản phẩm, mở trực tiếp URL đó bằng profile:

```powershell
python setup_browser.py "https://vt.tiktok.com/..."
```

Sau đó chạy bot:

```powershell
python main.py
```

Gửi URL như `https://vt.tiktok.com/...` cho bot. File mặc định nằm tại `data/tiktok_products.xlsx`; ảnh gốc nằm tại `data/product-images` và cũng được nhúng vào Excel.

## Lưu ý

- Giữ `HEADLESS=false` nếu TikTok thường yêu cầu CAPTCHA. Khi CAPTCHA hiện ra, xử lý trong Chrome; bot sẽ chờ tối đa `CAPTCHA_WAIT_SECONDS`.
- Không mở đồng thời `setup_browser.py` và bot vì Chrome không cho hai tiến trình dùng cùng một profile. Cũng không nhấn Enter để dừng setup; hãy đóng Chrome để cookie được ghi đầy đủ.
- Giao diện TikTok có thể thay đổi. Crawler đã có fallback qua JSON, Open Graph và DOM selector, nhưng selector có thể cần cập nhật về sau.
