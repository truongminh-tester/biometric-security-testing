import os
import cv2
import sys
import base64
import numpy as np
import shutil
import face_recognition
import subprocess
import io
import pickle
import librosa
import librosa.effects
import datetime
import json
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pydub import AudioSegment 

# -------------------------------------------------------------------
# KHỞI TẠO ỨNG DỤNG FLASK & CẤU HÌNH
# -------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'super_secret_security_key_attt_2025'

# [CỰC KỲ QUAN TRỌNG] BỘ 3 CẤU HÌNH GỠ BỎ MỌI GIỚI HẠN
# 1. Cho phép tổng dung lượng gói tin lên tới 200MB
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 
# 2. Không giới hạn bộ nhớ cho các trường Text (để chứa chuỗi ảnh Base64)
app.config['MAX_FORM_MEMORY_SIZE'] = None 
# 3. Không giới hạn số lượng trường trong form
app.config['MAX_FORM_PARTS'] = None

# Đường dẫn
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(SCRIPT_DIR, 'temp_uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Định nghĩa các thư mục Log và Bằng chứng
INTRUDER_FOLDER = os.path.join(SCRIPT_DIR, 'static', 'intruders')
LOG_FILE = os.path.join(SCRIPT_DIR, 'audit_logs.json')
os.makedirs(INTRUDER_FOLDER, exist_ok=True)

# -------------------------------------------------------------------
# ĐỊNH NGHĨA ĐƯỜNG DẪN DỮ LIỆU
# -------------------------------------------------------------------
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")
TRAIN_SCRIPTS_DIR = os.path.join(SCRIPT_DIR, "training_scripts")

DATASET_PATH_FACE = os.path.join(DATASET_DIR, "face")
DATASET_PATH_VOICE = os.path.join(DATASET_DIR, "voice")
DATASET_PATH_FINGERPRINT = os.path.join(DATASET_DIR, "fingerprint")
DATASET_PATH_IRIS = os.path.join(DATASET_DIR, "iris")

FACE_MODEL_PATH = os.path.join(MODELS_DIR, "encodings.pickle")
VOICE_MODEL_PATH = os.path.join(MODELS_DIR, "voice_models.pickle")
FINGERPRINT_MODEL_PATH = os.path.join(MODELS_DIR, "fingerprint_models.pickle")
IRIS_MODEL_PATH = os.path.join(MODELS_DIR, "iris_models.pickle")

TRAIN_SCRIPT_FACE = os.path.join(TRAIN_SCRIPTS_DIR, "train_face.py")
TRAIN_SCRIPT_VOICE = os.path.join(TRAIN_SCRIPTS_DIR, "train_voice.py")
TRAIN_SCRIPT_FINGERPRINT = os.path.join(TRAIN_SCRIPTS_DIR, "train_fingerprint.py")
TRAIN_SCRIPT_IRIS = os.path.join(TRAIN_SCRIPTS_DIR, "train_iris.py")

# Tạo thư mục cần thiết
for d in [MODELS_DIR, DATASET_DIR, DATASET_PATH_FACE, DATASET_PATH_VOICE, DATASET_PATH_FINGERPRINT, DATASET_PATH_IRIS]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------------
# TẢI MODEL
# -------------------------------------------------------------------
def load_all_models():
    global face_data, voice_models, fingerprint_models, iris_models, orb
    print("[INFO] Đang tải các model...")
    try:
        with open(FACE_MODEL_PATH, 'rb') as f: face_data = pickle.load(f)
    except: face_data = {"encodings": [], "names": []}
    try:
        with open(VOICE_MODEL_PATH, 'rb') as f: voice_models = pickle.load(f)
    except: voice_models = {}
    try:
        with open(FINGERPRINT_MODEL_PATH, 'rb') as f: fingerprint_models = pickle.load(f)
    except: fingerprint_models = {}
    try:
        with open(IRIS_MODEL_PATH, 'rb') as f: iris_models = pickle.load(f)
    except: iris_models = {}
    orb = cv2.ORB_create(nfeatures=1000) 
    print("[INFO] Đã tải xong.")

face_data, voice_models, fingerprint_models, iris_models, orb = {}, {}, {}, {}, None
load_all_models()

# ==============================================================================
#                                  HÀM HỖ TRỢ
# ==============================================================================

def save_audit_log(username, modality, status, image_b64=None, audio_file=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evidence_img_file = "N/A"
    evidence_audio_file = audio_file if audio_file else "N/A"

    if image_b64 and status == "FAILED":
        try:
            encoded = image_b64.split(',', 1)[1] if "," in image_b64 else image_b64
            img_data = base64.b64decode(encoded)
            evidence_filename = f"intruder_{username}_{modality}_{int(time.time())}.jpg"
            evidence_path = os.path.join(INTRUDER_FOLDER, evidence_filename)
            with open(evidence_path, "wb") as f:
                f.write(img_data)
            evidence_img_file = evidence_filename
        except Exception as e:
            print(f"[LOG ERROR] Không lưu được ảnh bằng chứng: {e}")

    log_entry = {
        "time": timestamp, "user": username, "modality": modality,
        "status": status, "evidence_img": evidence_img_file, "evidence_audio": evidence_audio_file
    }

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f: logs = json.load(f)
        except: pass
    logs.insert(0, log_entry)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

def check_if_eye(image_bgr):
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.medianBlur(gray, 9)
        rows = gray_blurred.shape[0]
        circles = cv2.HoughCircles(gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=rows/8,
                                   param1=100, param2=40, minRadius=20, maxRadius=int(rows/3))
        return circles is not None
    except: return False

def match_orb_features(username, image_data_url, model_dict, modality_name):
    start_time = time.time()
    if not username or not image_data_url: return False, "Thiếu dữ liệu.", None, 0
    if username not in model_dict: return False, f"User '{username}' chưa đăng ký.", None, 0

    des_user = model_dict[username]
    try:
        header, encoded_data = image_data_url.split(',', 1)
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(encoded_data), dtype=np.uint8), cv2.IMREAD_COLOR)
        
        is_eye = check_if_eye(frame)
        if modality_name == "Vân tay" and is_eye: return False, "⛔ CẢNH BÁO: Phát hiện MẮT giả dạng!", None, 0
        elif modality_name == "Mống mắt" and not is_eye: return False, "⚠️ LỖI: Không tìm thấy mắt!", None, 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray) 
        kp, des = orb.detectAndCompute(gray, None)
        if des is None: return False, "Ảnh quá mờ.", None, 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(des_user, des), key=lambda x: x.distance)
        good_matches = [m for m in matches if m.distance < 75]
        
        match_count = len(good_matches)
        
        total_features = len(kp)
        avg_distance = sum(m.distance for m in good_matches) / match_count if match_count > 0 else 100.0
        quality_score = min(100, int((total_features / 500) * 100))

        img_debug = cv2.drawKeypoints(frame, kp, None, color=(0, 255, 0), flags=0)
        _, buffer = cv2.imencode('.jpg', img_debug)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        if modality_name == "Mống mắt": MIN_MATCHES = 40; MAX_DISTANCE = 55; MIN_QUALITY = 15
        else: MIN_MATCHES = 15; MAX_DISTANCE = 60; MIN_QUALITY = 10
            
        is_success = (match_count > MIN_MATCHES) and (avg_distance < MAX_DISTANCE) and (quality_score > MIN_QUALITY)
        status_text = "XÁC THỰC THÀNH CÔNG" if is_success else "XÁC THỰC THẤT BẠI"
        
        badge_style = "background: rgba(255,255,255,0.6); padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); margin: 2px;"
        msg_html = f"""
        <div style="text-align: center;">
            <div style="font-size: 1.1rem; font-weight: bold; text-transform: uppercase;">{status_text}</div>
            <div style="display: flex; justify-content: center; gap: 4px;">
                <span style="{badge_style}">✅ Match: <b>{match_count}</b></span>
                <span style="{badge_style}">📉 Dist: <b>{avg_distance:.1f}</b></span>
                <span style="{badge_style}">💎 Quality: <b>{quality_score}</b></span>
            </div>
        </div>
        """
        return is_success, msg_html, img_base64, match_count
    except Exception as e: return False, f"Lỗi: {e}", None, 0

