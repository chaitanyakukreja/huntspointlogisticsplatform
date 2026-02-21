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

## Deploy to Vercel

**Important:** Set **Root Directory** to **`frontend`** in Vercel (Settings → General → Root Directory). Otherwise Vercel will try to build the Python API and fail with "No fastapi entrypoint found".

1. Go to [vercel.com](https://vercel.com) → Add New Project → Import **chaitanyakukreja/huntspointlogisticsplatform**.
2. **Before deploying:** Settings → General → **Root Directory** → set to **`frontend`** → Save.
3. Deploy. Build Command stays `npm run build`, Output Directory default.
4. (Optional) Add env var `NEXT_PUBLIC_API_URL` if you host the backend elsewhere.
5. See [DEPLOY.md](./DEPLOY.md) if you already see the FastAPI error.

## Deploy backend (optional)

Deploy the Python API (Railway, Render, Fly.io, etc.) and set `NEXT_PUBLIC_API_URL` in Vercel to that URL for live data.
