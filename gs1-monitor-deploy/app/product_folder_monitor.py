import os
from pathlib import Path
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gs1_digital_assets import GS1DigitalAssets
from gs1_trade_item import GS1TradeItem
import json
from datetime import datetime, timedelta  # Add timedelta import
from image_validator import ImageValidator
from PIL import Image
from wand.image import Image as WandImage

class ProductFolderStatus:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.gtin = os.path.basename(folder_path)
        self.has_product_image = False
        self.has_artwork = False
        self.has_planogram = False
        self.has_barcode = False
        self.last_updated = datetime.now().isoformat()
        self.validation_status = "Incomplete"
        self.manually_approved = False
        self.approval_date = None
        self.scheduled_deletion_date = None
        self.validation_errors = []
        
    def add_error(self, error_message):
        self.validation_errors.append(error_message)
        
    def to_dict(self):
        return {
            "gtin": self.gtin,
            "has_product_image": self.has_product_image,
            "has_artwork": self.has_artwork,
            "has_planogram": self.has_planogram,
            "has_barcode": self.has_barcode,
            "last_updated": self.last_updated,
            "validation_status": self.validation_status,
            "manually_approved": self.manually_approved,
            "approval_date": self.approval_date,
            "scheduled_deletion_date": self.scheduled_deletion_date,  # Added comma here
            "validation_errors": self.validation_errors
        }

class ProductFolderMonitor:
    def __init__(self, folder_path, gs1_client):
        self.folder_path = folder_path
        self.base_path = folder_path  # Add this line
        self.gs1_client = gs1_client
        self.image_validator = ImageValidator()
        self.status_file = os.path.join(self.base_path, "status.json")
        self.folder_status = {}
        self.load_status()

    def load_status(self):
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r') as f:
                self.folder_status = json.load(f)
                
    def save_status(self):
        with open(self.status_file, 'w') as f:
            json.dump(self.folder_status, f, indent=2)
            
    def check_contents(self, gtin_folder):
        gtin = os.path.basename(gtin_folder)
        status = ProductFolderStatus(gtin_folder)
        files = os.listdir(gtin_folder)
        
        # Hantera produktbild
        product_images = [f for f in files if 
            (f.lower().startswith('product_') or 
             (f.lower().endswith(('.tiff', '.tif', '.jpg')) and 
              not f.lower().startswith(('planogram_', 'artwork_', 'barcode_')) and
              (f.startswith(gtin) or f.lower().startswith('product_'))))
        ]
        
        if product_images:
            img_path = os.path.join(gtin_folder, product_images[0])
            print(f"\nProcessing product image: {img_path}")
            
            # Validera bild
            valid, message = self.image_validator.validate_product_image(img_path)
            if not valid:
                status.add_error(f"Bildfel: {message}")
            else:
                status.has_product_image = True
                
                # Skapa planogram om det behövs
                planogram_name = f"planogram_{gtin}_C1N1.png"
                planogram_path = os.path.join(gtin_folder, planogram_name)
                
                if not os.path.exists(planogram_path):
                    success, message = self.image_validator.convert_to_planogram(img_path, planogram_path)
                    if not success:
                        status.add_error(f"Planogram error: {message}")
                    else:
                        status.has_planogram = True
                else:
                    status.has_planogram = True
        
        # Hantera artwork
        artwork_files = [f for f in files if f.lower().startswith('artwork_')]
        if artwork_files:
            status.has_artwork = True
        
        # Hantera streckkod
        barcode_files = [f for f in files if f.lower().startswith('barcode_')]
        if barcode_files:
            status.has_barcode = True
        
        # Uppdatera validation_status
        status.validation_status = "Complete" if all([
            status.has_product_image,
            status.has_artwork,
            status.has_planogram,
            status.has_barcode
        ]) else "Incomplete"
        
        # Behåll existerande godkännande-status om det finns
        if gtin in self.folder_status:
            old_status = self.folder_status[gtin]
            status.manually_approved = old_status.get('manually_approved', False)
            status.approval_date = old_status.get('approval_date')
            status.scheduled_deletion_date = old_status.get('scheduled_deletion_date')
        
        # Uppdatera status
        self.folder_status[gtin] = status.to_dict()
        self.save_status()
        
        return status

    def check_all_folders(self):
        if not os.path.exists(self.base_path):
            return
            
        # Hämta alla existerande GTIN-mappar
        existing_folders = {
            folder_name for folder_name in os.listdir(self.base_path) 
            if os.path.isdir(os.path.join(self.base_path, folder_name)) 
            and folder_name.isdigit()
        }
        
        # Hämta alla GTINs i status-filen
        status_gtins = set(self.folder_status.keys())
        
        # Ta bort status för mappar som inte längre existerar
        removed_gtins = status_gtins - existing_folders
        for gtin in removed_gtins:
            print(f"Removing status for deleted folder: {gtin}")
            del self.folder_status[gtin]
        
        # Uppdatera status för existerande mappar
        for folder_name in existing_folders:
            folder_path = os.path.join(self.base_path, folder_name)
            self.check_contents(folder_path)
        
        # Spara uppdaterad status
        self.save_status()

    def notify_complete_folder(self, gtin):
        # You can implement different notification methods here
        print(f"Folder for GTIN {gtin} is complete and ready for upload!")