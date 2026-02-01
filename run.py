#!/usr/bin/env python3
"""
Accident Hotspot Alert System - Main Entry Point

This script initializes and runs the Flask application with proper error handling
and configuration management.
"""

import os
import sys
import logging
from app import app, init_db
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('accident_alert.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_requirements():

    required_files = ['chicago_il.npz']
    
    for file in required_files:
        if not os.path.exists(file):
            logger.warning(f"Required file '{file}' not found. The system will use demo data.")
    
    # Check Twilio configuration
    if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, Config.TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured. SMS alerts will run in demo mode.")
        logger.info("Set the following environment variables:")
        logger.info("- TWILIO_ACCOUNT_SID")
        logger.info("- TWILIO_AUTH_TOKEN") 
        logger.info("- TWILIO_PHONE_NUMBER")

def main():
    """Main application entry point."""
    logger.info("Starting Accident Hotspot Alert System...")
    
    # Check requirements
    check_requirements()
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Display startup information
    logger.info("=" * 50)
    logger.info("ACCIDENT HOTSPOT ALERT SYSTEM")
    logger.info("=" * 50)
    logger.info(f"Server running on: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    logger.info(f"Default search radius: {Config.DEFAULT_RADIUS_KM} km")
    logger.info(f"Risk threshold: {Config.RISK_THRESHOLD}")
    logger.info("=" * 50)
    
    if not all([Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN, Config.TWILIO_PHONE_NUMBER]):
        logger.info("📱 SMS alerts: DEMO MODE (no actual messages will be sent)")
    else:
        logger.info("📱 SMS alerts: ENABLED")
    
    # Start the Flask application
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
