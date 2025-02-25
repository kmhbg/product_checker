from flask import Flask, render_template, jsonify, request, redirect, url_for
from product_folder_monitor import ProductFolderMonitor, ProductFolderStatus
from gs1_digital_assets import GS1DigitalAssets
import shutil
import os
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__, template_folder='/Users/nille/Documents/Dev/GS1/templates')

# Add configuration storage
config = {
    'watch_folder': "/Users/nille/Documents/Dev/GS1/product_images"
}

# Initialize GS1 client with your credentials
gs1_client = GS1DigitalAssets(
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_username",
    password="your_password"
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
    if gtin in monitor.folder_status:
        status = ProductFolderStatus(f"{config['watch_folder']}/{gtin}")
        status.check_contents()
        status.approve()
        monitor.folder_status[gtin] = status.to_dict()
        monitor.save_status()
        return jsonify({"success": True, "message": f"GTIN {gtin} godkänd"})
    return jsonify({"success": False, "message": "GTIN hittades inte"}), 404

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
    return render_template('status.html', 
                         folders=monitor.folder_status,
                         current_folder=config['watch_folder'])

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=check_and_delete_expired_folders, daemon=True)
    cleanup_thread.start()
    app.run(debug=True)