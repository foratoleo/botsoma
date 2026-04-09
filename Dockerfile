FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install torch CPU-only first (prevents CUDA variant from being selected)
RUN pip install --no-cache-dir \
    torch==2.2.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN grep -v "^torch" requirements.txt > /tmp/reqs_no_torch.txt \
    && pip install --no-cache-dir -r /tmp/reqs_no_torch.txt \
    && pip install --no-cache-dir "numpy<2"

# sentence-transformers 2.7.0 has a known bug with newer transformers
# install compatible transformers version separately
RUN pip install --no-cache-dir transformers==4.38.0 sentence-transformers==2.7.0

# Copy application code
COPY bot/ bot/
COPY docs/ docs/

# Create appuser with writable home on /app (Azure may mount /home as read-only)
RUN useradd --create-home --shell /bin/false --home-dir /app/home appuser \
    && mkdir -p /app/home/.cache/huggingface \
    && chown -R appuser:appuser /app/home
ENV HOME=/app/home \
    HF_HOME=/app/home/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/home/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/home/.cache/huggingface
USER appuser

EXPOSE 3978

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3978/health')" || exit 1

CMD ["python", "-m", "bot.app"]
