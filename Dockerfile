FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system resolvehub && adduser --system --ingroup resolvehub resolvehub
COPY pyproject.toml README.md requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY resolvehub ./resolvehub
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./
RUN chmod +x /app/docker-entrypoint.sh

FROM runtime AS development
USER root
RUN pip install --no-cache-dir '.[dev]'
COPY tests ./tests

FROM runtime AS production
USER resolvehub
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
