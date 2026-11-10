FROM python:3.14-slim

COPY --from=docker.io/astral/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app

ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project

COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]