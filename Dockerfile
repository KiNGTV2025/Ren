# Build aşaması
FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# Final aşama
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PORT=8000
EXPOSE $PORT

# Gunicorn komutu shell ortamında çalıştırılacak şekilde güncellendi
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --worker-class sync --timeout 120 --access-logfile - --error-logfile -"]
