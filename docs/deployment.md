# Deployment

## Local

```bash
python scripts/download_inventory.py
python scripts/run_pipeline.py
cd frontend && npm install && npm run dev
# in another shell
PYTHONPATH=. python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

Or:

```bash
docker compose up --build
```

Frontend: http://127.0.0.1:3847  
API docs: http://127.0.0.1:8765/docs

## Free-tier public hosting

1. Run the pipeline so `frontend/public/data` is populated.
2. Build the frontend (`npm run build`).
3. Host `frontend/dist` on Cloudflare Pages (or any static host).
4. Optionally create Supabase PostGIS, run `001_init.sql`, and `DATABASE_URL` for the API.
5. Point GitHub Actions daily workflow at the same pipeline; commit or artifact the snapshots.

Terraform apply is **manual**. The Cloudflare module is gated by `enable_cloudflare=false`.

## Teardown

- Local: `docker compose down -v`
- Cloudflare: delete the Pages project and R2 bucket in the dashboard, or `terraform destroy` after enabling the module
- Supabase: delete the project in the dashboard
- No always-on VM is created in v1
