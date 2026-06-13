# Danh sách tài liệu chuẩn bị kiểm thử (Test Documents Specification)

Để quá trình kiểm thử các tính năng AI của hệ thống **HRM AI** đạt hiệu quả cao nhất (bao gồm cả CV Screening và Policy Chatbot), bạn nên chuẩn bị các tài liệu mẫu theo đặc tả dưới đây:

---

## 1. Tài liệu phục vụ tính năng "CV Screening & Ranking"

Bạn cần chuẩn bị 1 Job Description (JD) và ít nhất 3-5 CV của các ứng viên khác nhau để xem rõ độ lệch điểm số (Ranking) và phân tích biểu đồ kỹ năng.

### 1.1. Bản mô tả công việc (Job Description - JD)
*   **Định dạng file phù hợp**: `.pdf` hoặc `.txt`.
*   **Gợi ý nội dung mẫu**:
    *   Nên ghi rõ **Tên vị trí** (Ví dụ: *Kỹ sư phát triển Python Backend* hoặc *React Frontend Developer*).
    *   **Yêu cầu kỹ thuật chính (Skills)**: Nên ghi rõ các từ khóa kỹ năng để AI đối chiếu (Ví dụ: `Python`, `FastAPI`, `Docker`, `SQL`, `Redis`, `Next.js`, `Tailwind CSS`).
    *   **Số năm kinh nghiệm yêu cầu**: Ví dụ *tối thiểu 2 năm kinh nghiệm*.
    *   **Mô tả công việc (JD)**: Các đầu việc rõ ràng để AI lấy dữ liệu bóc tách.

### 1.2. Danh sách CV Ứng viên (Candidates CVs)
Chuẩn bị **ít nhất 3 CV** với các mức độ phù hợp khác nhau để thử nghiệm thuật toán xếp hạng:
*   **CV 1 (Match tốt - Top 1)**: 
    *   Chứa đầy đủ các từ khóa kỹ năng của JD (Ví dụ: Có đề cập kinh nghiệm làm việc với Python, FastAPI, Docker, Postgres).
    *   Kinh nghiệm làm việc ghi rõ hơn 3 năm (đáp ứng điều kiện kinh nghiệm).
*   **CV 2 (Match trung bình - Top 2-3)**:
    *   Kỹ năng có trùng một số phần, nhưng thiếu các phần quan trọng (Ví dụ: Có Python nhưng không có FastAPI hay Docker).
    *   Kinh nghiệm khoảng 1-2 năm.
*   **CV 3 (CV Lệch hướng / Trượt - Rejected)**:
    *   Nội dung của một ngành nghề khác hoàn toàn (Ví dụ: CV Nhân viên bán hàng - Sales, Marketing) để kiểm tra xem hệ thống có chấm điểm cực thấp hoặc tự động gợi ý Reject hay không.
*   **CV 4 (CV dạng File quét ảnh - Scanned PDF)**:
    *   Thử nghiệm tính năng OCR: Dùng một file CV được xuất ra từ file ảnh quét để kiểm tra khả năng nhận diện chữ qua Tesseract OCR của worker.

---

## 2. Tài liệu phục vụ tính năng "Policy Chatbot & RAG"

Chuẩn bị các tài liệu quy chế nội bộ của công ty để chatbot truy vấn thông tin chính xác.

### 2.1. Quy chế làm việc & Kỷ luật lao động
*   **Định dạng**: `.pdf`, `.docx` hoặc `.md`.
*   **Nội dung mẫu cần có**:
    *   **Giờ giấc làm việc**: Quy định giờ check-in (Ví dụ: *8:30 sáng*), check-out (*17:30 chiều*). Số phút đi muộn tối đa được phép.
    *   **Quy định trang phục**: Ví dụ *mặc lịch sự từ thứ 2 đến thứ 5, thứ 6 được tự do*.
    *   **Các hình thức kỷ luật**: Khi vi phạm đi muộn hoặc làm việc riêng.

### 2.2. Chính sách phúc lợi, nghỉ phép & bảo hiểm
*   **Định dạng**: `.pdf`, `.docx` hoặc `.txt`.
*   **Nội dung mẫu cần có**:
    *   **Số ngày phép**: Quy định mỗi nhân viên chính thức có *12 ngày phép năm*. Cơ chế dồn phép sang năm sau.
    *   **Mức hỗ trợ phụ cấp**: Tiền ăn trưa (Ví dụ: *500.000 VNĐ/tháng*), tiền gửi xe (Ví dụ: *150.000 VNĐ/tháng*).
    *   **Quy trình xin nghỉ ốm**: Cần giấy tờ gì đối chiếu (ví dụ: Giấy xác nhận của bệnh viện/bảo hiểm xã hội).

---

## 3. Thư mục chuẩn bị tài liệu gợi ý
Bạn nên gom toàn bộ các file này vào một thư mục riêng trên máy tính (ví dụ: `C:\TestDocuments\`) để dễ dàng kéo thả và upload lên hệ thống khi bắt đầu kiểm thử.
