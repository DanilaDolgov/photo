# import requests
# from bs4 import BeautifulSoup
# import json
# import time
#
#
# def extract_image_url(item):
#     sizes = item.get("sizes")
#     try:
#         if sizes:
#             candidate = sizes[-3:-2][0].get("url")
#             if candidate:
#                 return candidate
#     except Exception:
#         pass
#
#     preview = item.get("preview")
#     if preview:
#         return preview
#
#     return None
#
# base_url = "https://cloud-api.yandex.net/v1/disk/public/resources"
#
# urls = [
#     "https://tanyaname.ru/disk/19-09-2025-dilya-drvmfr",
#     "https://tanyaname.ru/disk/16-09-2025-tatyana-j4vq0d",
#     "https://tanyaname.ru/disk/29-06-2025-gleb-i-katerina-j7s5dw",
#     "https://tanyaname.ru/disk/zvezdy-vbdwmn",
#     "https://tanyaname.ru/disk/04-06-2025-viktoriya-tdjk96",
#     "https://tanyaname.ru/disk/1-maya-v9zqgr",
#     "https://tanyaname.ru/disk/14-03-2025-4-klass-sb38mz",
#     "https://tanyaname.ru/disk/16-02-2025-16-fevralya-dsswb0",
#     "https://tanyaname.ru/disk/12-02-2025-egor-i-tatyana-bq325h",
#     "https://tanyaname.ru/disk/09-02-2025-schuka-ltsqf7",
#     "https://tanyaname.ru/disk/08-12-2024-dlya-viki-z6gr4b",
#     "https://tanyaname.ru/disk/06-12-2024-6-dekabrya-krh1xt",
#     "https://tanyaname.ru/disk/22-11-2024-svet-rodnoy-pesni-q578fc",
#     "https://tanyaname.ru/disk/03-11-2024-anya-mj3j0v",
#     "https://tanyaname.ru/disk/18-10-2024-vera-46gpb2",
#     "https://tanyaname.ru/disk/16-09-2024-siblings-j72sbf",
#     "https://tanyaname.ru/disk/14-09-2024-fandom-fest-p7z5x8",
#     "https://disk.yandex.ru/d/NMxM1lo88n8AEw",
#     "https://disk.yandex.ru/d/hAebMUXRgEgdrg",
#     "https://disk.yandex.ru/d/tSrb-uZU9AQjSg",
#     "https://disk.yandex.ru/d/AXWMZlpBia0gcw",
#     "https://disk.yandex.ru/d/oMjhOyqhgZRKwA",
#     "https://disk.yandex.ru/d/k9ymUw-fSYuuIA",
#     "https://disk.yandex.ru/d/wk2zh9T7k53oOA",
#     "https://disk.yandex.ru/d/gNWwDFl3PLh_rA",
#     "https://disk.yandex.ru/d/HzEXDLk-X9LnDQ",
#     "https://disk.yandex.ru/d/Yg-fEFalpbKx3Q",
#     "https://disk.yandex.ru/d/6eIrg_Zo_z4paQ",
#     "https://disk.yandex.ru/d/_NyiaoD7hkpQnQ",
#     "https://disk.yandex.ru/d/pp8j89Y_r36XkA",
#     "https://disk.yandex.ru/d/VhDOGAQGvQ5NAg",
#     "https://disk.yandex.ru/d/JA1W2jRoXDFbpQ",
#     "https://disk.yandex.ru/d/gP0TkNd-5HvAXw",
#     "https://disk.yandex.ru/d/ELuuJuJQzmeSjA",
#     "https://disk.yandex.ru/d/ppv4Vf9ZVP8IUw",
#     "https://disk.yandex.ru/d/Qd_2ie0I8UcswA",
#     "https://disk.yandex.ru/d/NhfqMsl_zwgrsA",
#     "https://disk.yandex.ru/d/X33nefzhO-LPYA",
#     "https://disk.yandex.ru/d/FCD3pLRB28C38g",
#     "https://disk.yandex.ru/d/Zm7labEBFEH_zA",
#     "https://disk.yandex.ru/d/-ABYmSkMg_86BQ",
# ]
#
# image_urls = []
#
#
# def fetch_yandex_folder(public_key, path="/"):
#     """
#     Возвращает список preview/sizes для всех файлов в публичной папке Яндекс.Диска (рекурсивно).
#     public_key: любой публичный URL яндекс-диска (disk.yandex.ru или yadi.sk)
#     path: путь внутри ресурса, по умолчанию "/"
#     """
#     collected = []
#     limit = 1000
#     offset = 0
#
#     while True:
#         params = {
#             "public_key": public_key,
#             "path": path,
#             "limit": limit,
#             "offset": offset,
#             # запрашиваем preview и размеры (sizes) — preview предпочтительнее
#             "fields": "items.name,items.type,items.path,items.preview,items.sizes"
#         }
#
#         try:
#             resp = requests.get(base_url, params=params, timeout=20)
#             resp.raise_for_status()
#             data = resp.json()
#         except Exception as e:
#             print("Ошибка запроса Яндекс.Диск:", e)
#             break
#
#         if "_embedded" not in data or "items" not in data["_embedded"]:
#             break
#
#         items = data["_embedded"]["items"]
#
#         for item in items:
#             itype = item.get("type")
#             if itype == "file":
#                 url = extract_image_url(item)
#                 if url:
#                     collected.append(url)
#             elif itype == "dir":
#                 # рекурсивный заход в подпапку
#                 subpath = item.get("path", "/")
#                 # короткая пауза чтобы не бить API подряд
#                 time.sleep(0.1)
#                 collected.extend(fetch_yandex_folder(public_key, subpath))
#
#         # если вернулось меньше лимита — закончить
#         if len(items) < limit:
#             break
#         offset += limit
#
#     return collected
#
#
# for url in urls:
#     print("Обрабатываю:", url)
#
#     if "yandex" not in url and "yadi.sk" not in url:
#         try:
#             resp = requests.get(url + "/pieces?design_variant=masonry&folder_path=photos", timeout=15)
#             soup = BeautifulSoup(resp.text, "html.parser")
#
#             for a in soup.find_all("a", {"data-role": "gallery-link"}):
#                 versions = a.get("data-gallery-versions")
#                 if versions:
#                     try:
#                         versions_json = json.loads(versions.replace("&quot;", '"'))
#                         if versions_json:
#                             src = versions_json[0].get("src")
#                             if src:
#                                 if src.startswith("//"):
#                                     src = "https:" + src
#                                 image_urls.append(src)
#                     except json.JSONDecodeError:
#                         continue
#         except Exception as e:
#             print("Ошибка при парсинге tanyaname:", e)
#
#     else:
#         try:
#             previews = fetch_yandex_folder(url)
#             print(f"  найдено в ЯД: {len(previews)}")
#             image_urls.extend(previews)
#         except Exception as e:
#             print("Ошибка обработки Яндекс ссылки:", e)
# seen = set()
# filtered = []
# for u in image_urls:
#     if not u:
#         continue
#     if u not in seen:
#         seen.add(u)
#         filtered.append(u)
#
# image_urls = filtered
#
# print(f"Всего уникальных изображений: {len(image_urls)}")
#
#
# images_json = json.dumps(image_urls, ensure_ascii=False)
#
# html = f"""
# <!DOCTYPE html>
# <html lang="ru">
# <head>
# <meta charset="UTF-8">
# <title>Ленивая галерея слайд-шоу</title>
# <style>
# body {{
#     font-family: Arial, sans-serif;
#     background: #f2f2f2;
#     margin: 0;
#     padding: 20px;
# }}
# h2 {{
#     margin: 0 0 12px 0;
# }}
# .gallery {{
#     display: grid;
#     grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
#     gap: 12px;
# }}
# .gallery img {{
#     width: 100%;
#     height: 140px;
#     object-fit: cover;
#     border-radius: 8px;
#     cursor: pointer;
#     transition: 0.2s;
# }}
# .gallery img:hover {{
#     transform: scale(1.03);
# }}
# #slideshow {{
#     display: none;
#     position: fixed;
#     inset: 0;
#     background: rgba(0,0,0,0.95);
#     justify-content: center;
#     align-items: center;
#     flex-direction: column;
#     z-index: 1000;
#     color: white;
# }}
# #slideshow img {{
#     max-width: 90%;
#     max-height: 80%;
#     border-radius: 10px;
# }}
# .controls {{
#     margin-top: 15px;
# }}
# button {{
#     margin: 0 10px;
#     padding: 10px 15px;
#     font-size: 16px;
#     cursor: pointer;
#     border-radius: 5px;
#     border: none;
#     background: #ff5e5e;
#     color: white;
# }}
# button:hover {{
#     background: #ff3b3b;
# }}
# #like-count {{
#     margin-top: 10px;
# }}
# </style>
# </head>
# <body>
#
# <h2>Галерея слайд-шоу ({len(image_urls)} фото)</h2>
# <div class="gallery" id="gallery"></div>
#
# <div id="slideshow">
#     <img id="slide-img" alt="Фото">
#     <div class="controls">
#         <button id="prev-btn">Prev</button>
#         <button id="like-btn">❤️ Лайк</button>
#         <button id="next-btn">Next</button>
#         <button id="close-btn">Закрыть</button>
#     </div>
#     <p id="like-count">Лайков: 0</p>
# </div>
#
# <script>
# const allImages = {images_json};
# let loadedImages = [];  // массив для подгруженных миниатюр (в порядке, как отображаются)
# const batchSize = 30;
# let currentIndex = 0;
# const likedImages = [];
#
# const gallery = document.getElementById('gallery');
# const slideshow = document.getElementById('slideshow');
# const slideImg = document.getElementById('slide-img');
# const likeCount = document.getElementById('like-count');
# const prevBtn = document.getElementById('prev-btn');
# const nextBtn = document.getElementById('next-btn');
# const closeBtn = document.getElementById('close-btn');
# const likeBtn = document.getElementById('like-btn');
#
# function loadNextBatch() {{
#     const start = loadedImages.length;
#     const end = Math.min(start + batchSize, allImages.length);
#     for (let i = start; i < end; i++) {{
#         const url = allImages[i];
#         loadedImages.push(url);
#         const img = document.createElement('img');
#         img.src = url;
#         img.loading = "lazy";
#         img.onclick = () => openSlide(i);
#         gallery.appendChild(img);
#     }}
# }}
#
# // загружаем первые 30
# loadNextBatch();
#
# // Подгружаем ещё, когда пользователь дойдёт до конца загруженных миниатюр
# function ensureLoadedFor(index) {{
#     if (index >= loadedImages.length - 5 && loadedImages.length < allImages.length) {{
#         loadNextBatch();
#     }}
# }}
#
# function openSlide(index) {{
#     currentIndex = index;
#     // если текущий индекс ещё не загружен в loadedImages (редкий случай) — загружаем батч
#     while (currentIndex >= loadedImages.length && loadedImages.length < allImages.length) {{
#         loadNextBatch();
#     }}
#     slideImg.src = allImages[currentIndex];
#     slideshow.style.display = 'flex';
#     updateLikeCount();
# }}
#
# function closeSlide() {{
#     slideshow.style.display = 'none';
# }}
#
# function nextSlide() {{
#     currentIndex++;
#     if (currentIndex >= allImages.length) currentIndex = 0; // циклический
#     ensureLoadedFor(currentIndex);
#     slideImg.src = allImages[currentIndex];
#     updateLikeCount();
# }}
#
# function prevSlide() {{
#     currentIndex = (currentIndex - 1 + allImages.length) % allImages.length;
#     ensureLoadedFor(currentIndex);
#     slideImg.src = allImages[currentIndex];
#     updateLikeCount();
# }}
#
# function likeSlide() {{
#     const currentImage = allImages[currentIndex];
#     if (!likedImages.includes(currentImage)) {{
#         likedImages.push(currentImage);
#         // визуальная реакция на лайк: кратковременно изменить фон
#         likeBtn.style.transform = 'scale(1.1)';
#         setTimeout(() => likeBtn.style.transform = '', 150);
#     }}
#     updateLikeCount();
#     console.log('Лайкнутые фото:', likedImages);
# }}
#
# function updateLikeCount() {{
#     likeCount.innerText = 'Лайков: ' + likedImages.length;
# }}
#
# // Привязка кнопок
# nextBtn.addEventListener('click', nextSlide);
# prevBtn.addEventListener('click', prevSlide);
# closeBtn.addEventListener('click', closeSlide);
# likeBtn.addEventListener('click', likeSlide);
#
# // Закрытие по Esc и переходы стрелками
# document.addEventListener('keydown', function(e) {{
#     if (slideshow.style.display === 'flex') {{
#         if (e.key === 'ArrowRight') nextSlide();
#         if (e.key === 'ArrowLeft') prevSlide();
#         if (e.key === 'Escape') closeSlide();
#     }}
# }});
#
# // Подгрузка при скролле страницы (infinite scroll мини-оптимизация)
# window.addEventListener('scroll', () => {{
#     const scrollBottom = window.innerHeight + window.scrollY;
#     if (scrollBottom >= document.body.offsetHeight - 300) {{
#         if (loadedImages.length < allImages.length) loadNextBatch();
#     }}
# }});
# </script>
#
# </body>
# </html>
# """
#
# with open("gallery.html", "w", encoding="utf-8") as f:
#     f.write(html)
#
# print("Ленивая галерея со слайд-шоу и лайками создана: gallery.html")


