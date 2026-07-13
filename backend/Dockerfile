# --- Layers below change rarely: base image + dependency install --------
FROM python:3.11-slim

WORKDIR /app

# Only the manifest is copied here, so this (slow) layer stays cached
# as long as requirements.txt itself doesn't change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Layers above change on every commit: app source ---------------------
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
