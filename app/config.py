import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'fitbuddy.db'}")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
WORKOUT_MODEL = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-2.5-pro")
TIP_MODEL = os.getenv("GEMINI_TIP_MODEL", "gemini-2.5-flash")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "coach")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
APP_ENV = os.getenv("APP_ENV", "development")
