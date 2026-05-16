from typing import Optional
from datetime import datetime
from .crm_core import get_db_connection

# =========================================================
# OPERATIONS
# =========================================================

def assign_to_operations(lead_id: int, operation_executive_id: int):
    """Assign a lead to an operations executive."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO operations (lead_id, operation_executive)
        VALUES (%s, %s)
    """, (lead_id, operation_executive_id))
    cur.execute("UPDATE leads SET status='Assigned to Operations' WHERE id=%s", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_operation(
        lead_id: int,
        file_status: str = 'done',
        filing_date: Optional[str] = None,
        client_login: Optional[str] = None,
        client_password: Optional[str] = None,
        updated_by: Optional[int] = None):
    """Update operation details and keep the lead in the correct workflow stage."""
    conn = get_db_connection()
    cur = conn.cursor()
    normalized_status = (file_status or "done").strip().lower()
    if normalized_status == "done":
        lead_status = "Ready for Accounts"
        effective_filing_date = filing_date or datetime.now().strftime('%Y-%m-%d')
    elif normalized_status == "pending":
        lead_status = "Pending"
        effective_filing_date = filing_date
    elif normalized_status == "failed":
        lead_status = "Failed"
        effective_filing_date = filing_date
    else:
        lead_status = "Assigned to Operations"
        effective_filing_date = filing_date
    cur.execute('''
        UPDATE operations
        SET file_status=%s,
            filing_date=COALESCE(%s, filing_date),
            client_login=COALESCE(%s, client_login),
            client_password=COALESCE(%s, client_password),
            updated_by=COALESCE(%s, updated_by)
        WHERE lead_id=%s
    ''', (
        normalized_status,
        effective_filing_date,
        client_login,
        client_password,
        updated_by,
        lead_id
    ))
    cur.execute("""UPDATE leads SET status=%s WHERE id=%s""", (lead_status, lead_id))
    conn.commit()
    cur.close()
    conn.close()

def add_operation_remark(lead_id, employee_id, remark):
    """Add a remark for a lead in operations."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO operation_remarks (lead_id, employee_id, remark, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (lead_id, employee_id, remark))
    cur.execute("""
        UPDATE operations SET updated_by=%s WHERE lead_id=%s
    """, (employee_id, lead_id))
    conn.commit()
    cur.close()
    conn.close()

def get_operation_by_lead_id(lead_id: int):
    """Get operation details for a lead."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM operations WHERE lead_id = %s", (lead_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_operation_remarks(lead_id: int):
    """Get all operation remarks for a lead."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.*, e.name AS employee_name
        FROM operation_remarks r
        LEFT JOIN employees e ON e.id = r.employee_id
        WHERE r.lead_id = %s
        ORDER BY r.created_at DESC
    """, (lead_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows