from typing import List, Dict, Optional
from datetime import datetime
from .crm_core import get_db_connection

# =========================================================
# INVOICE MANAGEMENT (GST invoices with HSN & tax tables)
# =========================================================

def generate_invoice_number(invoice_type: str) -> str:
    """Generate a sequential invoice number for the current year."""
    year = datetime.now().year
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO invoice_sequence (year, type, last_number)
        VALUES (%s, %s, 1)
        ON DUPLICATE KEY UPDATE last_number = last_number + 1
    """, (year, invoice_type))
    conn.commit()
    cur.execute("SELECT last_number FROM invoice_sequence WHERE year=%s AND type=%s", (year, invoice_type))
    seq = cur.fetchone()[0]
    cur.close()
    conn.close()
    return f"{invoice_type}/{year}/{seq:03d}"

def create_invoice(data: Dict) -> int:
    """Create a new invoice with items and tax lines."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        invoice_number = generate_invoice_number(data['invoice_type'])
        cur.execute("""
            INSERT INTO invoices (
                invoice_number, invoice_type, customer_id, company_id,
                date, due_date, po_number, order_number,
                payment_terms, transport_details, place_of_supply,
                subtotal, cgst_rate, sgst_rate, igst_rate,
                tax_total, round_off, total, total_in_words,
                tax_in_words, status, lead_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            invoice_number, data['invoice_type'], data.get('customer_id'), data.get('company_id'),
            data.get('date'), data.get('due_date'), data.get('po_number'), data.get('order_number'),
            data.get('payment_terms'), data.get('transport_details'), data.get('place_of_supply'),
            data.get('subtotal', 0), data.get('cgst_rate', 0), data.get('sgst_rate', 0), data.get('igst_rate', 0),
            data.get('tax_total', 0), data.get('round_off', 0), data.get('total', 0),
            data.get('total_in_words'), data.get('tax_in_words'), data.get('status', 'Pending'),
            data.get('lead_id')
        ))
        invoice_id = cur.lastrowid
        for item in data.get('items', []):
            cur.execute("""
                INSERT INTO invoice_items (
                    invoice_id, name, description, hsn, qty, unit, price, line_total
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                invoice_id, item['name'], item.get('description'), item.get('hsn'),
                item['qty'], item.get('unit'), item['price'], item.get('line_total', item['qty'] * item['price'])
            ))
        for tax in data.get('tax_lines', []):
            cur.execute("""
                INSERT INTO invoice_tax (
                    invoice_id, hsn, taxable_value, rate,
                    cgst_rate, cgst_amount, sgst_rate, sgst_amount,
                    igst_rate, igst_amount, amount
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                invoice_id, tax.get('hsn'), tax.get('taxable_value', 0), tax.get('rate', 0),
                tax.get('cgst_rate', 0), tax.get('cgst_amount', 0),
                tax.get('sgst_rate', 0), tax.get('sgst_amount', 0),
                tax.get('igst_rate', 0), tax.get('igst_amount', 0),
                tax.get('amount', 0)
            ))
        conn.commit()
        return invoice_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_invoice_by_id(invoice_id: int) -> Optional[Dict]:
    """Retrieve a full invoice with its items, tax lines, and related customer/company."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT i.*,
               c.name AS customer_name, c.gstin AS customer_gstin, c.address AS customer_address,
               c.phone AS customer_phone, c.email AS customer_email,
               comp.name AS company_name, comp.address AS company_address, comp.gstin AS company_gstin,
               comp.bank_name, comp.account_number, comp.ifsc_code, comp.upi_id
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        LEFT JOIN company comp ON i.company_id = comp.id
        WHERE i.id = %s
    """, (invoice_id,))
    invoice = cur.fetchone()
    if not invoice:
        cur.close()
        conn.close()
        return None
    cur.execute("SELECT * FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
    invoice['items'] = cur.fetchall()
    cur.execute("SELECT * FROM invoice_tax WHERE invoice_id = %s", (invoice_id,))
    invoice['tax_lines'] = cur.fetchall()
    cur.close()
    conn.close()
    return invoice

def get_all_invoices(filters: Dict = None) -> List[Dict]:
    """Return a list of invoices (without items/tax lines) with optional filters."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT i.id, i.invoice_number, i.invoice_type, i.date, i.due_date,
               i.status, i.total, c.name AS customer_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
    """
    conditions = []
    params = []
    if filters:
        if 'status' in filters:
            conditions.append("i.status = %s")
            params.append(filters['status'])
        if 'customer_id' in filters:
            conditions.append("i.customer_id = %s")
            params.append(filters['customer_id'])
        if 'invoice_type' in filters:
            conditions.append("i.invoice_type = %s")
            params.append(filters['invoice_type'])
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY i.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_invoice_status(invoice_id: int, status: str) -> None:
    """Update invoice status (Draft, Pending, Paid, Cancelled)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET status = %s WHERE id = %s", (status, invoice_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_invoice(invoice_id: int) -> None:
    """Delete an invoice and its related items/tax lines (cascade)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM invoices WHERE id = %s", (invoice_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_company_settings_for_invoice(company_id: int = 1) -> Optional[Dict]:
    """Fetch company details from the 'company' table (multi‑company ready)."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM company WHERE id = %s", (company_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_company_settings(company_id: int, data: Dict) -> None:
    """Update company details for invoice header/banking."""
    conn = get_db_connection()
    cur = conn.cursor()
    fields = []
    values = []
    for key, val in data.items():
        fields.append(f"{key}=%s")
        values.append(val)
    values.append(company_id)
    cur.execute(f"UPDATE company SET {', '.join(fields)} WHERE id=%s", values)
    conn.commit()
    cur.close()
    conn.close()

def add_invoice_payment(invoice_id: int, amount: float, payment_date: str = None, 
                        transaction_id: str = None, remarks: str = None) -> int:
    """Record a payment against an invoice."""
    conn = get_db_connection()
    cur = conn.cursor()
    payment_date = payment_date or datetime.now().strftime('%Y-%m-%d')
    cur.execute("""
        INSERT INTO invoice_payments (invoice_id, amount, payment_date, transaction_id, remarks)
        VALUES (%s, %s, %s, %s, %s)
    """, (invoice_id, amount, payment_date, transaction_id, remarks))
    invoice_payment_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return invoice_payment_id

def get_invoice_payments(invoice_id: int) -> List[Dict]:
    """Get all payments for an invoice."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM invoice_payments WHERE invoice_id = %s ORDER BY payment_date DESC", (invoice_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows