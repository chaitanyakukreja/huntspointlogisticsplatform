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

1. Go to [vercel.com](https://vercel.com) and sign in (e.g. with GitHub).
2. **Add New Project** → Import **chaitanyakukreja/huntspointlogisticsplatform**.
3. Set **Root Directory** to `frontend` (Edit → set to `frontend`).
4. Leave **Build Command** as `npm run build` and **Output Directory** as default.
5. (Optional) Add env var `NEXT_PUBLIC_API_URL` = your hosted API URL if you deploy the backend elsewhere.
6. Deploy. The app works with built-in sample data if no API URL is set.

## Deploy backend (optional)

Deploy the Python API (Railway, Render, Fly.io, etc.) and set `NEXT_PUBLIC_API_URL` in Vercel to that URL for live data.
