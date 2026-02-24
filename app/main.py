from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.connection import db
from app.api.v1.router import router as v1_router
from app.core.exceptions import setup_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.initialize()
    print("Database connected")
    yield
    # Shutdown
    await db.close()
    print("Database disconnected")

# Create FastAPI app
app = FastAPI(
    title="Dailymotion Registration API",
    description="User registration and activation API",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(v1_router)

# Setup exception handlers
setup_exception_handlers(app)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