# ==============================================================================
#                                  ROUTES
# ==============================================================================

@app.route('/')
def index(): return render_template('index.html')

# --- LOGIN FACE ---
@app.route('/login_face', methods=['POST'])
def login_face():
    data = request.get_json()
    username, image_data_url = data.get('username'), data.get('image')
    if not username or not image_data_url: return jsonify({"success": False, "message": "Thiếu thông tin."})

    try:
        header, encoded_data = image_data_url.split(',', 1)
        img = cv2.imdecode(np.frombuffer(base64.b64decode(encoded_data), dtype=np.uint8), cv2.IMREAD_COLOR)
        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except: return jsonify({"success": False, "message": "Lỗi ảnh."})

    boxes = face_recognition.face_locations(rgb_frame, model="hog")
    encodings = face_recognition.face_encodings(rgb_frame, boxes)

    if len(encodings) == 0:
        save_audit_log(username, "Face", "FAILED", image_data_url)
        return jsonify({"success": False, "message": "Không thấy mặt nào trong khung hình."})

    # Logic: Quét từng người
    is_authorized = False
    for e in encodings:
        distances = face_recognition.face_distance(face_data["encodings"], e)
        if len(distances) == 0: continue
        best_idx = np.argmin(distances)
        if distances[best_idx] < 0.45 and face_data["names"][best_idx] == username:
            is_authorized = True; break

    if is_authorized:
        session['logged_in'], session['user'] = True, username
        save_audit_log(username, "Face", "SUCCESS")
        return jsonify({"success": True, "message": f"Chào {username}!", "redirect": "/dashboard"})
    else:
        save_audit_log(username, "Face", "FAILED", image_data_url)
        return jsonify({"success": False, "message": "Cảnh báo: Không tìm thấy chủ tài khoản trong đám đông!"})

