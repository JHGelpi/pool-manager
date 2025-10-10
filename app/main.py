from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import (
    health_router,
    inventory_router,
    tasks_router,
    alerts_router,
    readings_router
)
from app.services.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    if settings.SCHEDULER_ENABLED:
        scheduler.start()
        print("✓ Scheduler started")
    
    yield
    
    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
        print("✓ Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="Pool Manager API",
    description="Comprehensive pool maintenance management system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(inventory_router)
app.include_router(tasks_router)
app.include_router(alerts_router)
app.include_router(readings_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Redirect to static frontend"""
    return {"message": "Pool Manager API", "docs": "/docs", "frontend": "/static/index.html"}