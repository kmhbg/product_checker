import requests
from datetime import datetime, timedelta

class GS1TradeItem:
    def __init__(self, client_id, client_secret, username, password):
        self.base_url = "https://validoopwe-apimanagement.azure-api.net/tradeitem"
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

    def get_token(self):
        """Get initial access token"""
        url = "https://validoopwe-apimanagement.azure-api.net/connect/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'tradeitem.api offline_access',
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
        url = "https://validoopwe-apimanagement.azure-api.net/connect/token"
        
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

    def get_item_by_gtin(self, gtin, information_provider_gln, target_market="752"):
        """Get trade item information by GTIN"""
        if not self.ensure_valid_token():
            raise Exception("Failed to obtain valid token")

        url = f"{self.base_url}/tradeitem.api/TradeItemInformation/getItemByIdentification"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        params = {
            'gtin': gtin,
            'informationProviderGln': information_provider_gln,
            'targetMarket': target_market,
            'cinFormat': 'XML',
            'dataType': 'Product',
            'includeDiscontinued': True,
            'includeWithdrawn': True
        }

        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get trade item information: {response.text}")

    def verify_gtins(self, gtins):
        """Verify multiple GTINs"""
        if not self.ensure_valid_token():
            raise Exception("Failed to obtain valid token")

        url = f"{self.base_url}/tradeitem.api/activate/gtins/verified"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.post(url, headers=headers, json=gtins)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to verify GTINs: {response.text}")

    def search_trade_items(self, search_params):
        """Search for trade items with various parameters"""
        if not self.ensure_valid_token():
            raise Exception("Failed to obtain valid token")

        url = f"{self.base_url}/tradeitem.api/TradeItemInformation/search"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.post(url, headers=headers, json=search_params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to search trade items: {response.text}")