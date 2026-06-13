# Kịch bản kiểm thử hệ thống HRM AI (Test Scenario Walkthrough)

Tài liệu này hướng dẫn chi tiết từng bước thực hiện kiểm thử các tính năng AI của ứng dụng trên giao diện **Next.js** tại địa chỉ **`http://localhost:3000`**.

---

## KỊCH BẢN 1: KIỂM THỬ SÀNG LỌC CV & TỰ ĐỘNG HÓA TUYỂN DỤNG (CV SCREENING)

### **Mục tiêu**: 
Kiểm tra khả năng bóc tách CV, tính điểm tương hợp (Match score), kiểm tra so khớp kỹ năng, kiểm tra trích xuất thông tin liên hệ và tự động soạn thảo email phản hồi dựa trên trạng thái ứng viên.

### **Các bước thực hiện**:

#### **Bước 1: Khởi tạo và thiết lập Chiến dịch (Campaign)**
1. Mở trình duyệt và truy cập **`http://localhost:3000/cv-screening`**.
2. Tại cột bên trái **1) Campaign**:
   - Chọn mục **(Tạo mới)** từ danh sách dropdown.
   - Nhập tên chiến dịch mới (Ví dụ: `Tuyển dụng Kỹ sư Python Backend 2026`).
   - Nhấn nút **Tạo Campaign mới**.
3. Hệ thống sẽ tự động chuyển sang cấu hình cho Campaign mới tạo.

#### **Bước 2: Tải lên Mô tả công việc (JD)**
1. Tại phần **2) Upload & Ingest**, mục **Tài liệu JD tuyển dụng (PDF/TXT)**:
   - Click chọn file JD bạn đã chuẩn bị sẵn (ví dụ: `jd_python_backend.txt`).
   - Nhấp nút **Upload JD**.
   - Quan sát thông báo ở thanh tiêu đề xem job parse JD có chạy thành công và báo trạng thái `DONE` không.

#### **Bước 3: Tải lên danh sách hồ sơ ứng viên (CVs)**
1. Vẫn tại phần **2) Upload & Ingest**, mục **Tập tin CVs (Nhiều PDF)**:
   - Click chọn đồng thời từ 3-5 file CV ứng viên mà bạn đã chuẩn bị.
   - Nhấp nút **Upload CVs**.
   - Trạng thái xử lý job sẽ hiển thị dạng tag nhỏ màu xanh ở góc phải thanh Header. Hãy đợi khoảng 5-10 giây cho đến khi job báo trạng thái `DONE`.

#### **Bước 4: Cấu hình chấm điểm quy tắc (Campaign Settings)**
1. Ở phần **3) Campaign Settings** bên sidebar trái:
   - Kéo thanh slider **Trọng số Embed** về mức `0.70` (Mặc định).
   - Ô **Các kỹ năng yêu cầu**: Nhập các từ khóa kỹ năng quan trọng của JD (Ví dụ: `python, fastapi, docker, postgresql`).
   - Ô **Kinh nghiệm tối thiểu**: Nhập mức `2` (Năm).
   - Nhấp nút **Lưu cấu hình**.

#### **Bước 5: Chạy sàng lọc và Đánh giá xếp hạng**
1. Tại khu vực chính màn hình, nhấp nút **🚀 Bắt đầu Sàng Lọc**.
2. Đợi cho tiến trình job (ở header) kết thúc (`DONE`).
3. Nhấp nút **Xem Xếp Hạng** để tải dữ liệu về bảng.
4. **Kiểm tra kết quả**:
   - Bảng xếp hạng sẽ hiện ra danh sách các ứng viên.
   - CV nào khớp các tiêu chí tốt nhất (nhiều skill, đủ số năm kinh nghiệm) sẽ được xếp lên trên cùng với cột **Score Total** cao nhất.
   - CV không liên quan (như CV Sales) sẽ bị xếp ở cuối với điểm số cực thấp.

#### **Bước 6: Xem chi tiết ứng viên (Drill-down)**
1. Nhấp chuột vào một dòng ứng viên bất kỳ trên bảng để mở phần thông tin chi tiết (Candidate Drill-down) phía dưới.
2. **Kiểm tra các Tab**:
   - **Tab Evidence**: Xem các đoạn trích từ CV gốc làm căn cứ để AI tính điểm.
   - **Tab Rules**: Xem bảng kiểm lỗi điều kiện logic (Checklist skills/năm kinh nghiệm).
   - **Tab Review**: 
     - Nhấp nút **Khởi chạy Review** rồi đợi job chạy xong.
     - Nhấp **Lấy kết quả Review** để xem tóm tắt thế mạnh (Strengths) và điểm yếu (Gaps) do Llama3 phân tích.
   - **Tab Profile**:
     - Nhấp nút **Bóc tách Profile** rồi đợi job chạy xong.
     - Nhấp **Lấy kết quả & Radar Chart** để xem thông tin liên hệ (Email, SĐT) tự bóc tách và sơ đồ Radar Match.

