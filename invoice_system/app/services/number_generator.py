from datetime import datetime
from app import mysql

def generate_invoice_number(invoice_type):
    year = datetime.now().year
    prefix = "PI" if invoice_type == "PI" else "INV"

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT last_number FROM invoice_sequence
        WHERE year=%s AND type=%s FOR UPDATE
    """, (year, invoice_type))

    row = cur.fetchone()

    if row:
        new_number = row[0] + 1
        cur.execute("""
            UPDATE invoice_sequence
            SET last_number=%s
            WHERE year=%s AND type=%s
        """, (new_number, year, invoice_type))
    else:
        new_number = 1
        cur.execute("""
            INSERT INTO invoice_sequence (year, type, last_number)
            VALUES (%s, %s, %s)
        """, (year, invoice_type, new_number))

    mysql.connection.commit()

    return f"{prefix}-{year}-{str(new_number).zfill(4)}"