import requests
from bs4 import BeautifulSoup
import json
import time

def extract_image_url(item):
    sizes = item.get("sizes")
    try:
        if sizes:
            candidate = sizes[-3:-2][0].get("url")
            if candidate:
                return candidate
    except Exception:
        pass

    preview = item.get("preview")
    if preview:
        return preview

    return None

base_url = "https://cloud-api.yandex.net/v1/disk/public/resources"

urls = [
    "https://tanyaname.ru/disk/19-09-2025-dilya-drvmfr/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/16-09-2025-tatyana-j4vq0d/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/29-06-2025-gleb-i-katerina-j7s5dw/pieces?design_variant=masonry&folder_path=1",
    "https://tanyaname.ru/disk/zvezdy-vbdwmn/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/04-06-2025-viktoriya-tdjk96/pieces?design_variant=masonry&folder_path=foto",
    "https://tanyaname.ru/disk/1-maya-v9zqgr/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/14-03-2025-4-klass-sb38mz/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/16-02-2025-16-fevralya-dsswb0/pieces?design_variant=masonry&folder_path=1",
    "https://tanyaname.ru/disk/12-02-2025-egor-i-tatyana-bq325h/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/09-02-2025-schuka-ltsqf7/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/08-12-2024-dlya-viki-z6gr4b/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/06-12-2024-6-dekabrya-krh1xt/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/22-11-2024-svet-rodnoy-pesni-q578fc/pieces?design_variant=masonry&folder_path=photos-1",
    "https://tanyaname.ru/disk/03-11-2024-anya-mj3j0v/pieces?design_variant=masonry&folder_path=anya",
    "https://tanyaname.ru/disk/18-10-2024-vera-46gpb2/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/16-09-2024-siblings-j72sbf/pieces?design_variant=masonry&folder_path=photos",
    "https://tanyaname.ru/disk/14-09-2024-fandom-fest-p7z5x8/pieces?design_variant=masonry&folder_path=photos",
    "https://disk.yandex.ru/d/NMxM1lo88n8AEw",
    "https://disk.yandex.ru/d/hAebMUXRgEgdrg",
    "https://disk.yandex.ru/d/tSrb-uZU9AQjSg",
    "https://disk.yandex.ru/d/AXWMZlpBia0gcw",
    "https://disk.yandex.ru/d/oMjhOyqhgZRKwA",
    "https://disk.yandex.ru/d/k9ymUw-fSYuuIA",
    "https://disk.yandex.ru/d/wk2zh9T7k53oOA",
    "https://disk.yandex.ru/d/gNWwDFl3PLh_rA",
    "https://disk.yandex.ru/d/HzEXDLk-X9LnDQ",
    "https://disk.yandex.ru/d/Yg-fEFalpbKx3Q",
    "https://disk.yandex.ru/d/6eIrg_Zo_z4paQ",
    "https://disk.yandex.ru/d/_NyiaoD7hkpQnQ",
    "https://disk.yandex.ru/d/pp8j89Y_r36XkA",
    "https://disk.yandex.ru/d/VhDOGAQGvQ5NAg",
    "https://disk.yandex.ru/d/JA1W2jRoXDFbpQ",
    "https://disk.yandex.ru/d/gP0TkNd-5HvAXw",
    "https://disk.yandex.ru/d/ELuuJuJQzmeSjA",
    "https://disk.yandex.ru/d/ppv4Vf9ZVP8IUw",
    "https://disk.yandex.ru/d/Qd_2ie0I8UcswA",
    "https://disk.yandex.ru/d/NhfqMsl_zwgrsA",
    "https://disk.yandex.ru/d/X33nefzhO-LPYA",
    "https://disk.yandex.ru/d/FCD3pLRB28C38g",
    "https://disk.yandex.ru/d/Zm7labEBFEH_zA",
    "https://disk.yandex.ru/d/-ABYmSkMg_86BQ",
]

