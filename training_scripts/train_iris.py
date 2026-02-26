# Tệp: training_scripts/train_iris.py
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
# Đường dẫn đến thư mục chứa ảnh mống mắt (dataset/iris)
dataset_path = os.path.join(PROJECT_DIR, "dataset", "iris")
# Đường dẫn lưu model
models_file = os.path.join(PROJECT_DIR, "models", "iris_models.pickle")
# -----------------

print("[INFO] Bắt đầu huấn luyện mô hình mống mắt (Simulated via ORB)...")
print(f"[INFO] Đọc dữ liệu từ thư mục: {dataset_path}")

all_models = {}

# Khởi tạo thuật toán ORB (Đồng bộ tham số nfeatures=1000 với app.py)
try:
    orb = cv2.ORB_create(nfeatures=1000)
except Exception:
    print("\n[LỖI] Không thể tạo ORB. Hãy cài đặt: pip install opencv-contrib-python")
    exit()

# Kiểm tra thư mục dataset
if not os.path.exists(dataset_path):
    print(f"[LỖI] Không tìm thấy thư mục: {dataset_path}")
    print("Vui lòng tạo thư mục và thêm ảnh vào 'dataset/iris/<TenNguoi>/'")
    exit()

# Lặp qua từng người dùng
for person_name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person_name)
    if not os.path.isdir(person_path): continue

    print(f"[INFO] Đang xử lý cho: {person_name}")
    descriptors_list = []
    
    # Lặp qua từng ảnh của người đó
    for file_name in os.listdir(person_path):
        if not file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')): 
            continue
        
        file_path = os.path.join(person_path, file_name)
        
        # Đọc ảnh dưới dạng XÁM (Grayscale) để tối ưu cho ORB
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            print(f"[CẢNH BÁO] Không thể đọc file ảnh: {file_name}")
            continue

        # Tiền xử lý: Làm mờ nhẹ để giảm nhiễu (giống vân tay)
        # Giúp loại bỏ các chi tiết thừa như lông mi, phản xạ nhỏ
        gray_image = cv2.GaussianBlur(image, (5, 5), 0)
        
        # Trích xuất đặc trưng (Keypoints & Descriptors)
        kp, des = orb.detectAndCompute(gray_image, None)
        
        if des is not None:
            descriptors_list.append(des)
            
    if not descriptors_list:
        print(f"[CẢNH BÁO] Không tìm thấy đặc trưng nào cho {person_name} (Ảnh quá mờ hoặc quá tối?)")
        continue

    # Gộp tất cả đặc trưng lại thành một "siêu mẫu" cho người đó
    all_descriptors_for_person = np.vstack(descriptors_list)
    all_models[person_name] = all_descriptors_for_person
    print(f"[INFO] Đã huấn luyện xong cho {person_name} (Số lượng đặc trưng: {len(all_descriptors_for_person)})")

# Lưu model vào file pickle
with open(models_file, 'wb') as f:
    pickle.dump(all_models, f)

print(f"\n[INFO] Hoàn tất! Model mống mắt đã lưu tại: {models_file}")