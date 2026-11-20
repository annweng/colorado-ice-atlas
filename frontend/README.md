# Frontend

Vite + React + TypeScript map for Colorado Ice Atlas. Production is a static build served from GitHub Pages; it does not call FastAPI.

```bash
npm install
npm run dev
```

Dev server: http://127.0.0.1:3847 (proxies `/api` to the optional FastAPI on 8765).

```bash
GITHUB_PAGES=true npm run build
```

That sets `base` to `/colorado-ice-atlas/` for project Pages. Local and Cursor builds leave `base` as `/`.

Stack, basemaps, and snapshot files: `docs/stack.md`.