# --- LOGIN VOICE (Full Fix) ---
@app.route('/login_voice', methods=['POST'])
def login_voice():
    try:
        username = request.form.get('username')
        audio_file = request.files.get('audio_data')
        evidence_img = request.form.get('evidence_image') # Dữ liệu lớn (Base64)
        
        if not username or not audio_file: return jsonify({"success": False, "message": "Thiếu thông tin."})
        if username not in voice_models: return jsonify({"success": False, "message": "User không tồn tại."})

        timestamp_id = int(time.time())
        temp_webm = os.path.join(app.config['UPLOAD_FOLDER'], f'v_{timestamp_id}.webm')
        temp_wav = os.path.join(app.config['UPLOAD_FOLDER'], f'v_{timestamp_id}.wav')
        
        audio_file.save(temp_webm)
        AudioSegment.from_file(temp_webm).export(temp_wav, format="wav")
        y, sr = librosa.load(temp_wav, sr=16000)
        y_trim, _ = librosa.effects.trim(y, top_db=25)
        
        if y_trim.size > 0:
            mfcc = librosa.feature.mfcc(y=y_trim, sr=sr, n_mfcc=20)
            feat = np.vstack([mfcc, librosa.feature.delta(mfcc), librosa.feature.delta(mfcc, order=2)]).T
            score = voice_models[username].score(feat)
            
            if score > -250: 
                session['logged_in'] = True; session['user'] = username
                save_audit_log(username, "Voice", "SUCCESS")
                return jsonify({"success": True, "message": f"Chào {username}! (Score: {score:.1f})", "redirect": "/dashboard"})
            else: 
                # Lưu bằng chứng kép
                audio_ev_name = f"intruder_{username}_voice_{timestamp_id}.wav"
                shutil.copyfile(temp_wav, os.path.join(INTRUDER_FOLDER, audio_ev_name))
                save_audit_log(username, "Voice", "FAILED", image_b64=evidence_img, audio_file=audio_ev_name)
                return jsonify({"success": False, "message": f"Giọng không khớp ({score:.1f}). Đã lưu bằng chứng."})
        return jsonify({"success": False, "message": "Âm thanh lỗi."})

    except Exception as e: 
        print(f"[VOICE ERROR] {e}") # In lỗi ra terminal
        return jsonify({"success": False, "message": f"Lỗi Server: {str(e)}"})
    finally:
        if 'temp_webm' in locals() and os.path.exists(temp_webm): os.remove(temp_webm)
        if 'temp_wav' in locals() and os.path.exists(temp_wav): os.remove(temp_wav)

# --- LOGIN FINGERPRINT & IRIS ---
@app.route('/login_fingerprint', methods=['POST'])
def login_fingerprint():
    data = request.get_json()
    u = data.get('username')
    ok, msg, img, c = match_orb_features(u, data.get('image'), fingerprint_models, "Vân tay")
    if ok: session['logged_in'], session['user'] = True, u; save_audit_log(u, "Fingerprint", "SUCCESS")
    else: save_audit_log(u, "Fingerprint", "FAILED", data.get('image'))
    return jsonify({"success": ok, "message": msg, "analysis_image": img, "redirect": "/dashboard" if ok else None})

