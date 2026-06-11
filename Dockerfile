# ── Stage 1: Build Vite frontend ────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ .
RUN npm run build

# ── Stage 2: Python runtime ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System dependencies (lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo libwebp7 curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ /app/

# Copy built frontend from stage 1
COPY --from=frontend-builder /build/dist/ /app/static/

# Runtime directories
RUN mkdir -p /app/data && \
    (groupadd -g 1000 photosync 2>/dev/null || true) && \
    (useradd -u 1000 -g 1000 -d /app photosync 2>/dev/null || true) && \
    chown -R 1000:1000 /app/data 2>/dev/null || true

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8932/api/v1/system/health || exit 1

VOLUME ["/app/data"]
EXPOSE 8932

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8932", "--proxy-headers"]
