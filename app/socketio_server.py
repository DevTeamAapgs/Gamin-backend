import socketio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.socket import setup_socketio_routes
from app.db.mongo import connect_to_mongo, get_database
import logging

# Configure logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    db = get_database()
    try:
        await db.command("ping")
        logger.info("✅ MongoDB connection established!")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        import sys
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Socket.IO server...")

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI(lifespan=lifespan)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Setup all Socket.IO routes and event handlers
setup_socketio_routes(sio, app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)