from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import pytesseract
import os
import uuid
from datetime import datetime

# Tesseract config for Linux or server
pytesseract.pytesseract.tesseract_cmd = 'tesseract'  # Keep this if on Linux/Render

# Setup
app = Flask(__name__)
UPLOAD_FOLDER = 'static'
API_KEY = 'pns_ANPR_4e2fD7gN9aBtQxLmR8vZ'  # Change this

# Create static folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Haar Cascade
cascade = cv2.CascadeClassifier('haarcascade_russian_plate_number.xml')

# Indian States
states = {
    "AN": "Andaman and Nicobar", "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh",
    "AS": "Assam", "BR": "Bihar", "CH": "Chandigarh", "DN": "Dadra and Nagar Haveli",
    "DD": "Daman and Diu", "DL": "Delhi", "GA": "Goa", "GJ": "Gujarat", "HR": "Haryana",
    "HP": "Himachal Pradesh", "JK": "Jammu and Kashmir", "KA": "Karnataka", "KL": "Kerala",
    "LD": "Lakshadweep", "MP": "Madhya Pradesh", "MH": "Maharashtra", "MN": "Manipur",
    "ML": "Meghalaya", "MZ": "Mizoram", "NL": "Nagaland", "OD": "Odisha", "PY": "Puducherry",
    "PN": "Punjab", "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "UP": "Uttar Pradesh", "WB": "West Bengal", "CG": "Chhattisgarh", "TS": "Telangana",
    "JH": "Jharkhand", "UK": "Uttarakhand"
}

def detect_plate(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    nplate = cascade.detectMultiScale(gray, 1.1, 4)

    plate_number = None
    center_x, center_y = None, None

    for (x, y, w, h) in nplate:
        h_img, w_img, _ = img.shape
        a, b = (int(0.02 * h_img), int(0.02 * w_img))
        plate = img[y + a:y + h - a, x + b:x + w - b, :]

        # Clean plate
        kernel = np.ones((1, 1), np.uint8)
        plate = cv2.dilate(plate, kernel, iterations=1)
        plate = cv2.erode(plate, kernel, iterations=1)
        plate_gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
        _, plate_bin = cv2.threshold(plate_gray, 127, 255, cv2.THRESH_BINARY)

        read = pytesseract.image_to_string(plate_bin)
        plate_number = ''.join(e for e in read if e.isalnum())
        stat = plate_number[0:2]

        # Get plate center
        center_x = x + w / 2
        center_y = y + h / 2

        # Annotate image
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
        text_size = cv2.getTextSize(plate_number, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        cv2.rectangle(img, (x, y - text_size[1] - 10), (x + text_size[0] + 10, y), (0, 0, 255), -1)
        cv2.putText(img, plate_number, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

        break  # Only process first plate

    # Save annotated image
    filename = f"{uuid.uuid4().hex}.jpg"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    cv2.imwrite(save_path, img)

    return plate_number, center_x, center_y, filename, states.get(stat.upper(), "Unknown")

@app.route('/readnumberplate', methods=['POST'])
def anpr_api():
    # API key check
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"status": "unauthorized", "message": "Invalid API key"}), 401

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"status": "error", "message": "No selected image"}), 400

    temp_path = os.path.join(UPLOAD_FOLDER, "temp.jpg")
    image.save(temp_path)

    try:
        plate_number, x, y, filename, state = detect_plate(temp_path)

        return jsonify({
            "status": "success",
            "data": {
                "message": "ANPR successful",
                "number_plate": plate_number,
                "state": state,
                "plate_Xcenter": x,
                "plate_Ycenter": y,
                "view_image": f"/static/{filename}"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/static/<path:filename>')
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
