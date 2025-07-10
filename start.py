#!/usr/bin/env python3
"""
Gaming Platform Backend Startup Script
"""

import os
import sys
from threading import local
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
def main():
    """Main startup function."""
    print("🎮 Starting Gaming Platform Backend...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Using default configuration.")
        print("   Copy env.example to .env and configure your settings.")
    
    # Set default configuration
    host = "localhost"
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🌐 Server will run on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"❤️  Health check: http://{host}:{port}/health")
    
    try:
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 