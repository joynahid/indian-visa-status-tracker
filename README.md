# Indian Visa Status Tracker

Tracks Indian visa application status across three sources:
- **passtrack.net** — IVAC application tracking
- **indianvisaonline.gov.in** — official Indian visa portal
- **indianvisa-bangladesh.nic.in** — Bangladesh mission

## Architecture

- **Backend**: FastAPI + Playwright (Chromium) + ddddocr/2captcha
- **Frontend**: Next.js 14 (App Router, static export → Firebase Hosting)
- **Deployment**: Backend on Google Cloud Run, Frontend on Firebase Hosting

## Local Development

### Backend
```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp ../../.env.example .env  # then fill in real values
uvicorn main:app --reload --port 8765
```

### Frontend
```bash
cd apps/frontend
npm install
BASE_API_URL=http://localhost:8765 npm run dev
```

### Docker (full stack)
```bash
cp .env.example .env  # fill in real values
docker compose up
```

## Deployment

### Backend → Cloud Run
```bash
docker build -f apps/backend/Dockerfile.prod -t REGION-docker.pkg.dev/PROJECT/cloud-run-source-deploy/indian-visa-backend:latest ./apps/backend
docker push REGION-docker.pkg.dev/PROJECT/cloud-run-source-deploy/indian-visa-backend:latest
gcloud run deploy indian-visa-status \
  --image REGION-docker.pkg.dev/PROJECT/cloud-run-source-deploy/indian-visa-backend:latest \
  --region asia-southeast1 \
  --set-env-vars "COMMA_SEPARATED_PROXY_URLS=...,TWO_CAPTCHA_KEY=..." \
  --memory 2Gi --cpu 2 --min-instances 0 --max-instances 10
```

### Frontend → Firebase
```bash
cd apps/frontend
npm run build
firebase deploy --only hosting:app
```

## Key Endpoints

- `POST /track/start` — start tracking in background, returns `{slug, status}`
- `GET /track/{slug}` — poll for results (returns partial data as each source completes)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COMMA_SEPARATED_PROXY_URLS` | Yes (production) | Singapore proxy URL for Indian visa sites |
| `TWO_CAPTCHA_KEY` | Recommended | 2captcha API key for captcha fallback |
| `PORT` | No (default 8080) | Server port |
