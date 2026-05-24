# ─────────────────────────────────────────────
# Stage 1 – build / dependency resolution
# ─────────────────────────────────────────────
FROM python:3.9-slim AS builder

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency manifests first (better layer caching)
COPY pyproject.toml requirement.txt ./

# Install all dependencies into a local venv
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python \
       -r requirement.txt


# ─────────────────────────────────────────────
# Stage 2 – final runtime image
# ─────────────────────────────────────────────
FROM python:3.9-slim AS runtime

# Don't write .pyc files; don't buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY . .

# Create a non-root user for security
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose the port uvicorn will listen on
EXPOSE 8000

# Health-check so orchestrators know when the API is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')"

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
