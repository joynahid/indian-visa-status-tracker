FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 libglib2.0-0 \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 \
    libxkbcommon0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --no-cache-dir setuptools \
    "numpy>=2.1" ddddocr \
    aiohttp beautifulsoup4 fastapi google-cloud-firestore pandas pillow \
    pydantic pydantic-settings python-dotenv \
    python-multipart shortuuid slowapi "uvicorn[standard]" \
    playwright

RUN playwright install chromium && playwright install-deps chromium

COPY . .

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765", "--reload"]
