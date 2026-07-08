from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .api import router as api_router
from prometheus_client import make_asgi_app


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Web3 Webhook Service", version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix="/v1")
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    return app


app = create_app()

