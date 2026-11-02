from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global unhandled exception handler to guarantee CORS headers on errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        origin = request.headers.get("origin")
        headers = {}
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"

        err_msg = str(exc)
        if "Connection refused" in err_msg or "1225" in err_msg or "connect" in err_msg.lower():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": f"Database is unavailable. Please verify DATABASE_URL in backend/.env."},
                headers=headers,
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal Server Error: {err_msg}"},
            headers=headers,
        )

    # Mount versioned API routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_PREFIX}/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