#### **Bước 7: Email Automation**
1. Chọn **Tab 📧 Email Automation** của ứng viên đang xem.
2. Hãy thử thay đổi trạng thái của ứng viên (ví dụ: đổi từ `Applied` sang `Interviewing` hoặc `Rejected`).
3. Tại dropdown chọn **Loại thư phản hồi** (ví dụ: `Mời phỏng vấn` hoặc `Thư từ chối`).
4. Nhấn nút **Soạn Email bằng AI**.
5. **Kiểm tra kết quả**:
   - Đọc bản nháp email được sinh ra ở ô bên phải.
   - Kiểm tra xem AI có tự cá nhân hóa đúng tên ứng viên, vị trí tuyển dụng, và đề cập một cách khéo léo tới thế mạnh/điểm yếu của ứng viên hay không.

---

## KỊCH BẢN 2: KIỂM THỬ TRỢ LÝ TRÀ CỨU CHÍNH SÁCH NỘI BỘ (POLICY CHATBOT)

### **Mục tiêu**:
Kiểm tra khả năng nạp dữ liệu chính sách, cơ chế tìm kiếm văn bản liên quan có lai ghép (Hybrid Reranker), khả năng chat nhớ ngữ cảnh và hiển thị nguồn đối chiếu chính xác.

### **Các bước thực hiện**:

#### **Bước 1: Tải lên tài liệu chính sách**
1. Truy cập **`http://localhost:3000/policy-chat`**.
2. Tại cột bên trái:
   - Kéo thả hoặc click chọn file quy định bạn đã chuẩn bị (ví dụ: file `.docx` hoặc `.pdf` chứa quy chế đi muộn, nghỉ phép).
   - Hệ thống sẽ tự động xếp hàng và xử lý cắt lát (chunking) lưu vào DB vector.
   - Đợi cột trạng thái bên cạnh tên file hiển thị nút tròn xanh lá (`🟢 OK`).

#### **Bước 2: Thử nghiệm lọc nguồn tài liệu**
1. Chọn (tick chọn) vào file tài liệu bạn vừa tải lên ở danh sách tài liệu bên sidebar trái.
2. *Lưu ý*: Việc tick chọn này bắt buộc chatbot chỉ được phép đọc file này để trả lời câu hỏi của bạn.

#### **Bước 3: Đặt câu hỏi thử nghiệm**
1. Tại thanh chat phía dưới màn hình, gõ câu hỏi liên quan trực tiếp đến nội dung trong file chính sách của bạn.
   - *Ví dụ 1*: *"Tôi đi muộn quá bao nhiêu phút thì bị phạt?"*
   - *Ví dụ 2*: *"Quy định về xin nghỉ ốm cần những giấy tờ gì?"*
2. Nhấn nút gửi (Send).
3. **Kiểm tra kết quả**:
   - Trình duyệt sẽ nhận stream văn bản trả về từng chữ một (Hiệu ứng typing).
   - **Hiển thị nguồn đối chiếu (Citations)**: Bên dưới câu trả lời của chatbot, kiểm tra xem có xuất hiện ô thông tin trích dẫn nguồn đính kèm (chỉ rõ câu trả lời được lấy từ file nào, phần trăm độ tương đồng bao nhiêu, và hiển thị trích đoạn văn bản gốc).

#### **Bước 4: Thử nghiệm tính nhớ ngữ cảnh (Chat history)**
1. Tiếp tục đặt câu hỏi ngắn gọn mà không cần nhắc lại chủ ngữ của câu hỏi trước.
   - *Ví dụ*: Sau câu hỏi về nghỉ phép, hãy hỏi tiếp: *"Còn nếu tự ý nghỉ không phép thì sao?"*.
2. **Kiểm tra kết quả**: Chatbot phải hiểu từ "nghỉ không phép" ở đây là đang tiếp nối câu chuyện nghỉ phép ở phía trên và đưa ra câu trả lời dựa trên đúng quy chế kỷ luật của tài liệu đã chọn.
