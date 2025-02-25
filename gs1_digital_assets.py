import requests
import base64
import json
from datetime import datetime, timedelta
import os

class GS1DigitalAssets:
    def __init__(self, client_id, client_secret, username, password):
        self.base_url = "https://validoopwe-apimanagement.azure-api.net"
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

    def get_token(self):
        """Get initial access token"""
        url = f"{self.base_url}/connect/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'digitalassets.api offline_access',
            'username': self.username,
            'password': self.password
        }

        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'])
            return True
        return False

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        url = f"{self.base_url}/connect/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }

        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'])
            return True
        return False

    def ensure_valid_token(self):
        """Ensure we have a valid token"""
        if not self.access_token or not self.token_expires:
            return self.get_token()
        
        if datetime.now() >= self.token_expires - timedelta(minutes=5):
            return self.refresh_access_token()
        
        return True

    def upload_image(self, image_path, information_provider_gln, target_market_country_code):
        """Upload an image to GS1 Digital Assets"""
        if not self.ensure_valid_token():
            raise Exception("Failed to obtain valid token")

        url = f"{self.base_url}/digitalassets/digitalassets.api/AssetsApi"
        
        # Read and encode the image
        with open(image_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        # Prepare the request payload
        payload = {
            "FileName": os.path.basename(image_path),
            "InformationProviderGln": information_provider_gln,
            "TargetMarketCountryCode": target_market_country_code,
            "Asset": encoded_image,
            "AssetCategory": "productImage",
            "FieldofApplication": "Marketing",
            "AutoPublication": True,
            "NewDesign": False,
            "Tags": ["ecommerce"]
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Upload failed with status code {response.status_code}: {response.text}")

    def get_asset_status(self, asset_id):
        """Get the status of an uploaded asset"""
        if not self.ensure_valid_token():
            raise Exception("Failed to obtain valid token")

        url = f"{self.base_url}/digitalassets/digitalassets.api/AssetsApi/digitalAssets"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        params = {
            'digitalAssetId': asset_id
        }

        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get asset status: {response.text}")