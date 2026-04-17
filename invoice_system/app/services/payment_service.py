from app.repositories.payment_repo import PaymentRepo
from app import mysql

class PaymentService:

    def __init__(self):
        self.repo = PaymentRepo()

    def add_payment(self, data):
        invoice_id = data["invoice_id"]
        amount = data["amount"]

        cur = mysql.connection.cursor()

        # Get invoice total
        cur.execute("SELECT total FROM invoices WHERE id=%s", (invoice_id,))
        total = cur.fetchone()[0]

        # Get total paid so far
        cur.execute("SELECT SUM(amount) FROM invoice_payments WHERE invoice_id=%s", (invoice_id,))
        paid = cur.fetchone()[0] or 0

        new_paid = paid + amount

        # Determine status
        if new_paid >= total:
            status = "paid"
        elif new_paid > 0:
            status = "partial"
        else:
            status = "unpaid"

        # Save payment
        self.repo.save({
            "invoice_id": invoice_id,
            "amount": amount,
            "status": status
        })

        # Update invoice status
        cur.execute("UPDATE invoices SET status=%s WHERE id=%s", (status, invoice_id))
        mysql.connection.commit()

        return {"message": "Payment added", "status": status}
