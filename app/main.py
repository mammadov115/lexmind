from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.exceptions import EmailAlreadyExistsError, FirmNameAlreadyExistsError
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle manager for the FastAPI application."""
    # Create tables automatically for development/testing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose connection pools on shutdown
    await engine.dispose()


app = FastAPI(
    title="LexMind API",
    description="Multi-tenant backend for Law Firms and Cases management.",
    version="1.0.0",
    lifespan=lifespan,
)


# Register global exception handlers for domain errors
@app.exception_handler(EmailAlreadyExistsError)
async def email_already_exists_handler(
    request: Request, exc: EmailAlreadyExistsError
) -> JSONResponse:
    """Map domain email uniqueness error to HTTP 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(FirmNameAlreadyExistsError)
async def firm_name_already_exists_handler(
    request: Request, exc: FirmNameAlreadyExistsError
) -> JSONResponse:
    """Map domain firm name uniqueness error to HTTP 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


# Include api routers
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify system status."""
    return {"status": "healthy"}
