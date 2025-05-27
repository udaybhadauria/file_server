from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "mysecretkey")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# --- JWT Token Required Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
        return f(*args, **kwargs)
    return decorated

# --- Login Endpoint ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password required'}), 400
    if data['username'] == ADMIN_USERNAME and data['password'] == ADMIN_PASSWORD:
        token = jwt.encode({
            'user': data['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

# --- Upload Endpoint ---
@app.route('/upload', methods=['POST'])
@token_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Empty filename'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({'message': 'File uploaded successfully'}), 200

# --- Download Endpoint (JWT Protected) ---
@app.route('/download/<filename>', methods=['GET'])
@token_required
def download_file(filename):
    filename = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({'message': 'File not found'}), 404
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# --- Public Download (Unauthenticated for Gradio UI) ---
@app.route('/public_download/<filename>', methods=['GET'])
def public_download_file(filename):
    filename = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({'message': 'File not found'}), 404
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# --- Delete Endpoint ---
@app.route('/delete/<filename>', methods=['DELETE'])
@token_required
def delete_file(filename):
    filename = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted'}), 200
    else:
        return jsonify({'message': 'File not found'}), 404

# --- List Files with Metadata ---
@app.route('/list', methods=['GET'])
@token_required
def list_files():
    file_list = []
    for fname in os.listdir(UPLOAD_FOLDER):
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        if os.path.isfile(fpath):
            stats = os.stat(fpath)
            file_list.append({
                'name': fname,
                'size_kb': round(stats.st_size / 1024, 2),
                'modified': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    return jsonify({'files': file_list})

# --- Run App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8369)
