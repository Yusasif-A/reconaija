FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# ── System packages ──
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates \
    gcc g++ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── App code ──
COPY . .

EXPOSE ${PORT:-8000}

CMD sh -c "gunicorn -w 1 -k uvicorn.workers.UvicornWorker --threads 4 --timeout 600 -b 0.0.0.0:${PORT:-8000} main:app"
