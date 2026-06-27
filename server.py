"""
==============================================================
 Server Aplikasi File Sharing Sederhana
 Tugas Akhir - Client Server Programming (INF2.62.6003)
 Program Studi Informatika - Universitas Negeri Padang
==============================================================

Arsitektur   : Client-Server berbasis HTTP (REST API)
Framework    : Flask 3.1.3 (Python 3.12)
Konkurensi   : Threaded WSGI server (multi-thread per request)
Protokol     : HTTP/1.1, format data JSON + multipart/form-data
Autentikasi  : Token sederhana via header "Authorization: Bearer <token>"
Penyimpanan  : Direktori lokal (./storage) + metadata di file JSON

Fitur inti yang direplikasi dari aplikasi sejenis (Dropbox/Google Drive):
  1. Upload file              -> POST   /api/files
  2. Download file             -> GET    /api/files/<file_id>
  3. Lihat daftar file         -> GET    /api/files
  4. Hapus file                -> DELETE /api/files/<file_id>
  5. Login sederhana (token)   -> POST   /api/login
==============================================================
"""

import os
import json
import time
import uuid
import logging
import threading
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

# --------------------------------------------------------------
# Konfigurasi dasar
# --------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
METADATA_FILE = os.path.join(BASE_DIR, "metadata.json")
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # batas 50 MB per file (mitigasi DoS sederhana)
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif", "docx", "xlsx",
    "zip", "csv", "md", "json", "pptx", "mp3", "mp4"
}

# "Database" pengguna sederhana (username -> password).
# Pada aplikasi nyata, password WAJIB di-hash (bcrypt/argon2) - lihat slide Aspek Keamanan.
USERS = {
    "admin": "admin123",
    "user1": "password1",
}

# Token aktif yang sedang login: token -> username
ACTIVE_TOKENS = {}

# Lock untuk mengamankan akses metadata.json dari banyak thread sekaligus
# (penanganan konkurensi - lihat slide Penanganan Konkurensi)
metadata_lock = threading.Lock()

os.makedirs(STORAGE_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("file-sharing-server")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# --------------------------------------------------------------
# Util: metadata file (daftar file yang sudah diupload)
# --------------------------------------------------------------
def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------------------------------------------
# Decorator: autentikasi token sederhana
# --------------------------------------------------------------
def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("Akses ditolak: header Authorization tidak ada/salah format")
            return jsonify({"error": "Token tidak ditemukan. Silakan login terlebih dahulu."}), 401

        token = auth_header.split(" ", 1)[1]
        if token not in ACTIVE_TOKENS:
            logger.warning("Akses ditolak: token tidak valid (%s...)", token[:8])
            return jsonify({"error": "Token tidak valid atau sudah kedaluwarsa."}), 401

        request.username = ACTIVE_TOKENS[token]
        return f(*args, **kwargs)
    return wrapper


# --------------------------------------------------------------
# Endpoint: Login -> menghasilkan token
# --------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if USERS.get(username) != password:
        logger.warning("Login gagal untuk username='%s'", username)
        return jsonify({"error": "Username atau password salah."}), 401

    token = uuid.uuid4().hex
    ACTIVE_TOKENS[token] = username
    logger.info("Login berhasil: username='%s' token=%s...", username, token[:8])
    return jsonify({"token": token, "username": username})


# --------------------------------------------------------------
# Endpoint: Upload file (multipart/form-data)
# --------------------------------------------------------------
@app.route("/api/files", methods=["POST"])
@require_token
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file pada request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nama file kosong."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Tipe file tidak diizinkan."}), 400

    original_name = secure_filename(file.filename)
    file_id = uuid.uuid4().hex
    stored_name = f"{file_id}_{original_name}"
    filepath = os.path.join(STORAGE_DIR, stored_name)

    file.save(filepath)
    size_bytes = os.path.getsize(filepath)

    # Bagian kritis: tulis ke metadata.json - dikunci agar aman
    # ketika banyak client upload bersamaan (race condition).
    with metadata_lock:
        metadata = load_metadata()
        metadata[file_id] = {
            "file_id": file_id,
            "original_name": original_name,
            "stored_name": stored_name,
            "size_bytes": size_bytes,
            "uploaded_by": request.username,
            "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_metadata(metadata)

    logger.info(
        "Upload sukses: '%s' (%d bytes) oleh '%s' [thread=%s]",
        original_name, size_bytes, request.username, threading.current_thread().name
    )
    return jsonify(metadata[file_id]), 201


# --------------------------------------------------------------
# Endpoint: Daftar file
# --------------------------------------------------------------
@app.route("/api/files", methods=["GET"])
@require_token
def list_files():
    with metadata_lock:
        metadata = load_metadata()
    files = sorted(metadata.values(), key=lambda x: x["uploaded_at"], reverse=True)
    return jsonify({"count": len(files), "files": files})


# --------------------------------------------------------------
# Endpoint: Download file
# --------------------------------------------------------------
@app.route("/api/files/<file_id>", methods=["GET"])
@require_token
def download_file(file_id):
    with metadata_lock:
        metadata = load_metadata()

    if file_id not in metadata:
        abort(404, description="File tidak ditemukan.")

    info = metadata[file_id]
    logger.info("Download: '%s' oleh '%s'", info["original_name"], request.username)
    return send_from_directory(
        STORAGE_DIR, info["stored_name"],
        as_attachment=True, download_name=info["original_name"]
    )


# --------------------------------------------------------------
# Endpoint: Hapus file
# --------------------------------------------------------------
@app.route("/api/files/<file_id>", methods=["DELETE"])
@require_token
def delete_file(file_id):
    with metadata_lock:
        metadata = load_metadata()
        if file_id not in metadata:
            return jsonify({"error": "File tidak ditemukan."}), 404

        info = metadata.pop(file_id)
        save_metadata(metadata)

    filepath = os.path.join(STORAGE_DIR, info["stored_name"])
    if os.path.exists(filepath):
        os.remove(filepath)

    logger.info("Hapus file: '%s' oleh '%s'", info["original_name"], request.username)
    return jsonify({"message": f"File '{info['original_name']}' berhasil dihapus."})


# --------------------------------------------------------------
# Error handler umum
# --------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Ukuran file melebihi batas maksimum (50MB)."}), 413


if __name__ == "__main__":
    print("=" * 60)
    print(" File Sharing Server berjalan di http://localhost:5000")
    print(" Akun demo -> admin/admin123  atau  user1/password1")
    print("=" * 60)
    # threaded=True -> server menangani banyak client secara konkuren (multi-thread)
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
