import os
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import Dict, List, Optional
from config import Config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class GoogleSheetsCatalog:
    def __init__(self):
        self.sheet_id = Config.GOOGLE_SHEET_ID
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            # Try GitHub Secret first (for GitHub Actions)
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_CREDENTIALS'):
                import json
                credentials_dict = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_CREDENTIALS'))
                creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
            # Fall back to file (for local development)
            elif os.path.exists('service_account.json'):
                creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
            else:
                raise ValueError("No service account credentials found")
            
            self.service = build('sheets', 'v4', credentials=creds)
            print("Service account authentication successful")
        except Exception as e:
            print(f"Service account authentication failed: {e}")
            raise
    
    def get_catalog_data(self) -> pd.DataFrame:
        """
        Fetch catalog data from Google Sheets
        Expected columns: listing_id, sku, product_name, has_personalization, 
                         psd_file_url, file_variant, hologram_type
        """
        range_name = 'Catalog!A:G'  # Adjust based on your sheet structure
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print("No data found in catalog")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
            
        except Exception as e:
            print(f"Error fetching catalog data: {e}")
            return pd.DataFrame()
    
    def get_product_by_listing_id(self, listing_id: str) -> Optional[Dict]:
        """Get product details by listing ID"""
        df = self.get_catalog_data()
        
        if df.empty:
            return None
        
        product = df[df['listing_id'] == listing_id]
        
        if product.empty:
            return None
        
        return product.iloc[0].to_dict()
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product details by SKU"""
        df = self.get_catalog_data()
        
        if df.empty:
            return None
        
        product = df[df['sku'] == sku]
        
        if product.empty:
            return None
        
        return product.iloc[0].to_dict()
    
    def has_personalization(self, listing_id: str) -> bool:
        """Check if product has personalization option"""
        product = self.get_product_by_listing_id(listing_id)
        
        if product:
            return str(product.get('has_personalization', 'false')).lower() == 'true'
        
        return False
    
    def get_psd_file_url(self, listing_id: str, sku: str = None) -> Optional[str]:
        """Get PSD file URL for a product"""
        if sku:
            product = self.get_product_by_sku(sku)
        else:
            product = self.get_product_by_listing_id(listing_id)
        
        if product:
            return product.get('psd_file_url')
        
        return None
    
    def get_hologram_type(self, listing_id: str, sku: str = None) -> str:
        """Get hologram type for a product"""
        if sku:
            product = self.get_product_by_sku(sku)
        else:
            product = self.get_product_by_listing_id(listing_id)
        
        if product:
            return product.get('hologram_type', 'standard')
        
        return 'standard'
    
    def get_file_variant(self, listing_id: str, sku: str = None) -> str:
        """Get file variant for a product"""
        if sku:
            product = self.get_product_by_sku(sku)
        else:
            product = self.get_product_by_listing_id(listing_id)
        
        if product:
            return product.get('file_variant', 'single')
        
        return 'single'
