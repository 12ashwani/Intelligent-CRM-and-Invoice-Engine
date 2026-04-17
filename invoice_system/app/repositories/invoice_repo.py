from app import mysql

class InvoiceRepo:

    def save(self, invoice, items):
        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO invoices (invoice_number, invoice_type, customer_id, subtotal, tax_amount, cgst, sgst, igst, total, po_number, place_of_supply, payment_terms, due_date, total_in_words)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            invoice["invoice_number"],
            invoice["invoice_type"],
            invoice["customer_id"],
            invoice["subtotal"],
            invoice["tax"],
            invoice["cgst"],
            invoice["sgst"],
            invoice["igst"],
            invoice["total"],
            invoice.get("po_number", ""),
            invoice.get("place_of_supply", ""),
            invoice.get("payment_terms", "Net 30 days"),
            invoice.get("due_date", None),
            invoice.get("total_in_words", "")
        ))

        invoice_id = cur.lastrowid

        for item in items:
            cur.execute("""
                INSERT INTO invoice_items (invoice_id, name, qty, price, hsn)
                VALUES (%s,%s,%s,%s,%s)
            """, (invoice_id, item["name"], item["qty"], item["price"], item.get("hsn", "998314")))

        mysql.connection.commit()

        return {"invoice_id": invoice_id, "invoice_number": invoice["invoice_number"]}

    def get_all(self):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM invoices")
        return cur.fetchall()

    def get_full_invoice(self, invoice_id):
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM invoices WHERE id=%s", (invoice_id,))
        invoice = cur.fetchone()
        if not invoice:
            return None

        cur.execute("SELECT * FROM customers WHERE id=%s", (invoice[3],))
        customer = cur.fetchone()

        cur.execute("SELECT * FROM invoice_items WHERE invoice_id=%s", (invoice_id,))
        items = cur.fetchall()

        return invoice, customer, items

    def delete(self, invoice_id):
        cur = mysql.connection.cursor()
        # Delete invoice items first (foreign key constraint)
        cur.execute("DELETE FROM invoice_items WHERE invoice_id=%s", (invoice_id,))
        # Then delete the invoice
        cur.execute("DELETE FROM invoices WHERE id=%s", (invoice_id,))
        mysql.connection.commit()
        cur.close()

    def get_dashboard_stats(self):
        cur = mysql.connection.cursor()

        # Total Revenue
        cur.execute("SELECT SUM(total) FROM invoices")
        total_revenue = cur.fetchone()[0] or 0

        # Total Invoices
        cur.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cur.fetchone()[0]

        # Paid Amount
        cur.execute("SELECT SUM(amount) FROM invoice_payments WHERE status='paid'")
        paid = cur.fetchone()[0] or 0

    # Pending
        pending = total_revenue - paid

        return {
            "total_revenue": float(total_revenue),
        "total_invoices": total_invoices,
        "paid": float(paid),
        "pending": float(pending)
    }

    def get_monthly_sales(self):
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT MONTH(created_at), SUM(total)
            FROM invoices
            GROUP BY MONTH(created_at)
            ORDER BY MONTH(created_at)
        """)

        return cur.fetchall()
    def get_invoice_types(self):
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT invoice_type, COUNT(*)
            FROM invoices
            GROUP BY invoice_type
        """)

        return cur.fetchall()
