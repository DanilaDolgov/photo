
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

load_dotenv()  # загружает .env переменные


# ----------------- КОНФИГУРАЦИЯ (отредактируй при необходимости) -----------------


S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

DB_PATH = os.getenv("DB_PATH")  # MinIO не строг к региону, но boto3 требует значение

# Путь к gallery.html (тот файл, который генерируешь скриптом)
GALLERY_HTML_PATH = "gallery.html"

# ------------------------------------------------------------------------------

app = Flask(__name__)

# Инициализируем boto3 client для MinIO
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

# вызываем при старте
init_db()

# ----------------- Утилиты MinIO -----------------
def ensure_bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        # Если не существует, попробуем создать
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' создан.")
        except ClientError as e2:
            # В некоторых окружениях create_bucket может требовать region/ACL; ловим ошибку и продолжаем
            print("Не удалось создать bucket или он уже существует / недостаточно прав:", e2)

def upload_to_s3(url, filename):
    """
    Загружает картинку по URL в MinIO (Bucket S3_BUCKET), имя файла - filename (оригинальное имя).
    Возвращает True при успешной загрузке.
    """
    try:
        # пробуем создать/убедиться в бакете
        ensure_bucket_exists(S3_BUCKET)

        resp = requests.get(url, timeout=20)
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
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        return send_file(BytesIO(resp.content), mimetype="image/jpeg")
    except Exception as e:
        return str(e), 500

@app.route("/like", methods=["POST"])
def like_photo():
    """
    Ожидает JSON: { "url": "<image_url>" }
    Логика:
    - если записи нет: загружаем в MinIO под оригинальным именем, добавляем запись likes=1, uploaded=1/0
    - если запись есть: увеличиваем likes
    Возвращает JSON: { "likes": n }
    """
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
        # первая лайк — загружаем в MinIO
        uploaded = 0
        try:
            ok = upload_to_s3(url, filename)
            uploaded = 1 if ok else 0
        except Exception as e:
            uploaded = 0

        cur.execute(
            "INSERT INTO likes (url, filename, likes, uploaded) VALUES (?, ?, ?, ?)",
            (url, filename, 1, uploaded)
        )
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
    """
    Возвращает JSON: { url1: likes1, url2: likes2, ... }
    """
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT url, likes FROM likes ORDER BY likes DESC")
    rows = cur.fetchall()
    conn.close()
    result = {row["url"]: row["likes"] for row in rows}
    return jsonify(result)

@app.route("/download_liked")
def download_liked():
    """
    Скачивает все лайкнутые фотографии (по оригинальным URL) в ZIP и отдает пользователю.
    Если один из файлов не скачивается — пропускаем его.
    """
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
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    # Если в ZIP уже есть такое имя — добавим суффикс
                    arcname = filename
                    suffix = 1
                    while arcname in zf.namelist():
                        arcname = f"{os.path.splitext(filename)[0]}_{suffix}{os.path.splitext(filename)[1]}"
                        suffix += 1
                    zf.writestr(arcname, resp.content)
                else:
                    print(f"Не удалось скачать {url}: статус {resp.status_code}")
            except Exception as e:
                print(f"Ошибка при скачивании {url}: {e}")

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="liked_photos.zip")

@app.route("/liked_gallery")
def liked_gallery():
    """
    Визуальная страница с лайкнутыми фото и кнопкой загрузки ZIP.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT url, likes FROM likes ORDER BY likes DESC")
    rows = cur.fetchall()
    conn.close()

    items_html = ""
    for row in rows:
        url = row["url"]
        likes = row["likes"]
        items_html += f"""
        <div class="gallery-item">
            <img src="{url}" alt="Фото">
            <div class="like-count">❤️ {likes}</div>
        </div>
        """

    gallery_html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <title>Лайкнутые фото</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f2f2f2; margin: 0; padding: 20px; }}
        h2 {{ margin-bottom: 20px; }}
        a.button {{
            display: inline-block;
            padding: 10px 15px;
            background: #4CAF50;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            margin-bottom: 20px;
        }}
        a.button:hover {{ background: #45a049; }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}
        .gallery-item {{ position: relative; border-radius: 8px; overflow: hidden; }}
        .gallery-item img {{ width: 100%; height: 200px; object-fit: cover; }}
        .like-count {{
            position: absolute; bottom: 5px; right: 5px;
            background: rgba(0,0,0,0.6); color: white;
            padding: 5px 8px; border-radius: 5px; font-size: 14px;
        }}
    </style>
    </head>
    <body>
    <h2>Лайкнутые фотографии ({len(rows)})</h2>
    <a href="/download_liked" class="button">📦 Скачать все лайкнутые фото (ZIP)</a>
    <div class="gallery">
    {items_html}
    </div>
    </body>
    </html>
    """
    return render_template_string(gallery_html)

@app.route("/")
def index():
    """
    Отдаёт gallery.html, но автоматически вставляет ссылку 'Просмотреть лайки' в верх страницы.
    Если gallery.html отсутствует — выдаёт 404 и подсказку.
    """
    if not os.path.exists(GALLERY_HTML_PATH):
        return "Файл gallery.html не найден. Сначала сгенерируй его (generate_gallery.py).", 404

    with open(GALLERY_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Вставим кнопку/ссылку на liked_gallery сразу после <body>
    insert_html = '<div style="margin-bottom:12px;"><a href="/liked_gallery" style="display:inline-block;padding:8px 12px;background:#007bff;color:#fff;border-radius:6px;text-decoration:none;">Просмотреть лайки</a></div>'
    if "<body" in html_content.lower():
        # вставляем только после первого > в теге body
        import re
        def repl_body(match):
            return match.group(0) + "\n" + insert_html
        html_content = re.sub(r"(?i)<body[^>]*>", repl_body, html_content, count=1)
    else:
        # если вдруг нет body — просто добавим в начало
        html_content = insert_html + html_content

    return render_template_string(html_content)

# ----------------- Запуск -----------------
if __name__ == "__main__":
    print("MinIO endpoint:", S3_ENDPOINT)
    print("Using bucket:", S3_BUCKET)
    print("DB path:", DB_PATH)
    app.run(debug=True, host="0.0.0.0", port=5000)
