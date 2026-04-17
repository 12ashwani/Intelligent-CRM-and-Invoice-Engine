import os
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("CRM_DB_HOST", "localhost"),
        user=os.environ.get("CRM_DB_USER", "root"),
        password=os.environ.get("CRM_DB_PASSWORD", "Dayachand@7037"),
        database=os.environ.get("CRM_DB_NAME", "crm_db")
    )