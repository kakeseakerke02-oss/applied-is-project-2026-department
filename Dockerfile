FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/database.db

WORKDIR /app

# Тәуелділіктер коды өзгерген сайын қайта орнатылмайды.
COPY requirements.backend.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seed.py ./seed.py

RUN useradd --create-home --user-group --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data
USER appuser

EXPOSE 8000
CMD ["python", "-m", "app.container_start"]
