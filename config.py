import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Etsy API
    ETSY_API_KEY = os.getenv('ETSY_API_KEY')
    ETSY_SHARED_SECRET = os.getenv('ETSY_SHARED_SECRET')
    ETSY_SHOP_ID = os.getenv('ETSY_SHOP_ID')
    ETSY_ACCESS_TOKEN = os.getenv('ETSY_ACCESS_TOKEN')
    ETSY_ACCESS_TOKEN_SECRET = os.getenv('ETSY_ACCESS_TOKEN_SECRET')
    
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SERVICE_ACCOUNT_CREDENTIALS = os.getenv('GOOGLE_SERVICE_ACCOUNT_CREDENTIALS')
    
    # Supplier
    SUPPLIER_URL = os.getenv('SUPPLIER_URL', 'https://cardtrophy.com/')
    SUPPLIER_EMAIL = os.getenv('SUPPLIER_EMAIL')
    SUPPLIER_PASSWORD = os.getenv('SUPPLIER_PASSWORD')
    
    # Email
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_IMAP_SERVER = os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
    
    # Scheduling
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '18:00')
    TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
    
    # File Storage
    PSD_FILES_BASE_URL = os.getenv('PSD_FILES_BASE_URL')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    
    # Photopea
    PHOTOPEA_API_KEY = os.getenv('PHOTOPEA_API_KEY')
    
    @classmethod
    def validate(cls):
        required_fields = [
            'ETSY_API_KEY', 'ETSY_SHARED_SECRET', 'ETSY_SHOP_ID',
            'ETSY_ACCESS_TOKEN', 'GOOGLE_SHEET_ID', 'SUPPLIER_EMAIL'
        ]
        
        missing = [field for field in required_fields if not getattr(cls, field)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Create directories if they don't exist
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
