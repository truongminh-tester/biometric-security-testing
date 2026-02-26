# Tệp: training_scripts/train_fingerprint.py (Đã sửa - Tối ưu cho Vân tay)
import os
import pickle
import cv2
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

# --- XÁC ĐỊNH ĐƯỜNG DẪN ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
# -----------------------------

# --- THIẾT LẬP ---
dataset_path = os.path.join(PROJECT_DIR, "dataset", "fingerprint")
models_file = os.path.join(PROJECT_DIR, "models", "fingerprint_models.pickle")
# -----------------

print("[INFO] Bắt đầu huấn luyện mô hình vân tay (ORB)...")
print(f"[INFO] Đọc dữ liệu từ thư mục: {dataset_path}")

all_models = {}
try:
    # Đồng bộ tham số nfeatures=1000
    orb = cv2.ORB_create(nfeatures=1000) 
except Exception:
    print("\n[LỖI] Không thể tạo ORB. Thư viện OpenCV của bạn có thể bị thiếu.")
    exit()

if not os.path.exists(dataset_path):
    print(f"[LỖI] Không tìm thấy thư mục dữ liệu: {dataset_path}")
    exit()

# Lặp qua từng người
for person_name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person_name)
    if not os.path.isdir(person_path): continue

    print(f"[INFO] Đang xử lý cho: {person_name}")
    descriptors_list = []
    
    for file_name in os.listdir(person_path):
        if not file_name.lower().endswith(('.jpg', '.png', '.bmp', '.jpeg')): continue
        
        file_path = os.path.join(person_path, file_name)
        # Đọc ảnh xám
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            print(f"[CẢNH BÁO] Không thể đọc file ảnh, bỏ qua: {file_path}")
            continue

        # --- [SỬA ĐỔI QUAN TRỌNG] ---
        # 1. Bỏ GaussianBlur (Làm mờ vân tay)
        # gray_image = cv2.GaussianBlur(image, (5, 5), 0)
        
        # 2. Thay bằng EqualizeHist (Tăng tương phản)
        # Giúp vân tay đen đậm hơn trên nền trắng, ORB dễ bắt hơn
        gray_image = cv2.equalizeHist(image)
        # ----------------------------
        
        kp, des = orb.detectAndCompute(gray_image, None)
        
        if des is not None:
            descriptors_list.append(des)
            
    if not descriptors_list:
        print(f"[CẢNH BÁO] Không tìm thấy đặc trưng nào cho {person_name} (Ảnh quá mờ?)")
        continue

    # Gộp tất cả đặc trưng lại
    all_descriptors_for_person = np.vstack(descriptors_list)
    all_models[person_name] = all_descriptors_for_person
    print(f"[INFO] Đã huấn luyện xong cho {person_name} (Số lượng features: {len(all_descriptors_for_person)})")

# Lưu model
with open(models_file, 'wb') as f:
    pickle.dump(all_models, f)

print(f"\n[INFO] Hoàn tất huấn luyện vân tay! Đã lưu vào {models_file}")