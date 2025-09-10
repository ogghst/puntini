#!/usr/bin/env python3
"""Startup script for the FastAPI server.

This script provides a convenient way to start the FastAPI development server
with proper configuration and logging.
"""

import sys
from pathlib import Path

import uvicorn

from config.config import ConfigManager

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def main():
    """Start the FastAPI development server."""
    try:
        # Get configuration
        config = ConfigManager()
        config_data = config.config

        print("🚀 Starting Business Improvement Project Management API")
        print(f"📁 Backend directory: {backend_dir}")
        print(f"⚙️  Configuration loaded from: {config.config_path}")

        # Get server configuration
        server_config = config_data.get("server", {})

        # Run the server
        uvicorn.run(
            "main:app",
            host=server_config.get("host", "0.0.0.0"),  # noqa: S104
            port=server_config.get("port", 8000),
            reload=config_data.get("api_reload", True),
            log_level=config_data.get("log_level", "info").lower(),
            access_log=True,
        )

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