image_urls = []

def fetch_yandex_folder(public_key, path="/"):
    collected = []
    limit = 1000
    offset = 0

    while True:
        params = {
            "public_key": public_key,
            "path": path,
            "limit": limit,
            "offset": offset,
            "fields": "items.name,items.type,items.path,items.preview,items.sizes"
        }

        try:
            resp = requests.get(base_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print("Ошибка запроса Яндекс.Диск:", e)
            break

        if "_embedded" not in data or "items" not in data["_embedded"]:
            break

        items = data["_embedded"]["items"]

        for item in items:
            itype = item.get("type")
            if itype == "file":
                url = extract_image_url(item)
                if url:
                    collected.append(url)
            elif itype == "dir":
                subpath = item.get("path", "/")
                time.sleep(0.1)
                collected.extend(fetch_yandex_folder(public_key, subpath))

        if len(items) < limit:
            break
        offset += limit

    return collected

def fetch_tanyaname_folder(url):
    """Парсит страницу tanyaname.ru/disk/... и собирает ссылки изображений."""
    collected = []
    try:
        resp = requests.get(url + "", timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", {"data-role": "gallery-link"}):
            versions = a.get("data-gallery-versions")
            if versions:
                try:
                    versions_json = json.loads(versions.replace("&quot;", '"'))
                    if versions_json:
                        src = versions_json[0].get("src")
                        if src:
                            if src.startswith("//"):
                                src = "https:" + src
                            collected.append(src)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print("Ошибка при парсинге tanyaname:", e)
    return collected

for url in urls:
    print("Обрабатываю:", url)
    if "tanyaname.ru" in url:
        previews = fetch_tanyaname_folder(url)
        print(f"  найдено в tanyaname: {len(previews)}")
        image_urls.extend(previews)
    elif "yandex" in url or "yadi.sk" in url:
        try:
            previews = fetch_yandex_folder(url)
            print(f"  найдено в ЯД: {len(previews)}")
            image_urls.extend(previews)
        except Exception as e:
            print("Ошибка обработки Яндекс ссылки:", e)
    else:
        print("Неизвестный тип ссылки:", url)

# Убираем дубликаты и None
seen = set()
filtered = []
for u in image_urls:
    if not u:
        continue
    if u not in seen:
        seen.add(u)
        filtered.append(u)

image_urls = filtered
print(f"Всего уникальных изображений: {len(image_urls)}")

images_json = json.dumps(image_urls, ensure_ascii=False)

# --- Далее генерация HTML остаётся как ты уже имел ранее ---
html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Галерея слайд-шоу</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f2f2f2;
    margin: 0;
    padding: 20px;
}}
h2 {{
    margin: 0 0 12px 0;
}}
.gallery {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
}}
.gallery img {{
    width: 100%;
    height: 140px;
    object-fit: cover;
    border-radius: 8px;
    cursor: pointer;
    transition: 0.2s;
}}
.gallery img:hover {{
    transform: scale(1.03);
}}
#slideshow {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.95);
    justify-content: center;
    align-items: center;
    flex-direction: column;
    z-index: 1000;
    color: white;
}}
#slideshow img {{
    max-width: 90%;
    max-height: 80%;
    border-radius: 10px;
}}
.controls {{
    margin-top: 15px;
}}
button {{
    margin: 0 10px;
    padding: 10px 15px;
    font-size: 16px;
    cursor: pointer;
    border-radius: 5px;
    border: none;
    background: #ff5e5e;
    color: white;
}}
button:hover {{
    background: #ff3b3b;
}}
#like-count {{
    margin-top: 10px;
}}
</style>
</head>
<body>

