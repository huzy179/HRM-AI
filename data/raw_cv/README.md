# CV samples

Đặt 5–10 file CV dạng PDF vào thư mục này để test Phase 1.

- Không commit CV thật lên git.
- File sẽ bị ignore bởi `.gitignore` (ví dụ: `data/raw_cv/*.pdf`).

Lưu ý:
- Nếu PDF là dạng scan (ảnh) thì parser sẽ báo `EMPTY_TEXT_NEEDS_OCR`.
- Repo đã có OCR fallback trong `backend/services/cv_parser.py`.
  - Nếu chạy bằng Docker: Tesseract đã được đóng gói trong image.
  - Nếu chạy local (không dùng Docker): cần cài Tesseract ngoài hệ điều hành + `pytesseract`.

Gợi ý đặt tên:
- `cv_01.pdf`, `cv_02.pdf`, ...
