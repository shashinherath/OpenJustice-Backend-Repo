# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────
#  Stage 1 — Builder: install Python dependencies with uv
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools needed for some C-extension packages (asyncpg, pydub, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock* ./

# Install only production dependencies (no dev extras like pytest/black/mypy)
RUN uv pip install --system .


# ─────────────────────────────────────────────────────────────
#  Stage 2 — Runtime: lean production image
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps:
#   ffmpeg      — audio transcoding (pydub)
#   libsndfile1 — soundfile library
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Create directories that main.py needs at startup
# (These are ephemeral — for Azure, migrate to Azure Blob Storage)
RUN mkdir -p temp/audio media/audio uploads

# Copy and make entrypoint executable
RUN chmod +x start.sh

# Run as non-root for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# start.sh runs: alembic upgrade head && uvicorn
CMD ["./start.sh"]
