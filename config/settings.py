import os

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://qa:qa@127.0.0.1:5432/shop")
BROWSER = os.getenv("BROWSER", "chrome")            # chrome | firefox
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "10"))

VALID_USER = {"username": "qa_user", "password": "Passw0rd!"}
