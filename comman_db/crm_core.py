import mysql.connector
from mysql.connector import Error
from datetime import datetime
from calendar import monthrange
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List, Dict, Optional, Any
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Load project-level environment once, regardless of current working directory.
load_dotenv(PROJECT_ROOT / ".env", override=False)

# =========================================================
# MySQL CONFIGURATION
# =========================================================
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB") or os.getenv("DB_NAME", ""),
    "port": int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306")),
}
# =========================================================
# HELPER FUNCTIONS
# =========================================================


def get_db_connection():
    '''Establish and return a new database connection.'''
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")

def fetchall_dict(cursor) -> List[Dict]:
    """Convert MySQL cursor results to list of dictionaries."""
    columns = cursor.column_names
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# SQL fragments used across modules
LEAD_PAYMENT_SELECT = """
    COALESCE(p.total_amount, 0) AS total_fee,
    COALESCE(p.govt_amount, 0) AS govt_fee,
    COALESCE(p.professional_amount, 0) AS professional_fee,
    COALESCE(p.govt_amount, 0) + COALESCE(p.professional_amount, 0) AS paid_amount,
    GREATEST(COALESCE(p.total_amount, 0) - (COALESCE(p.govt_amount, 0) + COALESCE(p.professional_amount, 0)), 0) AS pending_amount
"""

LEAD_PENDING_DEPARTMENT_SELECT = """
    CASE
        WHEN l.status = 'New' THEN 'Marketing'
        WHEN l.status = 'Assigned to Operations' THEN 'Operations'
        WHEN l.status = 'Ready for Accounts' THEN 'Accounts'
        WHEN l.status = 'Assigned to Accounts' THEN 'Accounts'
        WHEN l.status = 'Pending' AND p.lead_id IS NOT NULL THEN 'Accounts'
        WHEN l.status = 'Pending' AND o.lead_id IS NOT NULL THEN 'Operations'
        WHEN l.status = 'Failed' AND p.lead_id IS NOT NULL THEN 'Accounts'
        WHEN l.status = 'Failed' AND o.lead_id IS NOT NULL THEN 'Operations'
        WHEN l.status = 'Completed' THEN 'Accounts'
        ELSE 'Marketing'
    END AS pending_department
"""

LATEST_OPERATION_REMARK_SELECT = """
    (
        SELECT r.remark
        FROM operation_remarks r
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark
"""

LATEST_OPERATION_REMARK_AT_SELECT = """
    (
        SELECT r.created_at
        FROM operation_remarks r
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark_created_at
"""

LATEST_OPERATION_REMARK_BY_SELECT = """
    (
        SELECT e.name
        FROM operation_remarks r
        LEFT JOIN employees e ON e.id = r.employee_id
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark_by_name
"""

def _normalize_status_text(value):
    return (value or "").strip().lower()

def _normalize_payment_status(value):
    status = _normalize_status_text(value)
    if status in {"received", "done", "paid"}:
        return "Paid"
    if status == "failed":
        return "Failed"
    return "Pending"

def _matches_any(value, options):
    normalized = _normalize_status_text(value)
    return normalized in {_normalize_status_text(option) for option in options}

def _parse_datetime_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

def _format_datetime_display(value):
    parsed = _parse_datetime_value(value)
    if not parsed:
        return ""
    return parsed.strftime("%d %b %Y %I:%M %p")

