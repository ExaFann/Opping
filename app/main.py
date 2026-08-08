from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from starlette.staticfiles import StaticFiles

from app.api import router
from app.config import Settings, get_settings
from app.database import Base, create_database
from app.models import CATEGORY_SEED, Category
from app.services.ai import build_ai_provider
from app.services.storage import LocalStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    engine, session_factory = create_database(app_settings.database_url)
    storage = LocalStorage(app_settings.upload_dir, app_settings.max_image_bytes)
    ai_provider = build_ai_provider(app_settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        storage.initialize()
        Base.metadata.create_all(engine)
        with session_factory() as db:
            existing = set(db.scalars(select(Category.slug)))
            for category in CATEGORY_SEED:
                if category["slug"] not in existing:
                    db.add(Category(**category))
            db.commit()
        yield
        engine.dispose()

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        description="AI-assisted inventory digitisation for second-hand shops.",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.storage = storage
    app.state.ai_provider = ai_provider

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=app_settings.api_prefix)
    app.mount("/media", StaticFiles(directory=storage.root, check_dir=False), name="media")
    return app


app = create_app()

