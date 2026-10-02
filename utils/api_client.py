import requests
from config import settings


class ApiClient:
    def __init__(self, base_url=settings.BASE_URL):
        self.base = base_url
        self.session = requests.Session()
        self.token = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self, username, password):
        r = self.session.post(f"{self.base}/api/auth/login",
                              json={"username": username, "password": password}, timeout=10)
        if r.status_code == 200:
            self.token = r.json()["token"]
        return r

    def get(self, path, **kw):
        return self.session.get(f"{self.base}{path}", headers=self._headers(), timeout=10, **kw)

    def post(self, path, json=None, **kw):
        return self.session.post(f"{self.base}{path}", json=json, headers=self._headers(), timeout=10, **kw)
