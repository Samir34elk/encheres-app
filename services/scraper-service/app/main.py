"""Scraper Service - Replaces GitHub Actions for web scraping automation"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import init_db
from app.scheduler.jobs import SchedulerService
from app.api import scheduler as scraper_router
from app.services.polite_client import polite_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Scraper Service...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Start scheduler (replaces GitHub Actions)
    if settings.ENABLE_SCHEDULER:
        scheduler.start()
        logger.info("✓ Scheduler started - GitHub Actions replaced!")
    else:
        logger.info("Scheduler disabled via configuration")

    yield

    logger.info("Shutting down Scraper Service...")
    scheduler.shutdown()
    await polite_client.aclose()


# Create FastAPI app
app = FastAPI(
    title="Scraper Service",
    version="1.0.0",
    description="Web scraping microservice - Replaces GitHub Actions workflows",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# Include API routers
app.include_router(scraper_router.router, prefix="/api/v1/scraper", tags=["scraper"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "scraper-service",
        "version": "1.0.0",
        "status": "running",
        "replaces": "GitHub Actions scheduled-jobs.yml",
        "scheduler_enabled": settings.ENABLE_SCHEDULER
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.scheduler.running if scheduler else False,
        "scraper_paused": polite_client.is_paused(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=8003,
        reload=settings.DEBUG
    )
