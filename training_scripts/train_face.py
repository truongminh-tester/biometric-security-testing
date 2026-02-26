# Tệp: training_scripts/train_face.py (Bản sửa lỗi Memory Contiguous)
import face_recognition
import os
import pickle
import numpy as np
import cv2
import sys
sys.stdout.reconfigure(encoding='utf-8')

# --- XÁC ĐỊNH ĐƯỜNG DẪN ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
# -----------------------------

print("[INFO] Bắt đầu quá trình mã hóa khuôn mặt...")

# --- THIẾT LẬP ---
dataset_path = os.path.join(PROJECT_DIR, "dataset", "face")
encodings_file = os.path.join(PROJECT_DIR, "models", "encodings.pickle")

known_encodings = []
known_names = []

print(f"[INFO] Đọc dữ liệu từ thư mục: {dataset_path}")

# Lặp qua từng thư mục con
for person_name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person_name)
    
    if not os.path.isdir(person_path):
        continue

    print(f"[INFO] Đang xử lý cho: {person_name}")
    
    # Lặp qua từng ảnh
    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)
        
        try:
            # 1. Đọc file bằng cv2 (ra BGR, uint8)
            image_bgr = cv2.imread(img_path)
            
            if image_bgr is None:
                print(f"[CẢNH BÁO] cv2 không đọc được file, bỏ qua: {img_name}")
                continue
            
            # 2. Chuyển sang RGB
            rgb_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            # 3. Đảm bảo mảng "liền mạch" (C-contiguous) cho Dlib
            rgb_image_contiguous = np.ascontiguousarray(rgb_image)

            # 4. Tìm vị trí khuôn mặt
            boxes = face_recognition.face_locations(rgb_image_contiguous, model="hog")
            
            # 5. Mã hóa
            encodings = face_recognition.face_encodings(rgb_image_contiguous, boxes)
        
        except Exception as e:
            print(f"[CẢNH BÁO] Lỗi không mong muốn khi xử lý: {img_name} (Lỗi: {e})")
            continue

        # 6. Lưu kết quả
        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)

if not known_encodings:
    print("[CẢNH BÁO] Không tìm thấy hoặc không mã hóa được bất kỳ khuôn mặt nào.")
else:
    print(f"[INFO] Đã mã hóa thành công {len(known_encodings)} khuôn mặt.")

print(f"[INFO] Lưu trữ dữ liệu mã hóa vào: {encodings_file}")
data = {"encodings": known_encodings, "names": known_names}

with open(encodings_file, "wb") as f:
    pickle.dump(data, f)

print("[INFO] Hoàn tất huấn luyện!")