<h2>Галерея слайд-шоу ({len(image_urls)} фото)</h2>
<div class="gallery" id="gallery"></div>

<div id="slideshow">
    <img id="slide-img" alt="Фото">
    <div class="controls">
        <button id="prev-btn">Prev</button>
        <button id="like-btn">❤️ Лайк</button>
        <button id="next-btn">Next</button>
        <button id="close-btn">Закрыть</button>
    </div>
    <p id="like-count">Лайков: 0</p>
</div>

<script>
const allImages = {images_json};
let loadedImages = [];
let currentIndex = 0;

const gallery = document.getElementById('gallery');
const slideshow = document.getElementById('slideshow');
const slideImg = document.getElementById('slide-img');
const likeCount = document.getElementById('like-count');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const closeBtn = document.getElementById('close-btn');
const likeBtn = document.getElementById('like-btn');

const batchSize = 30;

function loadNextBatch() {{
    const start = loadedImages.length;
    const end = Math.min(start + batchSize, allImages.length);
    for (let i = start; i < end; i++) {{
        const url = allImages[i];
        loadedImages.push(url);
        const img = document.createElement('img');
        img.src = url;
        img.loading = "lazy";
        img.onclick = () => openSlide(i);
        gallery.appendChild(img);
    }}
}}
loadNextBatch();

