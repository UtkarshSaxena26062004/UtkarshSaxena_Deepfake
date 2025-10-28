import os
import json
import datetime
import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from utils.hash_utils import sha256_of_file

# === Setup ===
UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
MODEL_PATH = 'model/deepfake_model.h5'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === Load model ===
print("🔹 Loading model, please wait...")
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully!")

# === Helper functions ===
def predict_image(img_path):
    """Predicts fake probability for a single image."""
    try:
        img = image.load_img(img_path, target_size=(299, 299))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
        prediction = model.predict(img_array)
        return float(prediction[0][0])  # fake probability
    except Exception as e:
        print("⚠️ Error in image prediction:", e)
        return 0.5  # fallback neutral score

def predict_video(video_path, every_n=10):
    """Predicts fake probability for video by sampling frames."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("⚠️ Cannot open video:", video_path)
        return 0.5

    preds = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % every_n == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (299, 299))
            frame = frame.astype("float32") / 255.0
            preds.append(model.predict(np.expand_dims(frame, axis=0))[0][0])

        frame_count += 1

    cap.release()
    return float(np.mean(preds)) if preds else 0.5

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f or f.filename.strip() == '':
        return redirect(url_for('index'))

    # Save file
    filename = f.filename.replace(' ', '_')
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(path)

    # Detect file type
    ext = os.path.splitext(filename)[1].lower()

    if ext in ['.jpg', '.jpeg', '.png']:
        print("🖼️ Processing image...")
        ai_score = predict_image(path)
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        print("🎥 Processing video...")
        ai_score = predict_video(path)
    else:
        return "❌ Unsupported file type. Please upload an image (.jpg/.png) or video (.mp4/.avi)."

    # Blockchain verification (placeholder)
    hexhash = sha256_of_file(path)
    bc_verified = False

    # Combine AI + metadata + blockchain scores
    metadata_score = 0.8
    authenticity = round((0.6 * (1 - ai_score)) + (0.3 * metadata_score) + (0.1 * int(bc_verified)), 3)

    report = {
        'file': filename,
        'ai_score': round(ai_score, 3),
        'blockchain_verified': bc_verified,
        'authenticity_score': authenticity,
        'hash': hexhash
    }

    # Save JSON report
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(os.path.join(REPORT_FOLDER, f'report_{ts}.json'), 'w') as rf:
        json.dump(report, rf, indent=2)

    return render_template('result.html', report=report)

# ========================================
# 🔹 Visualization / Dashboard Route
# ========================================
@app.route('/dashboard')
def dashboard():
    import glob, json, os, datetime

    report_files = glob.glob(os.path.join(REPORT_FOLDER, "*.json"))
    reports_data = []

    for file in sorted(report_files, reverse=True):
        with open(file, "r") as f:
            data = json.load(f)
            # Extract timestamp from filename (if stored as report_YYYYMMDD_HHMMSS.json)
            try:
                ts = os.path.basename(file).split("report_")[1].split(".json")[0]
                date_str = datetime.datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%d-%b-%Y %H:%M:%S")
            except:
                date_str = "Unknown"
            data["timestamp"] = date_str
            reports_data.append(data)

    if not reports_data:
        return "<h3>No reports found yet. Please upload a file first.</h3>"

    filenames = [r["file"] for r in reports_data]
    ai_scores = [r["ai_score"] for r in reports_data]
    authenticity = [r["authenticity_score"] for r in reports_data]
    blockchain = ["Verified" if r["blockchain_verified"] else "Not Verified" for r in reports_data]
    hashes = [r["hash"] for r in reports_data]
    timestamps = [r["timestamp"] for r in reports_data]

    real_count = sum(1 for r in ai_scores if r < 0.5)
    fake_count = len(ai_scores) - real_count

    return render_template(
        "dashboard.html",
        filenames=filenames,
        ai_scores=ai_scores,
        authenticity=authenticity,
        blockchain=blockchain,
        real_count=real_count,
        fake_count=fake_count,
        timestamps=timestamps,
        hashes=hashes
    )

# ========================================
# 🔹 PDF Report Download Route
# ========================================
from fpdf import FPDF
import os
from flask import send_file

@app.route('/download_report')
def download_report():
    pdf = FPDF()
    pdf.add_page()

    # ✅ Use local Unicode font (ensure DejaVuSans.ttf is in same folder)
    font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 14)

    pdf.cell(0, 10, txt="Deepfake Detection Report 🧠", ln=True)
    pdf.ln(10)

    data = {
        "file": "user_image😱.jpg",
        "result": "Fake 😅",
        "score": "92.4%",
        "date": "2025-10-27 19:45:00"
    }

    for key, value in data.items():
        pdf.cell(0, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    # Save in static/reports/
    output_path = os.path.join("static", "reports", "deepfake_report.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)

    return send_file(output_path, as_attachment=True)


# ========================================
if __name__ == '__main__':
    app.run(debug=True)
