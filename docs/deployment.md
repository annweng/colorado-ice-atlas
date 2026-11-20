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

GitHub Pages is the current production host.

- Site: https://annweng.github.io/colorado-ice-atlas/
- Source: GitHub Actions workflow `.github/workflows/deploy.yml`
- Trigger: any push to `main` that touches `frontend/**`, including the daily ice snapshot commit

The Vite build uses `base: /colorado-ice-atlas/` only when `GITHUB_PAGES=true`. Local and Cursor hosting still use `/`.

Cloudflare Pages remains an optional later host. To switch, point Pages at `frontend` with build `npm run build` and output `dist`, without `GITHUB_PAGES`.

Terraform apply is **manual**. The Cloudflare module is gated by `enable_cloudflare=false`.

## Teardown

- Local: `docker compose down -v`
- Cloudflare: delete the Pages project and R2 bucket in the dashboard, or `terraform destroy` after enabling the module
- Supabase: delete the project in the dashboard
- No always-on VM is created in v1
