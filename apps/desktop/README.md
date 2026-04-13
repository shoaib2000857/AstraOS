# AstraOS Desktop (frontend)

Development:

```bash
cd apps/desktop
python -m http.server  # not needed; use npm
# install deps
npm install
npm run dev
```

The frontend proxies `/api` requests to `http://127.0.0.1:8000` as configured in `vite.config.ts`.
