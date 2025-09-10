import requests
import json

USER="pengtb"
API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyVG9rZW5JZCI6IjIxMDcwODI4NDU4MTM4NzI0MDEiLCJqdGkiOiIzNzcyNzE3NzEzMzgyNzAzMTA0IiwidXNlcm5hbWUiOiJwZW5ndGIiLCJ0eXBlIjoxLCJpYXQiOjE3NTY4MDkzMDksImV4cCI6MTc1OTQwMTMwOX0.G1Ut8wXG__pPsy2hbBd0ttuPsQpuk2xnbpqYQst1ilw"
X_TIMEZONE_OFFSET=480 # GMT+8
BASE_URL="https://finance.konojojo.icu/api/v1"

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
            response = self.session.get(url)
        elif method == "POST":
            response = self.session.post(url, data=json.dumps(data))
        else:
            raise ValueError(f"Unsupported method: {method}")
        return response.json()
    