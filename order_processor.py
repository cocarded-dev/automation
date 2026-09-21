import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from etsy_api import EtsyAPI
from google_sheets_catalog import GoogleSheetsCatalog
from image_processor import ImageProcessor
from supplier_automation import SupplierAutomation
from config import Config

class OrderProcessor:
    def __init__(self):
        self.etsy_api = EtsyAPI()
        self.catalog = GoogleSheetsCatalog()
        self.image_processor = ImageProcessor()
        self.supplier_automation = None
        self.processed_orders_file = "processed_orders.json"
        self._load_processed_orders()
    
    def _load_processed_orders(self):
        """Load list of processed orders to avoid duplicates"""
        if os.path.exists(self.processed_orders_file):
            with open(self.processed_orders_file, 'r') as f:
                self.processed_orders = set(json.load(f))
        else:
            self.processed_orders = set()
    
    def _save_processed_order(self, order_id: str):
        """Save processed order ID to avoid reprocessing"""
        self.processed_orders.add(order_id)
        with open(self.processed_orders_file, 'w') as f:
            json.dump(list(self.processed_orders), f)
    
    def _is_order_processed(self, order_id: str) -> bool:
        """Check if order has already been processed"""
        return order_id in self.processed_orders
    
    def get_new_orders(self) -> List[Dict]:
        """Get new orders that haven't been processed yet"""
        # Get orders from the last 24 hours (adjust as needed)
        yesterday = datetime.now() - timedelta(days=1)
        min_date = yesterday.isoformat()
        
        all_orders = self.etsy_api.get_orders(min_created_date=min_date)
        
        # Filter out already processed orders
        new_orders = [
            order for order in all_orders 
            if not self._is_order_processed(str(order['order_id']))
        ]
        
        return new_orders
    
    def classify_order(self, order: Dict) -> Dict:
        """
        Classify order and determine processing requirements
        Returns classification dict with:
        - needs_personalization: bool
        - is_us_customer: bool
        - listing_id: str
        - sku: str
        - has_shipping_label: bool
        """
        classification = {
            'needs_personalization': False,
            'is_us_customer': False,
            'listing_id': '',
            'sku': '',
            'has_shipping_label': False
        }
        
        # Check if US customer
        classification['is_us_customer'] = self.etsy_api.is_us_customer(order)
        
        # Get listing ID from first line item
        if 'line_items' in order and order['line_items']:
            first_item = order['line_items'][0]
            classification['listing_id'] = str(first_item.get('listing_id', ''))
            classification['sku'] = str(first_item.get('sku', ''))
        
        # Check if personalization is needed
        if classification['listing_id']:
            classification['needs_personalization'] = self.catalog.has_personalization(
                classification['listing_id']
            )
        
        # Check for shipping label (US customers)
        if classification['is_us_customer']:
            classification['has_shipping_label'] = True
        
        return classification
    
    def process_personalization(self, order: Dict, classification: Dict) -> Optional[str]:
        """
        Process personalization for an order
        Returns path to generated PNG file
        """
        if not classification['needs_personalization']:
            return None
        
        # Get personalization details from order
        personalization_data = self.etsy_api.get_personalization_details(order)
        
        if not personalization_data:
            print("No personalization data found in order")
            return None
        
        # Get PSD file URL from catalog
        psd_url = self.catalog.get_psd_file_url(
            classification['listing_id'],
            classification['sku']
        )
        
        if not psd_url:
            print("No PSD file URL found in catalog")
            return None
        
        # Process the personalization
        order_id = str(order['order_id'])
        output_file = self.image_processor.process_personalization(
            psd_url,
            personalization_data,
            order_id
        )
        
        return output_file
    
    def download_shipping_label(self, order: Dict) -> Optional[str]:
        """Download shipping label for US orders"""
        order_id = str(order['order_id'])
        label_path = os.path.join(Config.OUTPUT_DIR, f"label_{order_id}.pdf")
        
        if self.etsy_api.download_shipping_label(order_id, label_path):
            return label_path
        
        return None
    
    def prepare_supplier_order_data(self, order: Dict, classification: Dict, personalized_file: str = None) -> Dict:
        """
        Prepare order data for supplier automation
        """
        order_id = str(order['order_id'])
        
        # Get product details from catalog
        product = self.catalog.get_product_by_listing_id(classification['listing_id'])
        
        # Build supplier order data
        supplier_data = {
            'order_id': order_id,
            'product_url': product.get('product_url', '') if product else '',
            'hologram_type': self.catalog.get_hologram_type(
                classification['listing_id'],
                classification['sku']
            ),
            'printing_file': personalized_file,
            'is_us_customer': classification['is_us_customer'],
            'order_value': self.etsy_api.get_order_value(order)
        }
        
        # Add US-specific data
        if classification['is_us_customer']:
            label_path = self.download_shipping_label(order)
            supplier_data['label_file'] = label_path
        
        # Add international-specific data
        else:
            # Format shipping address
            if 'shipping_address' in order:
                address = order['shipping_address']
                formatted_address = f"{address.get('first_name', '')} {address.get('last_name', '')}\n"
                formatted_address += f"{address.get('address_line1', '')}\n"
                if address.get('address_line2'):
                    formatted_address += f"{address['address_line2']}\n"
                formatted_address += f"{address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}\n"
                formatted_address += address.get('country_name', '')
                
                supplier_data['address'] = formatted_address
            
            supplier_data['ioss_number'] = self.etsy_api.get_ioss_number(order)
        
        return supplier_data
    
    def process_single_order(self, order: Dict) -> bool:
        """
        Process a single order through the complete workflow
        """
        order_id = str(order['order_id'])
        print(f"Processing order {order_id}...")
        
        try:
            # Classify order
            classification = self.classify_order(order)
            print(f"Order classification: {classification}")
            
            # Process personalization if needed
            personalized_file = None
            if classification['needs_personalization']:
                print("Processing personalization...")
                personalized_file = self.process_personalization(order, classification)
                
                if not personalized_file:
                    print("Failed to process personalization")
                    return False
            
            # Prepare supplier order data
            supplier_data = self.prepare_supplier_order_data(
                order,
                classification,
                personalized_file
            )
            
            # Initialize supplier automation if not already done
            if not self.supplier_automation:
                self.supplier_automation = SupplierAutomation()
                if not self.supplier_automation.login():
                    print("Failed to login to supplier website")
                    return False
            
            # Process order through supplier
            print("Processing order through supplier...")
            success = self.supplier_automation.process_order(supplier_data)
            
            if success:
                print(f"Successfully processed order {order_id}")
                self._save_processed_order(order_id)
                return True
            else:
                print(f"Failed to process order {order_id} through supplier")
                return False
                
        except Exception as e:
            print(f"Error processing order {order_id}: {e}")
            return False
    
    def process_all_new_orders(self) -> Dict[str, int]:
        """
        Process all new orders
        Returns statistics about processing
        """
        print("Fetching new orders...")
        new_orders = self.get_new_orders()
        
        stats = {
            'total': len(new_orders),
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        if not new_orders:
            print("No new orders to process")
            return stats
        
        print(f"Found {len(new_orders)} new orders")
        
        for order in new_orders:
            try:
                success = self.process_single_order(order)
                
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                print(f"Error processing order: {e}")
                stats['failed'] += 1
        
        return stats
    
    def cleanup(self):
        """Cleanup resources"""
        if self.supplier_automation:
            self.supplier_automation.close()
