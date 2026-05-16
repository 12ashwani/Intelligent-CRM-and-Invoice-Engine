from datetime import datetime
from typing import List, Dict, Optional
from .crm_core import get_db_connection, enrich_lead_rows
from .crm_employees import get_employees_by_department

# =========================================================
# ACCOUNTS & PAYMENTS
# =========================================================

def assign_to_accounts(lead_id: int, account_executive_id: int):
    """⚠️ DEPRECATED - Use assign_to_accounts_from_operations() instead."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO payments (lead_id, account_executive)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE account_executive=VALUES(account_executive)
    """, (lead_id, account_executive_id))
    cur.execute("""UPDATE leads SET status='Assigned to Accounts' WHERE id=%s""", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()

def assign_to_accounts_from_operations(lead_id: int, account_executive_id: int):
    """✅ CORRECT WORKFLOW - Operations assigns to Accounts after completing work."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT status FROM leads WHERE id=%s", (lead_id,))
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        raise ValueError(f"Lead {lead_id} not found")
    (current_status,) = result
    if current_status != 'Ready for Accounts':
        cur.close()
        conn.close()
        raise ValueError(f"Lead must be in 'Ready for Accounts' status. Current status: {current_status}")
    cur.execute("""
        INSERT INTO payments (lead_id, account_executive)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE account_executive=VALUES(account_executive)
    """, (lead_id, account_executive_id))
    cur.execute("""UPDATE leads SET status='Assigned to Accounts' WHERE id=%s""", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_payment(
        lead_id: int,
        govt_amount: float,
        professional_amount: float,
        govt_status: str = 'done',
        prof_status: str = 'done'):
    """Update payment status and finalize the lead."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE payments
        SET govt_payment_status=%s,
            professional_payment_status=%s,
            govt_amount=%s,
            professional_amount=%s,
            payment_date=%s
        WHERE lead_id=%s
    """, (govt_status, prof_status, govt_amount, professional_amount, datetime.now().strftime('%Y-%m-%d'), lead_id))
    cur.execute("UPDATE leads SET status='Completed' WHERE id=%s", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_payment_status(
    lead_id,
    govt=None,
    prof=None,
    status=None,
    amount=None,
    remarks=None,
    total_amount=None,
    govt_amount=None,
    professional_amount=None,
    updated_by=None,
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payments (lead_id) VALUES (%s)
        ON DUPLICATE KEY UPDATE lead_id = lead_id
    """, (lead_id,))
    if govt:
        cursor.execute("UPDATE payments SET govt_payment_status=%s WHERE lead_id=%s", (govt, lead_id))
    if prof:
        cursor.execute("UPDATE payments SET professional_payment_status=%s WHERE lead_id=%s", (prof, lead_id))
    if status:
        cursor.execute("UPDATE payments SET govt_payment_status=%s, professional_payment_status=%s WHERE lead_id=%s", (status, status, lead_id))
    if amount:
        cursor.execute("UPDATE payments SET govt_amount=%s, professional_amount=%s WHERE lead_id=%s", (amount, amount, lead_id))
    if total_amount is not None:
        cursor.execute("UPDATE payments SET total_amount=%s WHERE lead_id=%s", (total_amount, lead_id))
    if govt_amount is not None:
        cursor.execute("UPDATE payments SET govt_amount=%s WHERE lead_id=%s", (govt_amount, lead_id))
    if professional_amount is not None:
        cursor.execute("UPDATE payments SET professional_amount=%s WHERE lead_id=%s", (professional_amount, lead_id))
    if remarks:
        cursor.execute("UPDATE payments SET remarks=%s, updated_by=COALESCE(%s, updated_by) WHERE lead_id=%s", (remarks, updated_by, lead_id))
    if updated_by is not None and not remarks and all(value is None for value in (amount, total_amount, govt_amount, professional_amount, govt, prof, status)):
        cursor.execute("UPDATE payments SET updated_by=%s WHERE lead_id=%s", (updated_by, lead_id))
    if any(value is not None for value in (amount, total_amount, govt_amount, professional_amount, govt, prof, status)):
        cursor.execute("UPDATE payments SET payment_date=%s, updated_by=COALESCE(%s, updated_by) WHERE lead_id=%s", (datetime.now().strftime('%Y-%m-%d'), updated_by, lead_id))
    cursor.execute("SELECT govt_payment_status, professional_payment_status, total_amount, govt_amount, professional_amount FROM payments WHERE lead_id=%s", (lead_id,))
    row = cursor.fetchone()
    govt_status, prof_status, saved_total_amount, saved_govt_amount, saved_prof_amount = row
    collected_total = float(saved_govt_amount or 0) + float(saved_prof_amount or 0)
    target_total = float(saved_total_amount or 0)
    if govt_status == "failed" or prof_status == "failed":
        final_status = "Failed"
    elif target_total > 0 and collected_total >= target_total:
        final_status = "Completed"
    else:
        final_status = "Pending"
    if final_status == "Completed":
        cursor.execute("UPDATE payments SET govt_payment_status=%s, professional_payment_status=%s WHERE lead_id=%s", ("received", "received", lead_id))
    elif final_status == "Pending" and govt_status != "failed" and prof_status != "failed":
        cursor.execute("UPDATE payments SET govt_payment_status=%s, professional_payment_status=%s WHERE lead_id=%s", ("received" if float(saved_govt_amount or 0) > 0 else "pending", "received" if float(saved_prof_amount or 0) > 0 else "pending", lead_id))
    cursor.execute("UPDATE leads SET status=%s WHERE id=%s", (final_status, lead_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_payment_by_lead_id(lead_id: int):
    """Get payment details for a lead."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM payments WHERE lead_id = %s", (lead_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_accounts_data():
    leads = get_leads_for_accounts()
    employees = get_employees_by_department("accounts")
    return leads, employees

def get_leads_for_accounts(employee_id=None):
    """Fetch leads assigned to Accounts team."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if employee_id:
        cur.execute("""
            SELECT l.*, 
                   p.govt_payment_status, p.professional_payment_status,
                   p.total_amount, p.govt_amount, p.professional_amount,
                   p.payment_date, p.remarks, p.remarks as account_remark,
                   p.account_executive, o.client_login, o.client_password,
                   o.file_status, o.filing_date, o.updated_at AS operation_updated_at,
                   p.updated_at AS payment_updated_at,
                   e.name as account_executive_name, m.name as marketing_executive_name,
                   op.name as operation_executive_name, opu.name AS operation_updated_by_name,
                   acu.name AS payment_updated_by_name,
                   (SELECT r.remark FROM operation_remarks r WHERE r.lead_id = l.id ORDER BY r.created_at DESC, r.id DESC LIMIT 1) AS operation_remark,
                   (SELECT r.created_at FROM operation_remarks r WHERE r.lead_id = l.id ORDER BY r.created_at DESC, r.id DESC LIMIT 1) AS operation_remark_created_at,
                   (SELECT e.name FROM operation_remarks r LEFT JOIN employees e ON e.id = r.employee_id WHERE r.lead_id = l.id ORDER BY r.created_at DESC, r.id DESC LIMIT 1) AS operation_remark_by_name
            FROM leads l
            LEFT JOIN payments p ON l.id = p.lead_id
            LEFT JOIN operations o ON l.id = o.lead_id
            LEFT JOIN employees e ON p.account_executive = e.id
            LEFT JOIN employees m ON l.marketing_executive = m.id
            LEFT JOIN employees op ON o.operation_executive = op.id
            LEFT JOIN employees opu ON o.updated_by = opu.id
            LEFT JOIN employees acu ON p.updated_by = acu.id
            WHERE p.account_executive=%s 
              AND l.status IN ('Assigned to Accounts', 'Pending', 'Completed', 'Failed')
            ORDER BY (l.status = 'Pending') DESC, l.created_at DESC
        """, (employee_id,))
    else:
        cur.execute("""
            SELECT l.*, p.govt_payment_status, p.professional_payment_status,
                   p.total_amount, p.govt_amount, p.professional_amount,
                   p.payment_date, p.remarks, p.remarks as account_remark,
                   p.account_executive, o.client_login, o.client_password,
                   o.file_status, o.filing_date, o.updated_at AS operation_updated_at,
                   p.updated_at AS payment_updated_at,
                   e.name as account_executive_name, m.name as marketing_executive_name,
                   op.name as operation_executive_name, opu.name AS operation_updated_by_name,
                   acu.name AS payment_updated_by_name
            FROM leads l
            LEFT JOIN payments p ON l.id = p.lead_id
            LEFT JOIN operations o ON l.id = o.lead_id
            LEFT JOIN employees e ON p.account_executive = e.id
            LEFT JOIN employees m ON l.marketing_executive = m.id
            LEFT JOIN employees op ON o.operation_executive = op.id
            LEFT JOIN employees opu ON o.updated_by = opu.id
            LEFT JOIN employees acu ON p.updated_by = acu.id
            WHERE l.status IN ('Assigned to Accounts', 'Pending', 'Completed', 'Failed')
            ORDER BY (l.status = 'Pending') DESC, l.created_at DESC
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return enrich_lead_rows(rows)