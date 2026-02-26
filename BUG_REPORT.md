==============================================================================
BÁO CÁO SỰ CỐ (BUG REPORT) - LỖI VƯỢT QUÁ DUNG LƯỢNG PAYLOAD (HTTP 413)
==============================================================================

0. THÔNG TIN CHUNG
   - Mã lỗi (Bug ID): BUG-API-0413
   - Mức độ nghiêm trọng (Severity): Cao (High) - Gây gián đoạn luồng đăng nhập.
   - Người báo cáo / Khắc phục: Minh (QA/Dev)
   - Trạng thái: Đã khắc phục (Resolved).
   - Nền tảng: Web (Flask Backend).

1. MÔ TẢ SỰ CỐ
   Trong quá trình kiểm thử tính năng Đăng nhập bằng Giọng nói (Voice Login), khi hệ thống cố gắng lưu "Bằng chứng kép" (bao gồm file ghi âm .webm và ảnh chụp webcam định dạng chuỗi Base64), Frontend trình duyệt báo lỗi:
   "SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON"
   Kiểm tra log Backend, Server Flask ngắt kết nối API và ném ra lỗi HTTP 413 (Request Entity Too Large).

2. CÁC BƯỚC TÁI HIỆN (STEPS TO REPRODUCE)
   Bước 1: Khởi động hệ thống với cấu hình Flask mặc định.
   Bước 2: Tại Client, chọn tab "Giọng nói" và sử dụng Webcam có độ phân giải cao (HD/Full HD).
   Bước 3: Bấm Ghi âm (Hệ thống ngầm chụp 1 frame ảnh Base64 gửi kèm Audio).
   Bước 4: Gửi POST request đến API /login_voice.
   Bước 5: Quan sát Console Tab (F12) trên trình duyệt và Terminal của Server.

3. PHÂN TÍCH NGUYÊN NHÂN (ROOT CAUSE)
   - Về phía Backend: Framework Flask có cơ chế tự vệ mặc định, giới hạn dung lượng Request Body ở mức rất thấp (khoảng 500KB cho Text Form) để chống tấn công DoS.
   - Về phía Payload: Một bức ảnh webcam Full HD khi mã hóa sang chuỗi Base64 có thể phình to lên mức 5MB - 10MB.
   - Hậu quả: Gói dữ liệu vượt quá giới hạn bộ nhớ Text (MAX_FORM_MEMORY_SIZE) và tổng dung lượng (MAX_CONTENT_LENGTH). Server Flask lập tức từ chối Request, trả về một trang HTML báo lỗi (Mã 413) thay vì JSON. Frontend cố gắng parse chuỗi HTML này thành JSON nên gây ra lỗi SyntaxError.

4. GIẢI PHÁP KHẮC PHỤC (RESOLUTION)
   Can thiệp vào Application Config của Flask trong file app.py để định tuyến lại giới hạn bộ nhớ, cho phép xử lý các gói tin chứa hình ảnh và âm thanh chất lượng cao phục vụ lưu vết bằng chứng.

   [Code đã sửa trong app.py]
   # Tăng tổng dung lượng gói tin cho phép lên 200MB
   app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 

   # Gỡ bỏ giới hạn bộ nhớ đệm cho các trường Form (Base64 String không bị tràn RAM)
   app.config['MAX_FORM_MEMORY_SIZE'] = None 
   app.config['MAX_FORM_PARTS'] = None

5. KẾT QUẢ KIỂM THỬ (TEST RESULT)
   - Kịch bản Payload > 15MB: Hệ thống tiếp nhận thành công, không còn lỗi 413 hay SyntaxError.
   - File ghi âm (.wav) và ảnh (.jpg) của kẻ xâm nhập được lưu nguyên vẹn vào thư mục static/intruders/.
   - Log cảnh báo được đẩy lên Dashboard đầy đủ.

==============================================================================