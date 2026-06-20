# FinRoot — single-image build (Streamlit UI + core). Runs in Mock mode with zero keys.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FINROOT_LLM_PROVIDER=mock

WORKDIR /app

# Copy everything needed for install
COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY evals/ ./evals/
COPY results/ ./results/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install streamlit typer rich && \
    pip install -e .

# non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

# healthcheck hits the Streamlit endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:8501/_stcore/health'); " || exit 1

CMD ["streamlit", "run", "src/interface/ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
