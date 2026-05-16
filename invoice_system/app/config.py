import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)

class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    # =====================================================
    # MYSQL CONFIG
    # =====================================================

    MYSQL_HOST = os.getenv("DB_HOST", "localhost")
    MYSQL_USER = os.getenv("Db_USER", "root")
    MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "crm_db1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

    # =====================================================
    # APP CONFIG
    # =====================================================

    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "5001"))

    # =====================================================
    # CRM / SECURITY
    # =====================================================

    CRM_URL = os.getenv(
        "CRM_URL",
        "http://localhost:5000"
    )

    ACCESS_TTL_SECONDS = int(
        os.getenv("INVOICE_ACCESS_TTL_SECONDS", "3600")
    )

    INVOICE_ACCESS_SECRET = os.getenv(
        "INVOICE_ACCESS_SECRET",
        "invoice-access-secret"
    )