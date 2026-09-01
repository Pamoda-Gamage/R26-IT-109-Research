FROM python:3.12-slim

# build-essential covers any dependency (e.g. chromadb's hnswlib) that needs to
# compile from source for this platform/python combo; curl fetches the uv installer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Install dependencies in their own layer so code-only changes don't bust the cache.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

ENV PATH="/app/.venv/bin:${PATH}"
# Strip any CR characters before making the entrypoint executable: a Windows
# checkout (core.autocrlf=true) leaves CRLF endings, which breaks the shebang.
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
