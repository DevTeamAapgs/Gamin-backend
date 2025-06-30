from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.middleware.request_logger import RequestLoggingMiddleware, SecurityMiddleware, SecurityLoggingMiddleware

# Import routes
from app.routes import auth, player, game, admin, socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers for Swagger UI and API endpoints
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Gaming Platform Backend...")
    await connect_to_mongo()
    logger.info("Gaming Platform Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gaming Platform Backend...")
    await close_mongo_connection()
    logger.info("Gaming Platform Backend shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Gaming Platform Backend",
    description="Production-grade play-to-earn crypto gaming platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add security headers middleware first
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(
    RequestLoggingMiddleware,
    exclude_paths=["/health", "/docs", "/openapi.json", "/favicon.ico"],
    enable_db_logging=True
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gaming-platform-backend"}

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(player.router, prefix="/api/v1/player", tags=["Player"])
app.include_router(game.router, prefix="/api/v1/game", tags=["Game"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(socket.router, prefix="/api/v1/socket", tags=["WebSocket"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Gaming Platform Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 