@app.route('/login_iris', methods=['POST'])
def login_iris():
    data = request.get_json()
    u = data.get('username')
    ok, msg, img, c = match_orb_features(u, data.get('image'), iris_models, "Mống mắt")
    if ok: session['logged_in'], session['user'] = True, u; save_audit_log(u, "Iris", "SUCCESS")
    else: save_audit_log(u, "Iris", "FAILED", data.get('image'))
    return jsonify({"success": ok, "message": msg, "analysis_image": img, "redirect": "/dashboard" if ok else None})

# --- REGISTER ROUTES ---
def save_uploaded_image_common(data, base_folder):
    user, img_data, count = data.get('name'), data.get('image_data'), int(data.get('count'))
    user_dir = os.path.join(base_folder, user)
    if count == 0 and os.path.exists(user_dir): return jsonify({"status": "error", "message": f"Tên '{user}' đã tồn tại!"}), 200
    os.makedirs(user_dir, exist_ok=True)
    try:
        img = cv2.imdecode(np.frombuffer(base64.b64decode(img_data.split(',',1)[1]), np.uint8), cv2.IMREAD_COLOR)
        cv2.imwrite(os.path.join(user_dir, f"{count}.jpg"), img)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 400

@app.route('/register_face')
def reg_face_page(): return render_template('register_face.html')
@app.route('/api/register_face', methods=['POST'])
def api_reg_face():
    data = request.get_json()
    try:
        encoded = data.get('image_data').split(',', 1)[1]
        img = cv2.imdecode(np.frombuffer(base64.b64decode(encoded), np.uint8), cv2.IMREAD_COLOR)
        locs = face_recognition.face_locations(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if len(locs) != 1: return jsonify({"status": "error", "message": "Yêu cầu đúng 1 khuôn mặt!"}), 200
        return save_uploaded_image_common(data, DATASET_PATH_FACE)
    except: return jsonify({"status": "error"}), 400

@app.route('/api/trigger_train_face', methods=['POST'])
def trig_train_face(): subprocess.run([sys.executable, TRAIN_SCRIPT_FACE]); load_all_models(); return jsonify({"status": "success"})

@app.route('/register_voice')
def reg_voice_page(): return render_template('register_voice.html')
@app.route('/api/register_voice', methods=['POST'])
def api_reg_voice():
    user = request.form.get('name'); f = request.files.get('audio_data'); count = int(request.form.get('count'))
    user_dir = os.path.join(DATASET_PATH_VOICE, user)
    os.makedirs(user_dir, exist_ok=True)
    temp = os.path.join(user_dir, f"{count}.webm")
    f.save(temp); AudioSegment.from_file(temp).export(os.path.join(user_dir, f"{count}.wav"), format="wav"); os.remove(temp)
    return jsonify({"status": "success"})
@app.route('/api/trigger_train_voice', methods=['POST'])
def trig_train_voice(): subprocess.run([sys.executable, TRAIN_SCRIPT_VOICE]); load_all_models(); return jsonify({"status": "success"})

@app.route('/register_fingerprint')
def reg_finger_page(): return render_template('register_fingerprint.html')
@app.route('/api/register_fingerprint', methods=['POST'])
def api_reg_finger(): return save_uploaded_image_common(request.get_json(), DATASET_PATH_FINGERPRINT)
@app.route('/api/trigger_train_fingerprint', methods=['POST'])
def trig_train_finger(): subprocess.run([sys.executable, TRAIN_SCRIPT_FINGERPRINT]); load_all_models(); return jsonify({"status": "success"})

@app.route('/register_iris')
def reg_iris_page(): return render_template('register_iris.html')
@app.route('/api/register_iris', methods=['POST'])
def api_reg_iris(): return save_uploaded_image_common(request.get_json(), DATASET_PATH_IRIS)
@app.route('/api/trigger_train_iris', methods=['POST'])
def trig_train_iris(): subprocess.run([sys.executable, TRAIN_SCRIPT_IRIS]); load_all_models(); return jsonify({"status": "success"})

# --- DASHBOARD & LOGOUT ---
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f: logs = json.load(f)
    return render_template('dashboard.html', user=session.get('user'), logs=logs)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    # Bật debug để in lỗi ra console nếu có
    print(f"DEBUG: Max Content Length -> {app.config['MAX_CONTENT_LENGTH']}")
    app.run(debug=True, host='0.0.0.0', port=5000)