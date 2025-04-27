import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
# CSRF_KEY = os.getenv("CSRF_KEY")

# Инициализация templates
templates = Jinja2Templates(directory="app/templates")