from flask import Flask, render_template, jsonify, request, redirect, url_for
from product_folder_monitor import ProductFolderMonitor, ProductFolderStatus
from gs1_digital_assets import GS1DigitalAssets
import shutil
import os
from datetime import datetime, timedelta
import threading
import time
import json
import errno

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

def get_watch_folder():
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        primary_folder = os.getenv('WATCH_FOLDER', '/data')
        fallback_folder = os.getenv('WATCH_FOLDER_FALLBACK', '/data_local')
    else:
        # Utvecklingsmiljö - använd lokala mappar
        base_dir = os.path.dirname(os.path.abspath(__file__))
        primary_folder = os.path.join(base_dir, 'product_images')
        fallback_folder = primary_folder  # Samma mapp i utveckling
    
    try:
        # Testa primär mapp
        os.listdir(primary_folder)
        print(f"Using folder: {primary_folder}")
        return primary_folder
    except OSError as e:
        if e.errno == errno.ENOENT or e.errno == errno.ENOTCONN:
            print(f"Primary folder not accessible, using fallback: {fallback_folder}")
            # Skapa fallback-mapp om den inte finns
            os.makedirs(fallback_folder, exist_ok=True)
            return fallback_folder
        raise

# Add configuration storage
# Update configuration to use environment variable
config = {
    'watch_folder': get_watch_folder()
}

# Initialize GS1 client with your credentials
gs1_client = GS1DigitalAssets(
    client_id=os.getenv('GS1_CLIENT_ID'),
    client_secret=os.getenv('GS1_CLIENT_SECRET'),
    username=os.getenv('GS1_USERNAME'),
    password=os.getenv('GS1_PASSWORD')
)

# Create monitor with configurable path
monitor = ProductFolderMonitor(config['watch_folder'], gs1_client)

@app.route('/select_folder', methods=['GET'])
@app.route('/update_folder', methods=['POST'])
def update_folder():
    new_folder = request.form.get('folder_path')
    if new_folder and os.path.exists(new_folder):
        config['watch_folder'] = new_folder
        global monitor
        monitor = ProductFolderMonitor(new_folder, gs1_client)
        # Spara valet i en config-fil
        with open('folder_config.json', 'w') as f:
            json.dump({'watch_folder': new_folder}, f)
        return jsonify({"success": True, "message": "Mapp uppdaterad"})
    return jsonify({"success": False, "message": "Ogiltig mappsökväg"}), 400

def check_and_delete_expired_folders():
    while True:
        current_time = datetime.now()
        for gtin, status in monitor.folder_status.items():
            if (status.get('manually_approved', False) and 
                status.get('scheduled_deletion_date') and 
                datetime.fromisoformat(status['scheduled_deletion_date']) <= current_time):
                folder_path = f"{config['watch_folder']}/{gtin}"
                try:
                    shutil.rmtree(folder_path)
                    del monitor.folder_status[gtin]
                    monitor.save_status()
                except Exception as e:
                    print(f"Kunde inte ta bort mapp för {gtin}: {str(e)}")
        time.sleep(3600)  # Kolla en gång i timmen

@app.route('/approve/<gtin>', methods=['POST'])
def approve_gtin(gtin):
    try:
        folder_path = os.path.join(config['watch_folder'], gtin)
        
        # Kontrollera att mappen finns
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': 'GTIN folder not found'})
        
        # Uppdatera status
        status = monitor.check_contents(folder_path)
        
        if gtin in monitor.folder_status:
            status_dict = monitor.folder_status[gtin]
            status_dict['manually_approved'] = True
            status_dict['approval_date'] = datetime.now().isoformat()
            # Sätt borttagningsdatum till 30 dagar från nu
            deletion_date = datetime.now() + timedelta(days=30)
            status_dict['scheduled_deletion_date'] = deletion_date.isoformat()
            monitor.save_status()
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Failed to update status'})
    except Exception as e:
        print(f"Error in approve_gtin: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/disapprove/<gtin>', methods=['POST'])
def disapprove_gtin(gtin):
    if gtin in monitor.folder_status:
        status = ProductFolderStatus(f"{config['watch_folder']}/{gtin}")
        status.check_contents()
        status.disapprove()
        monitor.folder_status[gtin] = status.to_dict()
        monitor.save_status()
        return jsonify({"success": True, "message": f"GTIN {gtin} markerad som ej godkänd"})
    return jsonify({"success": False, "message": "GTIN hittades inte"}), 404

# Add this route after app initialization and before other routes
@app.route('/')
def index():
    monitor.check_all_folders()
    folders = []
    for gtin, folder_data in monitor.folder_status.items():
        folders.append(folder_data)
    return render_template('status.html', 
                         folders=folders, 
                         base_path=monitor.base_path)

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=check_and_delete_expired_folders, daemon=True)
    cleanup_thread.start()
    
    # Use environment variable to determine debug mode
    is_production = os.getenv('FLASK_ENV') == 'production'
    app.run(
        host='0.0.0.0',  # Viktigt för att lyssna på alla interfaces i Docker
        port=5001,       # Behåll 5000 som intern port
        debug=not is_production
    )