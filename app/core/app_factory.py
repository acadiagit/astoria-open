# Path: /astoria_rag_hub/app/core/app_factory.py
# Filename: app_factory.py

import os
import logging
from flask import Flask
from flask_cors import CORS

logger = logging.getLogger(__name__)

def validate_environment():
    """Checks for the presence of all required environment variables."""
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "ANTHROPIC_API_KEY" # Or the key for your chosen open-source model host
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

def create_app():
    """
    Creates and configures the Flask application.
    """
    # We will remove this validation call from main.py
    #if not validate_environment():
    #    logger.critical("Environment validation failed. Shutting down.")
    #    return None

    app = Flask(__name__)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(log_level)
    logger.info(f"Logging configured at {log_level} level")

    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logger.info("CORS configured.")

    # Import and register blueprints
    try:
        from app.routes.api_routes import register_api_routes
        register_api_routes(app)
        logger.info("API routes registered successfully.")
    except ImportError:
        logger.error("Could not import or register API routes. 'api_routes.py' may be missing or have errors.")
        # We can decide to fail here or continue with a non-functional API
        return None

    @app.route('/health')
    def health_check():
        return {"status": "ok"}, 200

    return app

#end-of-file
