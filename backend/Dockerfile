FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY modeling /app/modeling
COPY data /app/data
COPY scripts /app/scripts
COPY database /app/database
COPY frontend/public/data /app/frontend/public/data

ENV PYTHONPATH=/app:/app/backend
ENV DATA_DIR=/app/frontend/public/data
EXPOSE 8765
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765", "--app-dir", "backend"]