function ensureLoadedFor(index) {{
    if (index >= loadedImages.length - 5 && loadedImages.length < allImages.length) {{
        loadNextBatch();
    }}
}}

function openSlide(index) {{
    currentIndex = index;
    while (currentIndex >= loadedImages.length && loadedImages.length < allImages.length) {{
        loadNextBatch();
    }}
    slideImg.src = allImages[currentIndex];
    slideshow.style.display = 'flex';
    updateLikeCount();
}}

function closeSlide() {{ slideshow.style.display = 'none'; }}
function nextSlide() {{ currentIndex = (currentIndex + 1) % allImages.length; ensureLoadedFor(currentIndex); slideImg.src = allImages[currentIndex]; updateLikeCount(); }}
function prevSlide() {{ currentIndex = (currentIndex - 1 + allImages.length) % allImages.length; ensureLoadedFor(currentIndex); slideImg.src = allImages[currentIndex]; updateLikeCount(); }}

async function likeSlide() {{
    const currentImage = allImages[currentIndex];
    try {{
        const res = await fetch("/like", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ url: currentImage }})
        }});
        const data = await res.json();
        updateLikeCount(data.likes);
    }} catch(e) {{
        console.error("Ошибка при отправке лайка:", e);
    }}
    likeBtn.style.transform = "scale(1.1)";
    setTimeout(() => likeBtn.style.transform = "", 150);
}}

function updateLikeCount(count = null) {{
    if (count !== null) {{
        likeCount.innerText = "Лайков: " + count;
    }} else {{
        const currentImage = allImages[currentIndex];
        fetch("/liked_photos")
            .then(res => res.json())
            .then(data => {{
                likeCount.innerText = "Лайков: " + (data[currentImage] || 0);
            }});
    }}
}}

nextBtn.addEventListener('click', nextSlide);
prevBtn.addEventListener('click', prevSlide);
closeBtn.addEventListener('click', closeSlide);
likeBtn.addEventListener('click', likeSlide);

document.addEventListener('keydown', function(e) {{
    if (slideshow.style.display === 'flex') {{
        if (e.key === 'ArrowRight') nextSlide();
        if (e.key === 'ArrowLeft') prevSlide();
        if (e.key === 'Escape') closeSlide();
    }}
}});

window.addEventListener('scroll', () => {{
    const scrollBottom = window.innerHeight + window.scrollY;
    if (scrollBottom >= document.body.offsetHeight - 300) loadNextBatch();
}});
</script>

</body>
</html>
"""

with open("gallery.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Генерация gallery.html завершена.")

