import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or ''
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or ''
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') or ''
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///alerts.db'
    
    # Model Configuration
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'accident_model.pth'
    DATA_PATH = os.environ.get('DATA_PATH') or 'chicago_il.npz'
    
    # Alert Configuration
    DEFAULT_RADIUS_KM = float(os.environ.get('DEFAULT_RADIUS_KM') or 2.0)
    MAX_RADIUS_KM = float(os.environ.get('MAX_RADIUS_KM') or 5.0)
    RISK_THRESHOLD = float(os.environ.get('RISK_THRESHOLD') or 0.7)
    
    # SMS Configuration
    ALERT_MESSAGE = os.environ.get('ALERT_MESSAGE') or '⚠️ High accident-risk area near your location. Drive carefully.'
    
    # Flask Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
