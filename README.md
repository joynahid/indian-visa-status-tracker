# Indian Visa Status Tracker

Tracks Indian visa application status across three sources:
- `passtrack.net` for IVAC application tracking
- `indianvisaonline.gov.in` for the official Indian visa portal
- `indianvisa-bangladesh.nic.in` for the Bangladesh mission

## Architecture

- Backend: FastAPI + Playwright (Chromium) + ddddocr/2captcha
- Frontend: Next.js 14, static export to Firebase Hosting
- Deployment: Backend on DigitalOcean App Platform, frontend on Firebase Hosting
- Shared data: DigitalOcean Managed PostgreSQL for inquiries, results, webfiles, and status checks

## Local Development

### Backend
Direct Python development assumes Python 3.12+.

```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
playwright install chromium
cp ../../.env.example .env
uvicorn main:app --reload --port 8765
```

### Frontend
```bash
cd apps/frontend
npm install
BASE_API_URL=http://localhost:8765 npm run dev
```

### Docker
```bash
cp .env.example .env
docker compose up
```

## Deployment

### Backend on DigitalOcean App Platform
The backend runs as a Docker-based service on App Platform and connects to a managed PostgreSQL cluster. It listens on port `8080` and reads its runtime config from App Platform environment variables.

Required runtime env on the backend service:

- `DATABASE_URL`
- `COMMA_SEPARATED_PROXY_URLS`
- `TWO_CAPTCHA_KEY`
- `STATUS_CHECK_SECRET`

The frontend build must point `BASE_API_URL` at the public App Platform ingress URL before you export the static site.

### Frontend on Firebase
```bash
cd apps/frontend
BASE_API_URL=https://api.example.com npm run build
firebase deploy --only hosting:app
```

## Key Endpoints

- `POST /track/start` - start tracking in background, returns `{slug, status}`
- `GET /track/{slug}` - poll for results and partial data

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COMMA_SEPARATED_PROXY_URLS` | Yes in production | Proxy URL list for Indian visa sites |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `POSTGRES_DB` | Local/compose | Shared database name |
| `POSTGRES_USER` | Local/compose | Shared database user |
| `POSTGRES_PASSWORD` | Local/compose | Shared database password |
| `TWO_CAPTCHA_KEY` | Recommended | 2captcha API key for captcha fallback |
| `STATUS_CHECK_SECRET` | Recommended | Shared secret for `/status/run` |
| `PORT` | No, default `8080` | Server port |
