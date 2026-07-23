# ResolveHub Production Deployment Guide

ResolveHub is packaged as a modular FastAPI monolith with PostgreSQL, Redis, MinIO S3 object storage, and optional Temporal SLA workflows.

## Environment Variables

Key configuration variables (prefixed with `RH_`):

| Variable | Description | Default |
|---|---|---|
| `RH_ENVIRONMENT` | Environment mode (`local`, `test`, `staging`, `production`) | `production` |
| `RH_JWT_SECRET` | Secret key for JWT signing (minimum 32 characters) | *(Required)* |
| `RH_DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://...` |
| `RH_REDIS_URL` | Redis connection URL | `redis://...` |
| `RH_BROWSER_COOKIE_SECURE` | Set to `true` to require HTTPS cookies | `true` |
| `RH_STORAGE_PROVIDER` | Object storage mode (`local` or `s3`) | `s3` |
| `RH_S3_ENDPOINT_URL` | MinIO / AWS S3 endpoint URL | `http://minio:9000` |
| `RH_S3_BUCKET` | S3 bucket name for ticket attachments | `resolvehub-attachments` |
| `RH_S3_ACCESS_KEY` | S3 Access Key | *(Secret)* |
| `RH_S3_SECRET_KEY` | S3 Secret Key | *(Secret)* |
| `RH_SERVE_FRONTEND` | Set `true` to serve Vite static build from FastAPI | `true` |
| `RH_PROMETHEUS_ENABLED` | Expose `/api/v1/metrics` for scraping | `true` |

## PostgreSQL Row Level Security (RLS)

PostgreSQL RLS is enabled by migration `20260721_0008`. Every tenant query sets `app.current_organisation_id` dynamically on the database session. Superusers and database migrations automatically bypass RLS.

## Object Storage (MinIO / S3)

To run MinIO locally in Docker Compose:

```yaml
  minio:
    image: minio/minio:RELEASE.2024-01-16T16-07-38Z
    container_name: resolvehub-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadminsecret
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
```

## Running Database Migrations & Seeding Demo Data

```bash
# Run database migrations
docker compose exec api alembic upgrade head

# Seed realistic demo data
docker compose exec api python -m resolvehub.scripts.seed_demo_data
```

## Observability & Monitoring

Prometheus metrics are served at `GET /api/v1/metrics` in standard OpenMetrics text format. Scrape configurations can target port `8000` or the reverse proxy path `/api/v1/metrics`.

Readiness and liveness probes:
- Liveness: `GET /health/live` (returns 200 OK)
- Readiness: `GET /health/ready` (checks Database, Redis, and Storage; returns 200 OK or 503 Service Unavailable)
