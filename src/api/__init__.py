import requests
import json
import os

API_TOKEN=os.getenv("API_TOKEN")
X_TIMEZONE_OFFSET=int(os.getenv("X_TIMEZONE_OFFSET")) # GMT+8
BASE_URL=os.getenv("BASE_URL")

class BaseAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {API_TOKEN}",
            "X-Timezone-Offset": str(X_TIMEZONE_OFFSET),
            "Content-Type": "application/json",
        })
        self.base_url = BASE_URL
        
    def request_data(self, url: str, method: str = "GET", data: dict = None):
        if method == "GET":
            response = self.session.get(url, params=data)
        elif method == "POST":
            response = self.session.post(url, data=json.dumps(data))
        else:
            raise ValueError(f"Unsupported method: {method}")
        return response.json()
    