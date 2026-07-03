"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.routes import router as track_router


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        from src.scrapers.passtrack import close_session as passtrack_close

        await passtrack_close()

    app = FastAPI(title="Indian Visa Status", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://track.easyindianvisa.com",
            "https://track-easyindianvisa.web.app",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    limiter = Limiter(key_func=lambda: "global")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(track_router)
    return app
