# Tệp: qa_automation/test_api.py
import requests
import base64

BASE_URL = "http://127.0.0.1:5000"

# Chuỗi Base64 giả lập để test (thay thế cho ảnh thật)
DUMMY_BASE64_IMG = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/..."

def test_login_face_missing_data():
    """Test Case 1: Kiểm tra API /login_face khi gửi thiếu dữ liệu ảnh"""
    print("⏳ Running Test 1: Login Face (Missing Data)...", end=" ")
    response = requests.post(f"{BASE_URL}/login_face", json={"username": "Minh"})
    
    assert response.status_code == 200
    assert response.json()['success'] == False
    assert "Thiếu thông tin" in response.json()['message']
    print("✅ PASSED")

def test_login_voice_missing_audio():
    """Test Case 2: Kiểm tra API /login_voice khi gửi thiếu file ghi âm"""
    print("⏳ Running Test 2: Login Voice (Missing Audio)...", end=" ")
    payload = {'username': 'Minh', 'evidence_image': DUMMY_BASE64_IMG}
    
    # Gửi request nhưng KHÔNG đính kèm file audio_data
    response = requests.post(f"{BASE_URL}/login_voice", data=payload)
    
    assert response.status_code == 200
    assert response.json()['success'] == False
    assert "Thiếu thông tin" in response.json()['message']
    print("✅ PASSED")

def test_login_fingerprint_unregistered():
    """Test Case 3: Kiểm tra API /login_fingerprint với user chưa tồn tại"""
    print("⏳ Running Test 3: Fingerprint (Unregistered User)...", end=" ")
    payload = {"username": "Hacker_007", "image": DUMMY_BASE64_IMG}
    
    response = requests.post(f"{BASE_URL}/login_fingerprint", json=payload)
    
    assert response.status_code == 200
    assert response.json()['success'] == False
    assert "chưa đăng ký" in response.json()['message']
    print("✅ PASSED")

if __name__ == "__main__":
    print("==================================================")
    print("🚀 BẮT ĐẦU CHẠY AUTOMATION TEST API")
    print("==================================================")
    try:
        test_login_face_missing_data()
        test_login_voice_missing_audio()
        test_login_fingerprint_unregistered()
        print("--------------------------------------------------")
        print("🎉 TOÀN BỘ TEST CASE ĐÃ PASS!")
    except ConnectionError:
        print("❌ LỖI: Không thể kết nối đến Server. Hãy chắc chắn app.py đang chạy!")
    except AssertionError as e:
        print(f"❌ FAILED: Lỗi logic hoặc API trả về sai cấu trúc! Chi tiết: {e}")