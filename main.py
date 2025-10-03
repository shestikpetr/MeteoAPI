from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import Config
from app.routers import auth
from app.routers import stations_router, parameters_router, data_router
from app.admin.routes import admin_router
from app.middleware.error_handlers import add_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 FastAPI MeteoApp starting up...")
    if Config.USE_CONNECTION_POOLING:
        print("📊 Connection pooling enabled")
    else:
        print("🔗 Using single connections (legacy mode)")

    yield

    # Shutdown
    print("🛑 FastAPI MeteoApp shutting down...")
    print("📊 Closing database connections...")

    try:
        from app.database.connection import DatabaseManager
        DatabaseManager.close_all()
        print("✅ Database connections closed successfully")
    except Exception as e:
        print(f"❌ Error closing database connections: {e}")

# Create FastAPI application
app = FastAPI(
    title="MeteoApp API",
    description="REST API for meteorological data management",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(stations_router.router, prefix="/api/v1/stations", tags=["stations"])
app.include_router(parameters_router.router, prefix="/api/v1/stations", tags=["parameters"])
app.include_router(data_router.router, prefix="/api/v1/data", tags=["sensor-data"])
app.include_router(admin_router, include_in_schema=False)  # Hide admin endpoints from docs

@app.get("/", tags=["health"])
async def root():
    return {"message": "MeteoApp FastAPI is running!", "version": "2.0.0"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "MeteoApp FastAPI"}

@app.get("/database/stats", tags=["monitoring"])
async def database_stats():
    """Get database connection statistics"""
    try:
        from app.database.connection import DatabaseManager
        stats = DatabaseManager.get_connection_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    config = Config()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8085,
        reload=True,
        log_level="info"
    )