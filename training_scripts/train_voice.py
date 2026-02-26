# Tệp: training_scripts/train_voice.py (Phiên bản Nâng cấp - Tự động nhân bản dữ liệu)
import os
import pickle
import numpy as np
import librosa
import librosa.effects
from sklearn.mixture import GaussianMixture as GMM
import sys

sys.stdout.reconfigure(encoding='utf-8')

# --- XÁC ĐỊNH ĐƯỜNG DẪN ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# --- THIẾT LẬP ---
dataset_path = os.path.join(PROJECT_DIR, "dataset", "voice")
models_file = os.path.join(PROJECT_DIR, "models", "voice_models.pickle")
N_COMPONENTS = 64 
TARGET_SR = 16000

# -------------------------------------------------------------------
# HÀM TRÍCH XUẤT MFCC TỪ TÍN HIỆU ÂM THANH
# -------------------------------------------------------------------
def extract_features(y, sr):
    y_trimmed, _ = librosa.effects.trim(y, top_db=25)
    if y_trimmed.size > 0:
        mfcc = librosa.feature.mfcc(y=y_trimmed, sr=sr, n_mfcc=20)
        # Tính thêm Delta và Delta-Delta
        delta_mfcc = librosa.feature.delta(mfcc)
        delta2_mfcc = librosa.feature.delta(mfcc, order=2)
        # Gộp tất cả lại thành bộ đặc trưng 60 chiều
        combined = np.vstack([mfcc, delta_mfcc, delta2_mfcc])
        return combined.T
    return None

# -------------------------------------------------------------------
# BẮT ĐẦU HUẤN LUYỆN
# -------------------------------------------------------------------
print("[INFO] Bắt đầu huấn luyện với kỹ thuật Data Augmentation...")
all_models = {}

if not os.path.exists(dataset_path):
    print(f"[LỖI] Không tìm thấy thư mục dataset tại: {dataset_path}")
    sys.exit()

for person_name in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person_name)
    if not os.path.isdir(person_path): continue

    print(f"\n[+] Đang xử lý cho: {person_name}")
    features_list = []
    
    for file_name in os.listdir(person_path):
        if not file_name.endswith('.wav'): continue
        file_path = os.path.join(person_path, file_name)
        
        try:
            # 1. Tải file âm thanh gốc
            y, sr = librosa.load(file_path, sr=TARGET_SR)
            
            # --- BẮT ĐẦU TĂNG CƯỜNG DỮ LIỆU (AUGMENTATION) ---
            
            # Biến thể 1: File gốc
            f_orig = extract_features(y, sr)
            if f_orig is not None: features_list.append(f_orig)

            # Biến thể 2: Tăng tốc độ (Nhanh hơn 1.1x)
            y_fast = librosa.effects.time_stretch(y, rate=1.1)
            f_fast = extract_features(y_fast, sr)
            if f_fast is not None: features_list.append(f_fast)

            # Biến thể 3: Giảm tốc độ (Chậm hơn 0.9x)
            y_slow = librosa.effects.time_stretch(y, rate=0.9)
            f_slow = extract_features(y_slow, sr)
            if f_slow is not None: features_list.append(f_slow)

            # Biến thể 4: Tăng cao độ (+2 bán âm - Giọng thanh hơn)
            y_pitch_up = librosa.effects.pitch_shift(y, sr=sr, n_steps=2)
            f_up = extract_features(y_pitch_up, sr)
            if f_up is not None: features_list.append(f_up)

            # Biến thể 5: Giảm cao độ (-2 bán âm - Giọng trầm hơn)
            y_pitch_down = librosa.effects.pitch_shift(y, sr=sr, n_steps=-2)
            f_down = extract_features(y_pitch_down, sr)
            if f_down is not None: features_list.append(f_down)
            
            # Biến thể 6: Thêm nhiễu trắng nhẹ (Chống nhiễu môi trường)
            y_noise = y + 0.005 * np.random.randn(len(y))
            f_noise = extract_features(y_noise, sr)
            if f_noise is not None: features_list.append(f_noise)

        except Exception as e:
            print(f" [!] Lỗi file {file_name}: {e}")

    # Gộp tất cả đặc trưng lại để huấn luyện GMM
    if len(features_list) > 0:
        final_features = np.vstack(features_list)
        print(f" [INFO] Tổng số vector đặc trưng sau nhân bản: {final_features.shape[0]}")
        
        # Huấn luyện mô hình GMM
        gmm = GMM(n_components=N_COMPONENTS, covariance_type='diag', n_init=3, reg_covar=1e-6)
        gmm.fit(final_features)
        
        all_models[person_name] = gmm
        print(f" [OK] Đã huấn luyện xong cho {person_name}")
    else:
        print(f" [!] Không có dữ liệu để huấn luyện cho {person_name}")

# Lưu tất cả model vào file pickle
with open(models_file, 'wb') as f:
    pickle.dump(all_models, f)

print(f"\n[THANH CÔNG] Đã lưu mô hình nâng cấp vào {models_file}")