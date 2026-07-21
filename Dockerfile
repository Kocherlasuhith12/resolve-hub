FROM python:3.12.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system resolvehub && adduser --system --ingroup resolvehub resolvehub
COPY pyproject.toml README.md ./
COPY resolvehub ./resolvehub
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY migrations ./migrations

FROM runtime AS development
USER root
RUN pip install --no-cache-dir '.[dev]'
COPY tests ./tests

FROM runtime AS production
USER resolvehub
EXPOSE 8000
CMD ["uvicorn", "resolvehub.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