def _build_workflow_fields(row):
    lead_status = _normalize_status_text(row.get("status"))
    file_status = _normalize_status_text(row.get("file_status"))
    pending_department = row.get("pending_department") or "Marketing"
    account_remark = row.get("account_remark") or ""

    certificate_done = _matches_any(
        account_remark,
        {"certificate done", "certificate received", "certificate downloaded"},
    )
    professional_fee_pending = _matches_any(
        account_remark,
        {"professional fee pending"},
    )
    government_fee_pending = _matches_any(
        account_remark,
        {"government fee pending", "gov fee pending"},
    )

    govt_status_label = _normalize_payment_status(row.get("govt_payment_status"))
    prof_status_label = _normalize_payment_status(row.get("professional_payment_status"))

    if certificate_done:
        workflow_status = "Certificate Done"
        certificate_status = "Done"
    elif professional_fee_pending or (
        govt_status_label == "Paid" and prof_status_label == "Pending"
    ):
        workflow_status = "Professional Fee Pending"
        certificate_status = "Pending"
    elif government_fee_pending or govt_status_label == "Pending":
        workflow_status = "Government Fee Pending"
        certificate_status = "Pending"
    elif lead_status == "pending":
        workflow_status = f"Pending at {pending_department}"
        certificate_status = "Pending"
    elif lead_status == "completed":
        workflow_status = "Completed"
        certificate_status = "Done"
    elif file_status == "failed" or lead_status == "failed":
        workflow_status = "Failed"
        certificate_status = "Pending"
    elif file_status == "done":
        workflow_status = "Ready for Accounts"
        certificate_status = "Pending"
    elif file_status == "pending":
        workflow_status = "Pending at Operations"
        certificate_status = "Pending"
    elif lead_status == "assigned to accounts":
        workflow_status = "Pending at Accounts"
        certificate_status = "Pending"
    elif lead_status == "assigned to operations":
        workflow_status = "Pending at Operations"
        certificate_status = "Pending"
    else:
        workflow_status = row.get("status") or "Pending at Marketing"
        certificate_status = "Pending"

    if workflow_status.startswith("Pending at "):
        pending_label = workflow_status
    elif lead_status == "new":
        pending_label = "Pending at Marketing"
    else:
        pending_label = f"Pending at {pending_department}" if lead_status == "pending" else ""

    if workflow_status in {"Certificate Done", "Professional Fee Pending", "Government Fee Pending"}:
        department_remark = row.get("account_remark") or row.get("operation_remark") or ""
    elif pending_department == "Operations":
        department_remark = row.get("operation_remark") or row.get("account_remark") or ""
    elif pending_department == "Accounts":
        department_remark = row.get("account_remark") or row.get("operation_remark") or ""
    else:
        department_remark = row.get("operation_remark") or row.get("account_remark") or ""

    payment_status_label = "Pending"
    if govt_status_label == "Failed" or prof_status_label == "Failed":
        payment_status_label = "Failed"
    elif govt_status_label == "Paid" and prof_status_label == "Paid":
        payment_status_label = "Paid"
    elif govt_status_label == "Paid" or prof_status_label == "Paid":
        payment_status_label = "Partial"

    return {
        "govt_fee_status_label": govt_status_label,
        "professional_fee_status_label": prof_status_label,
        "workflow_status_label": workflow_status,
        "pending_label": pending_label,
        "certificate_status": certificate_status,
        "department_remark": department_remark,
        "payment_status_label": payment_status_label,
    }

def _build_last_updated_fields(row):
    candidates = [
        (
            _parse_datetime_value(row.get("payment_updated_at")),
            row.get("payment_updated_by_name") or row.get("account_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("operation_updated_at")),
            row.get("operation_updated_by_name") or row.get("operation_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("operation_remark_created_at")),
            row.get("operation_remark_by_name") or row.get("operation_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("payment_date")),
            row.get("payment_updated_by_name") or row.get("account_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("created_at")),
            row.get("marketing_executive_name"),
        ),
    ]

    latest_timestamp = None
    latest_name = ""

    for timestamp, name in candidates:
        if not timestamp:
            continue
        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_name = name or ""

    return {
        "last_updated_by_name": latest_name,
        "last_updated_at": latest_timestamp,
        "last_updated_at_display": _format_datetime_display(latest_timestamp),
    }

def enrich_lead_row(row):
    enriched = dict(row)
    enriched.update(_build_workflow_fields(enriched))
    enriched.update(_build_last_updated_fields(enriched))
    return enriched

def enrich_lead_rows(rows):
    return [enrich_lead_row(row) for row in rows]

# print("DB_HOST =", os.getenv("DB_HOST"))
# print("DB_USER =", os.getenv("DB_USER"))
# print("DB_PASSWORD =", os.getenv("DB_PASSWORD"))
# print("DB_NAME =", os.getenv("DB_NAME"))
