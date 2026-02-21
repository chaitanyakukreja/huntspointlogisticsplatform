# Deploy to Vercel (fix "No fastapi entrypoint" error)

Vercel is building from the **repo root** and detecting the Python API. You must tell it to build only the **Next.js app** in the `frontend` folder.

## Fix: Set Root Directory

1. Open your project on [Vercel](https://vercel.com).
2. Go to **Settings** → **General**.
3. Under **Root Directory**, click **Edit**.
4. Enter: **`frontend`**
5. Click **Save**.
6. Go to **Deployments** → open the **⋯** on the latest deployment → **Redeploy**.

Vercel will then build from `frontend/` (Next.js) and stop looking for FastAPI.

## Optional: Environment variables

- **NEXT_PUBLIC_API_URL** — set this if you host the backend elsewhere (e.g. Railway, Render). Leave empty to use built-in sample data.

## Repo note

This repo has two parts:

- **Root** — Python/FastAPI backend (not built by Vercel).
- **frontend/** — Next.js app (this is what Vercel should build).
