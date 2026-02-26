import pickle
import numpy as np
import os
import sys

# Đảm bảo in tiếng Việt không bị lỗi font trên Terminal
sys.stdout.reconfigure(encoding='utf-8')

PATH_ENCODINGS = os.path.join("models", "encodings.pickle")

def evaluate_model():
    print("================================================================")
    print("📊 BÁO CÁO KIỂM THỬ MÔ HÌNH NHẬN DIỆN KHUÔN MẶT (AI EVALUATION)")
    print("================================================================")

    if not os.path.exists(PATH_ENCODINGS):
        print("❌ LỖI: Không tìm thấy file encodings.pickle. Hãy train model trước!")
        return

    data = pickle.load(open(PATH_ENCODINGS, "rb"))
    encodings = np.array(data["encodings"])
    names = np.array(data["names"])
    unique_names = np.unique(names)

    # Ngưỡng chấp nhận (Tolerance) mặc định của thuật toán
    TOLERANCE = 0.6 
    
    print(f"Tổng số User trong DB: {len(unique_names)}")
    print(f"Ngưỡng xác thực (Threshold/Tolerance) mặc định: {TOLERANCE}\n")
    print(f"{'User (Tài khoản)':<18} | {'Nội bộ (Cùng người)':<20} | {'Khác người':<15} | {'Trạng thái'}")
    print("-" * 80)

    for name in unique_names:
        mine = encodings[names == name]
        others = encodings[names != name]
        
        # 1. Tính khoảng cách Nội bộ (Intra-class)
        if len(mine) > 1:
            # Tính ma trận khoảng cách
            dist_matrix = pairwise_distances(mine, mine)
            # Chỉ lấy tam giác trên của ma trận (bỏ đường chéo chứa các số 0)
            intra_dists = dist_matrix[np.triu_indices(len(mine), k=1)]
            intra = np.mean(intra_dists)
        else:
            intra = 0.0 # User chỉ có 1 ảnh thì không có khoảng cách nội bộ

        # 2. Tính khoảng cách Khác người (Inter-class)
        inter = np.mean(pairwise_distances(mine, others)) if len(others) > 0 else 0.0

        # 3. Đánh giá chất lượng (QA Evaluation)
        # Nội bộ phải < Tolerance VÀ Khác người phải > Tolerance
        if intra < TOLERANCE and inter > TOLERANCE:
            status = "✅ PASS"
        else:
            status = "❌ FAIL (Dễ nhận nhầm)"

        print(f"{name:<18} | {intra:<20.4f} | {inter:<15.4f} | {status}")

    print("================================================================")
    print("💡 KẾT LUẬN DÀNH CHO TESTER:")
    print("- 'Nội bộ' càng gần 0 càng tốt (Tránh lỗi FRR - Từ chối người dùng hợp lệ).")
    print("- 'Khác người' càng gần 1.0 càng tốt (Tránh lỗi FAR - Nhận diện kẻ gian).")
    print("================================================================")

if __name__ == "__main__":
    from sklearn.metrics import pairwise_distances
    evaluate_model()