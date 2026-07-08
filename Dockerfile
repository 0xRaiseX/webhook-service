# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install --user --no-cache-dir build
COPY . .
RUN python -m build

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /root/.cache/pip /root/.cache/pip
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir /tmp/*.whl
COPY . .
USER nobody
CMD ["uvicorn", "src.webhook_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
