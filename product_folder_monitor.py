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

class FolderEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
        self.status_file = os.path.basename(monitor.status_file)
        super().__init__()

    def on_created(self, event):
        if event.is_directory:
            # Ny GTIN-mapp skapad
            if os.path.basename(event.src_path).isdigit():
                print(f"\nNew GTIN folder detected: {event.src_path}")
                self.monitor.check_contents(event.src_path)
        else:
            # Ny fil skapad
            if os.path.basename(event.src_path) != self.status_file:
                gtin_folder = os.path.dirname(event.src_path)
                if os.path.basename(gtin_folder).isdigit():
                    print(f"\nNew file detected in GTIN folder: {event.src_path}")
                    self.monitor.check_contents(gtin_folder)

    def on_modified(self, event):
        if not event.is_directory and os.path.basename(event.src_path) != self.status_file:
            gtin_folder = os.path.dirname(event.src_path)
            if os.path.basename(gtin_folder).isdigit():
                print(f"\nFile modified in GTIN folder: {event.src_path}")
                self.monitor.check_contents(gtin_folder)

class ProductFolderMonitor:
    def __init__(self, folder_path, gs1_client):
        self.folder_path = folder_path
        self.base_path = folder_path
        self.gs1_client = gs1_client
        self.image_validator = ImageValidator()
        self.status_file = os.path.join(self.base_path, "status.json")
        self.folder_status = {}
        self.load_status()
        
        # Sätt upp file watcher
        self.event_handler = FolderEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.folder_path, recursive=True)
        self.observer.start()
        print(f"Started watching folder: {self.folder_path}")

    def __del__(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()

    def load_status(self):
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r') as f:
                self.folder_status = json.load(f)
                
    def save_status(self):
        with open(self.status_file, 'w') as f:
            json.dump(self.folder_status, f, indent=2)
            
    def check_contents(self, gtin_folder):
        # Kontrollera att det är en GTIN-mapp
        gtin = os.path.basename(gtin_folder)
        if not gtin.isdigit():
            return None
            
        print(f"\nChecking contents of GTIN folder: {gtin_folder}")
        status = ProductFolderStatus(gtin_folder)
        
        try:
            files = os.listdir(gtin_folder)
            print(f"Files found in folder: {files}")
            
            # Hantera produktbild
            product_images = [f for f in files if 
                (f.lower().startswith('product_') or 
                 (f.lower().endswith(('.tiff', '.tif', '.jpg')) and 
                  not f.lower().startswith(('planogram_', 'artwork_', 'barcode_')) and
                  (f.startswith(gtin) or f.lower().startswith('product_'))))
            ]
            
            print(f"Product images found: {product_images}")
            
            if product_images:
                img_path = os.path.join(gtin_folder, product_images[0])
                print(f"Processing image: {img_path}")
                
                # Validera bild
                valid, message = self.image_validator.validate_product_image(img_path)
                print(f"Image validation result: {valid}, {message}")
                
                if valid:
                    status.has_product_image = True
                    
                    # Skapa planogram
                    planogram_name = f"planogram_{gtin}_C1N1.png"
                    planogram_path = os.path.join(gtin_folder, planogram_name)
                    
                    if not os.path.exists(planogram_path):
                        print(f"Creating planogram at: {planogram_path}")
                        success, message = self.image_validator.convert_to_planogram(img_path, planogram_path)
                        print(f"Planogram creation result: {success}, {message}")
                        if success:
                            status.has_planogram = True
                    else:
                        status.has_planogram = True
                        print("Planogram already exists")
                else:
                    status.add_error(f"Bildfel: {message}")
            
            # Uppdatera status
            self.folder_status[gtin] = status.to_dict()
            self.save_status()
            print(f"Updated status for {gtin}: {status.to_dict()}")
            
        except Exception as e:
            print(f"Error processing folder {gtin_folder}: {str(e)}")
            status.add_error(f"Processfel: {str(e)}")
        
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