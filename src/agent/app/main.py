from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# OTEL
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# App imports
from app.core.config import settings
from app.api.routes import chat
from app.db.database import engine
from app.models import chat as chat_models  # Import models for creating tables

# Initialize settings
logger = logging.getLogger(__name__)

# Create database tables if they don't exist (for development only)
# In production, use Alembic migrations instead
def create_tables():
    from app.db.database import Base
    logger.info("Creating database tables (if they don't exist)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor().instrument_app(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Run initialization tasks when the app starts"""
    # For development only
    # In production, use Alembic migrations instead
    if settings.ENVIRONMENT == "development":
        # Create database tables on first run
        create_tables()

        # Create initial admin user if needed
        from app.db.init_db import init_db
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            init_db(db)
        finally:
            db.close()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)