# Hunts Point Logistics Platform

Coordination for truck drivers, fleets, and local business — path optimization, energy tips, and delivery visibility.

## Repo structure

- **`/` (root)** — Python backend (FastAPI), optimizer, synthetic data
- **`/frontend`** — Next.js app (Driver / Company / Business views)

## Run locally

**Backend**
```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

**Frontend**
```bash
cd frontend && npm install && npm run dev
```
Set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` in `frontend/.env.local` (optional; app works with sample data if API is down).

## Deploy

- **Vercel**: Connect this repo, set **Root Directory** to `frontend`, then deploy. The frontend will use sample data unless you set `NEXT_PUBLIC_API_URL` to a hosted API.
- **Backend**: Deploy the root (FastAPI) to Railway, Render, Fly.io, or similar, then point the frontend env to that URL.
