# --- Layers below change rarely: base image + dependency install --------
FROM python:3.11-slim

WORKDIR /app

# Build context is the repo root (see docker-compose.yml) so this image can
# also COPY the shared ./data directory the hybrid retrieval pipeline needs
# for BM25 + NDCG eval -- backend/ alone no longer has everything it needs.

# Only the manifest is copied here, so this (slow) layer stays cached
# as long as requirements.txt itself doesn't change.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Layers above change on every commit: app source + data --------------
COPY backend/ .
COPY data/ ./data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
