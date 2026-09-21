import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config

class EtsyAPI:
    BASE_URL = "https://openapi.etsy.com/v3"
    TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
    
    def __init__(self):
        self.api_key = Config.ETSY_API_KEY
        self.shop_id = Config.ETSY_SHOP_ID
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self._load_and_refresh_token()
    
    def _load_and_refresh_token(self):
        """Load token from file and refresh if expired"""
        # Try to load from etsy_token.json first
        if os.path.exists('etsy_token.json'):
            try:
                with open('etsy_token.json', 'r') as f:
                    token_data = json.load(f)
                
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                # Calculate expiration time
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Check if token needs refresh
                if self._is_token_expired():
                    print("Access token expired, refreshing...")
                    self._refresh_access_token()
                
                return
            except Exception as e:
                print(f"Error loading token from file: {e}")
        
        # Fallback to config
        self.access_token = Config.ETSY_ACCESS_TOKEN
        # Set default expiration (1 hour from now)
        self.token_expires_at = datetime.now() + timedelta(hours=1)
    
    def _is_token_expired(self) -> bool:
        """Check if the access token is expired or will expire soon"""
        if not self.token_expires_at:
            return True
        
        # Refresh 5 minutes before actual expiration to be safe
        return datetime.now() >= self.token_expires_at - timedelta(minutes=5)
    
    def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token with token chaining"""
        if not self.refresh_token:
            print("No refresh token available, manual OAuth required")
            return False
        
        # Backup current token before refresh
        self._backup_token()
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'client_id': self.api_key,
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(self.TOKEN_URL, data=refresh_data)
            token_info = response.json()
            
            if 'access_token' in token_info:
                old_refresh_token = self.refresh_token
                self.access_token = token_info['access_token']
                self.refresh_token = token_info.get('refresh_token', self.refresh_token)
                
                # Update expiration time
                expires_in = token_info.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Add timestamp to track refresh cycle
                token_info['refreshed_at'] = datetime.now().isoformat()
                token_info['refresh_cycle_start'] = self._get_refresh_cycle_start()
                
                # Save updated token info
                with open('etsy_token.json', 'w') as f:
                    json.dump(token_info, f, indent=2)
                
                # Update .env file
                self._update_env_token(self.access_token)
                
                # Log token chaining activity
                if self.refresh_token != old_refresh_token:
                    print("Token chaining: Got new refresh token - cycle extended")
                else:
                    print("Token refresh: Same refresh token - cycle not extended")
                
                print("Access token refreshed successfully")
                return True
            else:
                print(f"Error refreshing token: {token_info}")
                # Try to restore from backup
                self._restore_token()
                return False
                
        except Exception as e:
            print(f"Error refreshing access token: {e}")
            # Try to restore from backup
            self._restore_token()
            return False
    
    def _backup_token(self):
        """Create backup of current token state"""
        try:
            if os.path.exists('etsy_token.json'):
                with open('etsy_token.json', 'r') as f:
                    token_data = json.load(f)
                
                # Save backup with timestamp
                backup_name = f"etsy_token_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_name, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                print(f"Token backup created: {backup_name}")
        except Exception as e:
            print(f"Error creating token backup: {e}")
    
    def _restore_token(self):
        """Restore token from most recent backup"""
        try:
            # Find most recent backup
            backups = [f for f in os.listdir('.') if f.startswith('etsy_token_backup_')]
            if backups:
                latest_backup = max(backups)
                with open(latest_backup, 'r') as f:
                    token_data = json.load(f)
                
                with open('etsy_token.json', 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                print(f"Token restored from backup: {latest_backup}")
                return True
        except Exception as e:
            print(f"Error restoring token backup: {e}")
        return False
    
    def _get_refresh_cycle_start(self) -> str:
        """Get the start date of the current 90-day refresh cycle"""
        try:
            if os.path.exists('etsy_token.json'):
                with open('etsy_token.json', 'r') as f:
                    token_data = json.load(f)
                return token_data.get('refresh_cycle_start', datetime.now().isoformat())
        except:
            pass
        return datetime.now().isoformat()
    
    def get_token_status(self) -> dict:
        """Get current token status and cycle information"""
        cycle_start = self._get_refresh_cycle_start()
        try:
            start_date = datetime.fromisoformat(cycle_start)
            days_in_cycle = (datetime.now() - start_date).days
            days_remaining = 90 - days_in_cycle
        except:
            days_in_cycle = 0
            days_remaining = 90
        
        return {
            'access_token_valid': not self._is_token_expired(),
            'access_token_expires': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'refresh_cycle_days': days_in_cycle,
            'refresh_cycle_remaining': days_remaining,
            'refresh_cycle_start': cycle_start,
            'token_chaining_supported': True
        }
    
    def _update_env_token(self, new_token: str):
        """Update the access token in .env file"""
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Find and replace the access token line
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('ETSY_ACCESS_TOKEN='):
                    lines[i] = f'ETSY_ACCESS_TOKEN={new_token}'
                    break
            
            with open('.env', 'w') as f:
                f.write('\n'.join(lines))
            
        except Exception as e:
            print(f"Error updating .env file: {e}")
        
    def _make_request(self, endpoint: str, params: dict = None, method: str = "GET", retry: bool = True) -> dict:
        """Make authenticated request to Etsy API with automatic token refresh"""
        headers = {
            "x-api-key": f"{self.api_key}:{Config.ETSY_SHARED_SECRET}",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check for authentication errors
            if response.status_code == 401 and retry:
                print("Authentication failed, attempting token refresh...")
                if self._refresh_access_token():
                    # Retry the request with new token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    if method == "GET":
                        response = requests.get(url, headers=headers, params=params)
                    elif method == "POST":
                        response = requests.post(url, headers=headers, json=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return None
    
    def get_orders(self, min_created_date: str = None) -> List[Dict]:
        """
        Get orders from Etsy shop
        min_created_date: ISO 8601 format date string to filter orders
        """
        endpoint = f"/application/shops/{self.shop_id}/orders"
        
        params = {}
        if min_created_date:
            params['min_created'] = min_created_date
        
        response = self._make_request(endpoint, params)
        
        if response and 'results' in response:
            return response['results']
        return []
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get specific order details"""
        endpoint = f"/application/orders/{order_id}"
        return self._make_request(endpoint)
    
    def get_receipt(self, receipt_id: str) -> Optional[Dict]:
        """Get receipt details (contains shipping info)"""
        endpoint = f"/application/receipts/{receipt_id}"
        return self._make_request(endpoint)
    
    def get_shipping_label(self, order_id: str) -> Optional[Dict]:
        """Get shipping label for US orders"""
        endpoint = f"/application/shops/{self.shop_id}/orders/{order_id}/shipping-label"
        return self._make_request(endpoint)
    
    def download_shipping_label(self, order_id: str, save_path: str) -> bool:
        """Download shipping label PDF"""
        label_info = self.get_shipping_label(order_id)
        
        if label_info and 'pdf_url' in label_info:
            try:
                response = requests.get(label_info['pdf_url'])
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            except requests.exceptions.RequestException as e:
                print(f"Failed to download shipping label: {e}")
                return False
        
        return False
    
    def is_us_customer(self, order: Dict) -> bool:
        """Check if customer is from US"""
        if 'shipping_address' in order:
            country_code = order['shipping_address'].get('country_code', '')
            return country_code == 'US'
        return False
    
    def get_order_value(self, order: Dict) -> float:
        """Get total order value"""
        return float(order.get('total_price', {}).get('value', 0) / 100)  # Convert from cents
    
    def get_ioss_number(self, order: Dict) -> str:
        """Get IOSS number for international orders"""
        return order.get('ioss_number', '')
    
    def get_personalization_details(self, order: Dict) -> Dict:
        """Extract personalization details from order"""
        personalization = {}
        
        if 'line_items' in order:
            for item in order['line_items']:
                if 'personalization' in item:
                    personalization[item['product_id']] = item['personalization']
        
        return personalization
