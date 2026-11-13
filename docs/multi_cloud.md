# Multi-cloud portability

v1 does not run on three clouds at once. The code is written so a later migration can swap hosting without rewriting ice math or the map.

## Interfaces that must stay provider-neutral

- PostgreSQL / PostGIS migrations in `database/migrations`
- FastAPI + environment variables
- Snapshot files (GeoJSON / JSON) as the object-storage payload
- Docker images for API and pipeline
- GitHub Actions today; Cloud Scheduler or EventBridge later

## Future GCP

- Cloud Run for FastAPI
- Cloud SQL PostgreSQL + PostGIS
- Cloud Storage for snapshots
- Cloud Scheduler for the daily job
- Secret Manager for `DATABASE_URL`
- Terraform module: `infrastructure/terraform/modules/gcp`

## Future AWS

- ECS Fargate (or Cloud Run equivalent) for FastAPI
- RDS PostgreSQL + PostGIS
- S3 for snapshots
- EventBridge Scheduler for the daily job
- Secrets Manager
- Terraform module: `infrastructure/terraform/modules/aws`

## Migration sequence

1. Export PostGIS (`pg_dump`) or re-load from snapshots.
2. Copy snapshot objects to the new bucket.
3. Point `DATA_DIR` / `DATABASE_URL` at the new services.
4. Shift DNS / Pages to the new frontend host.
5. Keep one daily job; do not dual-write until a cutover window.

A real GCP or AWS apply is a later portfolio enhancement and needs explicit approval because it can incur cost.
