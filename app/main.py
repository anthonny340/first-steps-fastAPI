from fastapi import FastAPI
from dotenv import load_dotenv
from app.core.db import Base, engine
from app.api.v1.posts.router import router as posts_router

load_dotenv()


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)  # dev
    app = FastAPI(title="Mi pequeño Blog - Anthonny")
    app.include_router(posts_router)

    return app

app = create_app()