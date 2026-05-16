from typing import List, Dict, Optional
from datetime import datetime
from .crm_core import (
    get_db_connection, fetchall_dict, enrich_lead_rows,
    LATEST_OPERATION_REMARK_SELECT, LATEST_OPERATION_REMARK_AT_SELECT,
    LATEST_OPERATION_REMARK_BY_SELECT, LEAD_PENDING_DEPARTMENT_SELECT, LEAD_PAYMENT_SELECT
)

# =========================================================
# LEADS (MARKETING)
# =========================================================

def create_lead(marketing_exec_id: int, company_name: str, **kwargs) -> int:
    """Insert a new lead for a marketing executive."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO leads (
            marketing_executive, company_name, date, email,
            auth_person_name, auth_person_number, auth_person_email, service, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        marketing_exec_id,
        company_name,
        kwargs.get('date', datetime.now().strftime('%Y-%m-%d')),
        kwargs.get('email'),
        kwargs.get('auth_person_name'),
        kwargs.get('auth_person_number'),
        kwargs.get('auth_person_email'),
        kwargs.get('service'),
        kwargs.get('status', 'Marketing')
    ))
    lead_id = cur.lastrowid
    if lead_id is None:
        raise RuntimeError("Failed to create lead: could not retrieve lead_id")
    conn.commit()
    cur.close()
    conn.close()
    return lead_id

def get_all_leads() -> List[Dict]:
    """Get all leads with basic info."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return enrich_lead_rows(rows)

def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """Get a single lead by ID with all relations."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT l.*, 
               m.name AS marketing_executive_name,
               o.file_status, o.client_login, o.client_password, o.filing_date,
               o.operation_executive, op.name AS operation_executive_name,
               p.govt_payment_status, p.professional_payment_status,
               p.total_amount, p.govt_amount, p.professional_amount,
               p.payment_date, p.remarks AS account_remark,
               p.account_executive, acc.name AS account_executive_name,
               """ + LATEST_OPERATION_REMARK_SELECT + """,
               """ + LEAD_PENDING_DEPARTMENT_SELECT + """,
               """ + LEAD_PAYMENT_SELECT + """
        FROM leads l
        LEFT JOIN employees m ON l.marketing_executive = m.id
        LEFT JOIN operations o ON l.id = o.lead_id
        LEFT JOIN employees op ON o.operation_executive = op.id
        LEFT JOIN payments p ON l.id = p.lead_id
        LEFT JOIN employees acc ON p.account_executive = acc.id
        WHERE l.id = %s
    """, (lead_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return enrich_lead_row(row) if row else None

def update_lead_status(lead_id: int, status: str):
    """Update lead status."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE leads SET status=%s WHERE id=%s", (status, lead_id))
    conn.commit()
    cur.close()
    conn.close()

def get_scoped_lead(role: str, lead_id: int, employee_id: int):
    """Return a lead only if it belongs to the current role scope."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if role == "marketing":
        cur.execute(
            "SELECT id, status FROM leads WHERE id=%s AND marketing_executive=%s",
            (lead_id, employee_id),
        )
    elif role == "operations":
        cur.execute("""
            SELECT l.id, l.status
            FROM leads l
            JOIN operations o ON l.id = o.lead_id
            WHERE l.id=%s AND o.operation_executive=%s
        """, (lead_id, employee_id))
    elif role == "accounts":
        cur.execute("""
            SELECT l.id, l.status
            FROM leads l
            JOIN payments p ON l.id = p.lead_id
            WHERE l.id=%s AND p.account_executive=%s
        """, (lead_id, employee_id))
    else:
        cur.close()
        conn.close()
        return None
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def return_lead_to_previous_stage(lead_id: int):
    """Move a lead one step back in the workflow."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur2 = conn.cursor()
    try:
        cur.execute("SELECT id, status FROM leads WHERE id=%s", (lead_id,))
        lead = cur.fetchone()
        if not lead:
            raise ValueError("Lead not found.")
        status = lead["status"]
        if status == "Assigned to Operations":
            cur2.execute("DELETE FROM operation_remarks WHERE lead_id=%s", (lead_id,))
            cur2.execute("DELETE FROM operations WHERE lead_id=%s", (lead_id,))
            cur2.execute("UPDATE leads SET status='New' WHERE id=%s", (lead_id,))
        elif status == "Ready for Accounts":
            cur2.execute("UPDATE leads SET status='Assigned to Operations' WHERE id=%s", (lead_id,))
        elif status == "Assigned to Accounts":
            cur2.execute("UPDATE payments SET account_executive=NULL WHERE lead_id=%s", (lead_id,))
            cur2.execute("UPDATE leads SET status='Ready for Accounts' WHERE id=%s", (lead_id,))
        elif status in {"Pending", "Completed", "Failed"}:
            cur2.execute("UPDATE leads SET status='Assigned to Accounts' WHERE id=%s", (lead_id,))
        else:
            raise ValueError("This lead cannot be returned from its current status.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur2.close()
        cur.close()
        conn.close()