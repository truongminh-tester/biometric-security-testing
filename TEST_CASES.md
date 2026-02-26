==============================================================================
TÀI LIỆU KIỂM THỬ (TEST CASES) - HỆ THỐNG XÁC THỰC SINH TRẮC HỌC
==============================================================================

| ID | Chức năng (Feature) | Kịch bản kiểm thử (Test Scenario) | Các bước thực hiện (Steps) | Dữ liệu đầu vào (Input) | Kết quả mong đợi (Expected Result) | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC_SEC_01** | Vân tay (Security) | Kiểm tra chống giả mạo vân tay bằng hình ảnh mắt | 1. Chọn tab Vân tay<br>2. Upload ảnh mống mắt<br>3. Bấm xác thực | Ảnh mống mắt (Iris image) | Hệ thống từ chối và hiển thị lỗi: "⛔ CẢNH BÁO: Phát hiện MẮT giả dạng Vân tay!" | ✅ PASS |
| **TC_FUNC_02** | Khuôn mặt (Functional) | Kiểm tra nhận diện khi có nhiều khuôn mặt trong ảnh | 1. Chọn tab Khuôn mặt<br>2. Đưa ảnh có 3 người vào camera<br>3. Bấm xác thực | Ảnh webcam chứa 3 khuôn mặt (có chủ tài khoản) | Hệ thống quét toàn bộ, nhận diện đúng chủ tài khoản trong đám đông và cho phép đăng nhập. | ✅ PASS |
| **TC_DATA_03** | Giọng nói (Data Integrity) | Kiểm tra lưu bằng chứng kép khi đăng nhập giọng nói thất bại | 1. Nhập username đúng<br>2. Ghi âm bằng giọng người khác<br>3. Kiểm tra Dashboard | Giọng nói sai (Score < Threshold) | Web báo lỗi. Tại Dashboard, dòng log FAILED có hiển thị đầy đủ Nút "Xem ảnh" và Thanh Audio để nghe lại. | ✅ PASS |
| **TC_PERF_04** | Giọng nói (Performance) | Kiểm tra xử lý gói dữ liệu Payload lớn | 1. Nhập username<br>2. Upload ảnh webcam độ phân giải Full HD cực nặng kèm âm thanh | Gói tin Payload > 10MB | Hệ thống xử lý mượt mà, không bị văng lỗi 413 (Request Entity Too Large) hay sập Server. | ✅ PASS |
| **TC_API_05** | API Validation | Bắt lỗi thiếu thông tin qua API | Gửi POST request đến `/login_face` với payload rỗng | Payload: `{}` | Server không sập. Trả về chuẩn JSON: `{"success": false, "message": "Thiếu thông tin."}` | ✅ PASS |

==============================================================================
*Lưu ý: Các test case API đã được tự động hóa toàn bộ trong kịch bản `tests/test_api.py`.*