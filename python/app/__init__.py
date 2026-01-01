from fastapi import FastAPI

from .routers import provider, model, auth, conversation


def create_app(lifespan) -> FastAPI:
    app = FastAPI(title="FrameScope", lifespan=lifespan)
    app.include_router(provider.router, prefix="/api")
    app.include_router(model.router, prefix="/api")
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(conversation.router, prefix="/api")

    return app
