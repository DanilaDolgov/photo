FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# копируем app.py + html
COPY app.py .
COPY gallery.html .

# создаём место для БД SQLite
RUN mkdir -p /data

ENV DB_PATH=/data/likes.db

EXPOSE 5000

CMD ["python", "app.py"]
