==============================================================================
HỆ THỐNG XÁC THỰC SINH TRẮC HỌC & GIÁM SÁT AN NINH (WEB VERSION)
==============================================================================

0. GIỚI THIỆU
   Hệ thống Web App cho phép Đăng ký, Đăng nhập và Giám sát bằng 4 phương thức:
   1. Khuôn mặt (Face): Sử dụng Webcam & HOG/CNN (Tích hợp nhận diện đám đông).
   2. Giọng nói (Voice): Ghi âm qua trình duyệt & MFCC/GMM (Lưu bằng chứng kép).
   3. Vân tay (Fingerprint): Tải ảnh vân tay & thuật toán ORB.
   4. Mống mắt (Iris): Tải ảnh mống mắt & thuật toán ORB.
   * Tính năng mở rộng (SOC Dashboard): Ghi lại Audit Log và lưu trữ bằng chứng xâm nhập.
   * Tích hợp bộ tài liệu Kiểm thử (QA/Automation Test).

1. CÀI ĐẶT MÔI TRƯỜNG
   Bước 1: Cài đặt Python 3.11 (hoặc 3.9).
   Bước 2: Cài đặt FFmpeg (bắt buộc cho xử lý âm thanh).
           - Tải từ: https://ffmpeg.org/download.html
           - Thêm thư mục 'bin' của FFmpeg vào biến môi trường PATH.
   Bước 3: Cài đặt thư viện Python:
           >> pip install -r requirements.txt

2. CẤU TRÚC THƯ MỤC
   Biometrics/
   ├── app.py                 # Server chính (Flask) + Cấu hình bypass max_payload
   ├── requirements.txt       # Danh sách thư viện
   ├── audit_logs.json        # Database lưu lịch sử truy cập (Dashboard)
   ├── dataset/               # Chứa dữ liệu thô (ảnh/âm thanh)
   ├── models/                # Chứa file .pickle (AI Model đã train)
   ├── static/
   │   └── intruders/         # Nơi lưu Bằng chứng xâm nhập (Ảnh & WAV của kẻ gian)
   ├── templates/             # Giao diện Web (HTML)
   │   ├── index.html         # Trang Đăng nhập
   │   ├── dashboard.html     # Trang SOC Dashboard (Xem log & Nghe ghi âm)
   │   └── register_*.html    # Các trang đăng ký
   ├── training_scripts/      # Kịch bản huấn luyện (được gọi bởi app.py)
   ├── qa_automation/         # Kịch bản Automation Test (Dành cho Tester)
   │   └── test_api.py
   └── docs/                  # Tài liệu Kiểm thử & Báo cáo
       ├── Biometric_Test_Cases.xlsx
       └── BUG_REPORT.md

3. HƯỚNG DẪN SỬ DỤNG

   A. Khởi chạy Server:
      Mở terminal tại thư mục dự án và chạy:
      >> python app.py
      Truy cập địa chỉ: http://127.0.0.1:5000/

   B. Quy trình Đăng ký (Bắt buộc cho người mới):
      1. Tại trang chủ, nhấn link "Chưa có tài khoản? Đăng ký ngay!".
      2. Chọn phương thức muốn đăng ký (ví dụ: Mống mắt).
      3. Nhập tên (viết liền không dấu, ví dụ: Minh).
      4. Thực hiện thu thập dữ liệu (Chụp ảnh/Ghi âm/Upload).
      5. Hệ thống sẽ TỰ ĐỘNG huấn luyện (Train) và cập nhật model.
      6. Sau khi xong, bạn sẽ được chuyển về trang Đăng nhập.

   C. Quy trình Đăng nhập & Giám sát (Dashboard):
      1. Nhập tên người dùng và chọn phương thức xác thực.
      2. Thực hiện xác thực (hệ thống sẽ hiển thị ảnh phân tích đặc trưng với Vân tay/Mống mắt).
      3. Nếu thành công -> Tự động chuyển hướng vào màn hình Dashboard xem Log.
      4. Nếu thất bại -> Hệ thống từ chối, đồng thời lưu Bằng chứng (Ảnh/Voice) vào Dashboard.

   D. Chạy kiểm thử tự động (Automation Test):
      Mở một terminal khác và chạy:
      >> python qa_automation/test_api.py

4. LƯU Ý QUAN TRỌNG & BẢO MẬT
   - Anti-Spoofing: Hệ thống có bộ lọc hình học. Không thể dùng ảnh mắt để đăng nhập vào tab vân tay (và ngược lại).
   - Payload Size: Server đã được cấu hình nới rộng MAX_CONTENT_LENGTH lên 200MB để xử lý ảnh Base64 độ phân giải cao, tránh lỗi HTTP 413.
   - Xóa lịch sử: Để làm sạch Dashboard, cần làm rỗng file `audit_logs.json` (thành `[]`) và xóa các file trong thư mục `static/intruders/`.

==============================================================================