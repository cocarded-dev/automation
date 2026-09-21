import os
import requests
from PIL import Image, ImageDraw, ImageFont
from psd_tools import PSDImage
from typing import Dict, Optional
from config import Config

class ImageProcessor:
    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        self.output_dir = Config.OUTPUT_DIR
        self.target_size = (1013, 642)  # Required output dimensions
    
    def download_psd(self, url: str, filename: str) -> str:
        """Download PSD file from URL"""
        save_path = os.path.join(self.temp_dir, filename)
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return save_path
        except requests.exceptions.RequestException as e:
            print(f"Failed to download PSD: {e}")
            return None
    
    def edit_psd_with_photopea(self, psd_path: str, personalization_data: Dict, output_filename: str) -> Optional[str]:
        """
        Edit PSD file using Photopea API
        This is a placeholder - actual implementation depends on Photopea's API availability
        """
        # Photopea might not have a public API, so we'll use alternative approach
        # For now, this serves as a placeholder for potential API integration
        print("Photopea API integration - to be implemented based on API availability")
        return self.edit_psd_locally(psd_path, personalization_data, output_filename)
    
    def edit_psd_locally(self, psd_path: str, personalization_data: Dict, output_filename: str) -> Optional[str]:
        """
        Edit PSD file locally using psd-tools and Pillow
        This is a fallback method when Photopea API is not available
        """
        try:
            # Load PSD file
            psd = PSDImage.open(psd_path)
            
            # Convert to PIL Image for editing
            image = psd.composite()
            
            # Resize to target dimensions
            image = image.resize(self.target_size, Image.Resampling.LANCZOS)
            
            # Add personalization text (basic implementation)
            draw = ImageDraw.Draw(image)
            
            # Try to use a default font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Add personalization text at a default position
            # This should be customized based on your PSD template structure
            y_position = 300
            for key, value in personalization_data.items():
                text = f"{key}: {value}"
                draw.text((50, y_position), text, fill='black', font=font)
                y_position += 50
            
            # Save as PNG
            output_path = os.path.join(self.output_dir, output_filename)
            image.save(output_path, 'PNG')
            
            return output_path
            
        except Exception as e:
            print(f"Error editing PSD locally: {e}")
            return None
    
    def process_personalization(self, psd_url: str, personalization_data: Dict, order_id: str) -> Optional[str]:
        """
        Main method to process personalization
        Downloads PSD, edits it, and returns path to output PNG
        """
        # Download PSD
        filename = f"order_{order_id}.psd"
        psd_path = self.download_psd(psd_url, filename)
        
        if not psd_path:
            return None
        
        # Generate output filename
        output_filename = f"order_{order_id}_personalized.png"
        
        # Try Photopea first, fall back to local editing
        if Config.PHOTOPEA_API_KEY:
            result = self.edit_psd_with_photopea(psd_path, personalization_data, output_filename)
        else:
            result = self.edit_psd_locally(psd_path, personalization_data, output_filename)
        
        # Clean up temporary PSD file
        if os.path.exists(psd_path):
            os.remove(psd_path)
        
        return result
    
    def resize_image(self, input_path: str, output_path: str = None) -> str:
        """Resize image to target dimensions"""
        if not output_path:
            output_path = input_path
        
        try:
            image = Image.open(input_path)
            resized = image.resize(self.target_size, Image.Resampling.LANCZOS)
            resized.save(output_path)
            return output_path
        except Exception as e:
            print(f"Error resizing image: {e}")
            return None
