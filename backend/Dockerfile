FROM ghcr.io/astral-sh/uv:0.11.11-python3.12-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /srv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm
ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /srv
RUN useradd --system --uid 10001 app
COPY --from=build /srv/.venv /srv/.venv
COPY app ./app
COPY data ./data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
