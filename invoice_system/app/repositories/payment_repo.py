from app import mysql

class PaymentRepo:

    def save(self, data):
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO invoice_payments (invoice_id, amount, status)
            VALUES (%s,%s,%s)
        """, (data["invoice_id"], data["amount"], data["status"]))
        mysql.connection.commit()
