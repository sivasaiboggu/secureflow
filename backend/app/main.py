from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app
import time

from app.config.settings import settings
from app.config.database import engine, Base
from app.api.v1.router import api_router
from app.core.middleware import RequestLoggingMiddleware, MetricsMiddleware
from app.core.exceptions import CustomException
from app.utils.logger import setup_logging
from sqlalchemy import text

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    logger.info("Starting SecureFlow application...")
    # Create database tables on start
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception:
        # Driver errors can include the database user, host or DSN. Keep them
        # out of logs; the readiness probe reports the outage separately.
        logger.error("Database tables could not be created or verified at startup.")
    yield
    logger.info("Shutting down SecureFlow application...")

# Create FastAPI app
app = FastAPI(
    title="SecureFlow API",
    description="Cloud security posture research prototype: AWS listing/check workflows, explicit sample-data demos, and review-only remediation plans.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Exception handlers
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Health check endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "secureflow"}

@app.get("/ready")
async def readiness_check():
    # Check database connection
    try:
        from app.config.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready"}
    except Exception:
        # Driver errors can include the database user, host or DSN. The probe is
        # unauthenticated, so neither the response nor the log may carry them.
        logger.error("Readiness check failed: database did not answer a simple query.")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"}
        )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
