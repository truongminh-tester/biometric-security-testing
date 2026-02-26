# Tệp: qa_automation/test_ui.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_ui_login_flow():
    print("🚀 Khởi động trình duyệt Chrome...")
    # Yêu cầu đã cài: pip install selenium
    driver = webdriver.Chrome()
    
    try:
        # 1. Mở trang web mục tiêu
        driver.get("http://127.0.0.1:5000")
        driver.maximize_window()
        
        # Đợi trang tải xong phần tử input username
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        # 2. Tự động nhập tên người dùng
        print("✍️ Đang nhập tên người dùng (Test_User)...")
        username_input = driver.find_element(By.ID, "username")
        username_input.send_keys("Test_User")
        time.sleep(1)

        # 3. Tự động chuyển sang Tab "Giọng nói"
        print("🖱️ Chuyển sang Tab Giọng nói...")
        voice_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Giọng')]")
        voice_tab.click()
        time.sleep(1)

        # 4. Tự động bấm nút Ghi âm
        print("🎙️ Bấm nút Ghi âm...")
        record_btn = driver.find_element(By.ID, "recordButton")
        record_btn.click()
        
        # Đợi 5 giây để giả lập thời gian thu âm
        time.sleep(5)
        
        print("✅ Đã hoàn thành kịch bản thao tác UI cơ bản!")
        
    except Exception as e:
        print(f"❌ Lỗi UI Test: {e}")
    finally:
        print("🛑 Tự động đóng trình duyệt sau 3 giây.")
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    test_ui_login_flow()