#!/usr/bin/env python3
"""
Script to generate microservices structure from monolithic backend.
This automates the migration to microservices architecture.
"""

import os
import shutil
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
SERVICES_DIR = PROJECT_ROOT / "services"

# Service definitions
SERVICES = {
    "auth-service": {
        "port": 8001,
        "models": ["user"],
        "endpoints": ["auth"],
        "schemas": ["user"],
    },
    "core-service": {
        "port": 8002,
        "models": ["sale", "lot", "favorite", "alert", "price_history", "comment"],
        "endpoints": ["sales", "lots", "favorites", "alerts"],
        "schemas": ["sale", "lot", "favorite", "alert"],
    },
    "scraper-service": {
        "port": 8003,
        "models": [],
        "endpoints": ["scheduler"],
        "schemas": ["ingestion"],
        "services": ["scraper", "batch_scraper", "sale_discovery", "ingestion"],
    },
    "notification-service": {
        "port": 8004,
        "models": ["notification"],
        "endpoints": ["notifications"],
        "schemas": ["notification"],
        "services": ["notification_service"],
    },
    "admin-service": {
        "port": 8005,
        "models": [],
        "endpoints": ["admin", "ingestion"],
        "schemas": ["ingestion"],
    },
}


def create_init_files(service_dir: Path):
    """Create __init__.py files in all directories"""
    for root, dirs, _ in os.walk(service_dir):
        for directory in dirs:
            if directory != "__pycache__":
                init_file = Path(root) / directory / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("")
                    print(f"  Created: {init_file.relative_to(PROJECT_ROOT)}")


def copy_models(service_name: str, service_config: dict):
    """Copy models from backend to service"""
    service_dir = SERVICES_DIR / service_name
    models_dir = service_dir / "app" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    for model in service_config.get("models", []):
        src = BACKEND_DIR / "app" / "models" / f"{model}.py"
        dst = models_dir / f"{model}.py"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied model: {model}.py")


def copy_schemas(service_name: str, service_config: dict):
    """Copy schemas from backend to service"""
    service_dir = SERVICES_DIR / service_name
    schemas_dir = service_dir / "app" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    for schema in service_config.get("schemas", []):
        src = BACKEND_DIR / "app" / "schemas" / f"{schema}.py"
        dst = schemas_dir / f"{schema}.py"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied schema: {schema}.py")


def copy_endpoints(service_name: str, service_config: dict):
    """Copy API endpoints from backend to service"""
    service_dir = SERVICES_DIR / service_name
    api_dir = service_dir / "app" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    for endpoint in service_config.get("endpoints", []):
        src = BACKEND_DIR / "app" / "api" / "v1" / "endpoints" / f"{endpoint}.py"
        dst = api_dir / f"{endpoint}.py"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied endpoint: {endpoint}.py")


def copy_services(service_name: str, service_config: dict):
    """Copy service files from backend to service"""
    service_dir = SERVICES_DIR / service_name
    services_dir = service_dir / "app" / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    for service in service_config.get("services", []):
        src = BACKEND_DIR / "app" / "services" / f"{service}.py"
        dst = services_dir / f"{service}.py"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied service: {service}.py")


def create_main_file(service_name: str, service_config: dict):
    """Create main.py for each service"""
    service_dir = SERVICES_DIR / service_name
    port = service_config["port"]

    main_content = f'''"""Main application file for {service_name}"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting {{settings.SERVICE_NAME}}...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {{e}}")

    yield

    logger.info("Shutting down {{settings.SERVICE_NAME}}...")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description=f"{service_name} microservice",
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

# TODO: Include API routers
# from app.api import router as api_router
# app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {{
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running"
    }}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port={port},
        reload=settings.DEBUG
    )
'''

    main_file = service_dir / "app" / "main.py"
    main_file.write_text(main_content)
    print(f"  Created: main.py")


def create_requirements(service_name: str, service_config: dict):
    """Create requirements.txt for each service"""
    service_dir = SERVICES_DIR / service_name

    base_requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "sqlalchemy==2.0.23",
        "asyncpg==0.29.0",
        "python-dotenv==1.0.0",
        "httpx==0.25.1",
    ]

    # Add service-specific requirements
    if service_name == "auth-service":
        base_requirements.extend([
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "authlib==1.2.1",
        ])

    if service_name == "scraper-service":
        base_requirements.extend([
            "playwright==1.40.0",
            "selectolax==0.3.17",
            "celery==5.3.4",
            "redis==5.0.1",
            "apscheduler==3.10.4",
        ])

    if service_name == "notification-service":
        base_requirements.extend([
            "fastapi-mail==1.4.1",
        ])

    requirements_file = service_dir / "requirements.txt"
    requirements_file.write_text("\n".join(base_requirements) + "\n")
    print(f"  Created: requirements.txt")


def create_dockerfile(service_name: str, service_config: dict):
    """Create Dockerfile for each service"""
    service_dir = SERVICES_DIR / service_name
    port = service_config["port"]

    dockerfile_content = f'''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library
COPY ../shared /app/shared

# Copy application code
COPY ./app /app/app

# Expose port
EXPOSE {port}

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''

    dockerfile = service_dir / "Dockerfile"
    dockerfile.write_text(dockerfile_content)
    print(f"  Created: Dockerfile")


def create_db_session(service_name: str):
    """Create database session file"""
    service_dir = SERVICES_DIR / service_name / "app" / "db"
    service_dir.mkdir(parents=True, exist_ok=True)

    # Copy existing session file
    src = BACKEND_DIR / "app" / "db" / "session.py"
    dst = service_dir / "session.py"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  Copied: db/session.py")


def generate_service(service_name: str, service_config: dict):
    """Generate a complete microservice"""
    print(f"\n{'='*60}")
    print(f"Generating {service_name}...")
    print(f"{'='*60}")

    service_dir = SERVICES_DIR / service_name
    service_dir.mkdir(parents=True, exist_ok=True)

    # Create structure
    copy_models(service_name, service_config)
    copy_schemas(service_name, service_config)
    copy_endpoints(service_name, service_config)
    copy_services(service_name, service_config)
    create_db_session(service_name)
    create_main_file(service_name, service_config)
    create_requirements(service_name, service_config)
    create_dockerfile(service_name, service_config)
    create_init_files(service_dir)

    print(f"✓ {service_name} generated successfully!")


def main():
    """Main function"""
    print("="*60)
    print("Microservices Generator")
    print("="*60)
    print(f"Backend: {BACKEND_DIR}")
    print(f"Services: {SERVICES_DIR}")
    print(f"Total services to generate: {len(SERVICES)}")

    for service_name, service_config in SERVICES.items():
        generate_service(service_name, service_config)

    print("\n" + "="*60)
    print("✓ All microservices generated successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review generated files in services/")
    print("2. Run: cd services/<service-name> && pip install -r requirements.txt")
    print("3. Configure environment variables")
    print("4. Start services with docker-compose.microservices.yml")


if __name__ == "__main__":
    main()
