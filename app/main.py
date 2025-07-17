from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.middleware.encryption_middleware import ResponseEncryptionMiddleware
from app.middleware.request_logger import RequestLoggingMiddleware, SecurityMiddleware, SecurityLoggingMiddleware

# Import routes
from app.routes import auth, player, game, admin, socket, roles, admincrud, common

from app.utils.crypto import AESCipher

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
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        "requestSnippetsEnabled": True,
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai",
        "syntaxHighlight.activated": True,
        "withCredentials": True,
    }
)

# Add security headers middleware first
app.mount("/public", StaticFiles(directory="public"), name="public")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:4200",
        "https://*.ngrok-free.app", 
        "https://*.ngrok.io"        
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=600 
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(
    RequestLoggingMiddleware,
    exclude_paths=["/health", "/docs", "/openapi.json", "/favicon.ico"],
    enable_db_logging=True
)

app.add_middleware(ResponseEncryptionMiddleware, crypto=AESCipher(mode="CBC"))

# # Custom OpenAPI configuration for cookie authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    

      # Add custom header parameter for Swagger (X-Plaintext)
    openapi_schema["components"]["parameters"] = {
        "XPlaintext": {
            "name": "X-Plaintext",
            "in": "header",
            "required": False,
            "schema": {"type": "string", "default": "true"},
            "description": "Tells the server to skip AES encryption/decryption (used by Swagger)"
        }
    }

    # Add cookie authentication scheme
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "Access token stored in HTTP-only cookie"
        },
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Bearer token for API clients (fallback)"
        }
    }
    


    openapi_schema["security"] = [
        {"cookieAuth": []},
        {"bearerAuth": []}
    ]

    # Add security requirements to protected endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                endpoint = openapi_schema["paths"][path][method.lower()]
                if "tags" in endpoint and any(tag in ["Authentication", "Player", "Game", "Admin","Roles"] for tag in endpoint["tags"]):
                    if "parameters" not in endpoint:
                        endpoint["parameters"] = []
                        endpoint["parameters"].append({"$ref": "#/components/parameters/XPlaintext"})
                    # if "security" not in endpoint:
                    endpoint["security"] = [
                        {"cookieAuth": []},
                        {"bearerAuth": []}
                    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema





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
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(admincrud.router, prefix="/api/v1/admincrud", tags=["Admin CRUD"])
app.include_router(common.router, prefix="/api/v1", tags=["Common"])




# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Gaming Platform Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

app.openapi = custom_openapi


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 