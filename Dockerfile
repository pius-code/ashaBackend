FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8080

CMD ["uv", "run", "main.py"]
