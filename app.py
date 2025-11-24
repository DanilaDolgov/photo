import io
import zipfile
import sqlite3
import requests
from flask import Flask, request, jsonify, render_template_string, send_file
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from io import BytesIO
from urllib.parse import quote

load_dotenv()  # загружает .env переменные

# ----------------- КОНФИГУРАЦИЯ -----------------

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
DB_PATH = os.getenv("DB_PATH")
GALLERY_HTML_PATH = "gallery.html"

PHOTOS_PER_PAGE = 20  # количество фото на страницу

# ------------------------------------------------------------------------------

app = Flask(__name__)

# Инициализация boto3 клиента для MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name=S3_REGION
)

# ----------------- БД (SQLite) -----------------
def get_db_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        url TEXT PRIMARY KEY,
        filename TEXT,
        likes INTEGER NOT NULL,
        uploaded INTEGER NOT NULL DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------- Утилиты MinIO -----------------
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' создан.")
        except ClientError as e2:
            print("Не удалось создать bucket:", e2)

def upload_to_s3(url, filename):
    try:
        ensure_bucket_exists(S3_BUCKET)
        proxy_url = f"http://127.0.0.1:5000/proxy?url={quote(url, safe='')}"
        resp = requests.get(proxy_url, timeout=30)
        resp.raise_for_status()
        s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=resp.content)
        print(f"Uploaded to MinIO: {filename}")
        return True
    except Exception as e:
        print("Ошибка загрузки в MinIO:", e)
        return False

# ----------------- РОУТЫ -----------------

@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return "Нет URL", 400
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "*/*"
    }
    try:
        if "cloud-api.yandex.net" in url and "/download" in url:
            info = requests.get(url, headers=headers, timeout=10).json()
            real_url = info.get("href")
            if not real_url:
                return "Нет href", 500
        else:
            real_url = url
        resp = requests.get(real_url, stream=True, timeout=30, headers=headers, allow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return send_file(BytesIO(resp.content), mimetype=content_type, as_attachment=False)
    except Exception as e:
        return str(e), 500

@app.route("/like", methods=["POST"])
def like_photo():
    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400
    url = data["url"].strip()
    if not url:
        return jsonify({"error": "Empty URL"}), 400
    filename = url.split("/")[-1] or url.replace("/", "_")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT likes, uploaded FROM likes WHERE url = ?", (url,))
    row = cur.fetchone()
    if row is None:
        uploaded = 1 if upload_to_s3(url, filename) else 0
        cur.execute("INSERT INTO likes (url, filename, likes, uploaded) VALUES (?, ?, ?, ?)",
                    (url, filename, 1, uploaded))
        conn.commit()
        likes_count = 1
    else:
        likes_count = row["likes"] + 1
        cur.execute("UPDATE likes SET likes = ? WHERE url = ?", (likes_count, url))
        conn.commit()
    conn.close()
    return jsonify({"likes": likes_count})

@app.route("/liked_photos", methods=["GET"])
def get_liked_photos():
    page = int(request.args.get("page", 1))
    offset = (page - 1) * PHOTOS_PER_PAGE
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT url, likes FROM likes ORDER BY likes DESC LIMIT ? OFFSET ?", (PHOTOS_PER_PAGE, offset))
    rows = cur.fetchall()
    conn.close()
    result = {row["url"]: row["likes"] for row in rows}
    return jsonify(result)

@app.route("/download_liked")
def download_liked():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT url, filename FROM likes ORDER BY likes DESC")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "Нет лайкнутых фотографий", 400
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            url = row["url"]
            filename = row["filename"] or (url.split("/")[-1] or "file")
            try:
                proxied_url = f"http://127.0.0.1:5000/proxy?url={quote(url, safe='')}"
                resp = requests.get(proxied_url, timeout=30)
                if resp.status_code == 200:
                    arcname = filename
                    suffix = 1
                    while arcname in zf.namelist():
                        arcname = f"{os.path.splitext(filename)[0]}_{suffix}{os.path.splitext(filename)[1]}"
                        suffix += 1
                    zf.writestr(arcname, resp.content)
            except Exception as e:
                print(f"Ошибка при скачивании {url}: {e}")
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="liked_photos.zip")

@app.route("/liked_gallery")
def liked_gallery():
    page = int(request.args.get("page", 1))
    offset = (page - 1) * PHOTOS_PER_PAGE
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT url, likes FROM likes ORDER BY likes DESC LIMIT ? OFFSET ?", (PHOTOS_PER_PAGE, offset))
    rows = cur.fetchall()
    conn.close()
    items_html = ""
    for row in rows:
        url = row["url"]
        likes = row["likes"]
        items_html += f"""
        <div class="gallery-item">
            <img src="/proxy?url={quote(url, safe='')}" alt="Фото">
            <div class="like-count">❤️ {likes}</div>
        </div>
        """
    total_pages = (len(rows) + PHOTOS_PER_PAGE - 1) // PHOTOS_PER_PAGE
    pagination_html = f'<div style="margin:15px 0;">Страница {page}</div>'
    gallery_html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <title>Лайкнутые фото</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f2f2f2; margin: 0; padding: 20px; }}
        h2 {{ margin-bottom: 20px; }}
        a.button {{ display: inline-block; padding: 10px 15px; background: #4CAF50; color: white; border-radius: 8px; text-decoration: none; margin-bottom: 20px; }}
        a.button:hover {{ background: #45a049; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .gallery-item {{ position: relative; border-radius: 8px; overflow: hidden; }}
        .gallery-item img {{ width: 100%; height: 200px; object-fit: cover; }}
        .like-count {{ position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.6); color: white; padding: 5px 8px; border-radius: 5px; font-size: 14px; }}
    </style>
    </head>
    <body>
    <h2>Лайкнутые фотографии</h2>
    <a href="/download_liked" class="button">📦 Скачать все лайкнутые фото (ZIP)</a>
    {pagination_html}
    <div class="gallery">{items_html}</div>
    </body>
    </html>
    """
    return render_template_string(gallery_html)

@app.route("/")
def index():
    if not os.path.exists(GALLERY_HTML_PATH):
        return "Файл gallery.html не найден. Сначала сгенерируй его (generate_gallery.py).", 404
    with open(GALLERY_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    insert_html = '<div style="margin-bottom:12px;"><a href="/liked_gallery" style="display:inline-block;padding:8px 12px;background:#007bff;color:#fff;border-radius:6px;text-decoration:none;">Просмотреть лайки</a></div>'
    import re
    if "<body" in html_content.lower():
        def repl_body(match):
            return match.group(0) + "\n" + insert_html
        html_content = re.sub(r"(?i)<body[^>]*>", repl_body, html_content, count=1)
    else:
        html_content = insert_html + html_content
    return render_template_string(html_content)

# ----------------- Запуск -----------------
if __name__ == "__main__":
    print("MinIO endpoint:", S3_ENDPOINT)
    print("Using bucket:", S3_BUCKET)
    print("DB path:", DB_PATH)
    app.run(debug=True, host="0.0.0.0", port=5000)
