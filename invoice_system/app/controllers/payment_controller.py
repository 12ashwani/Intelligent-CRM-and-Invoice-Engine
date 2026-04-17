from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from app.services.payment_service import PaymentService
from app import mysql

payment_bp = Blueprint("payment", __name__)
service = PaymentService()

@payment_bp.route("/", methods=["POST"])
def add_payment():
    data = request.json
    return jsonify(service.add_payment(data))


@payment_bp.route("/pay/<int:invoice_id>", methods=["GET", "POST"])
def pay_invoice(invoice_id):

    cur = mysql.connection.cursor()

    # Get invoice
    cur.execute("SELECT * FROM invoices WHERE id=%s", (invoice_id,))
    invoice = cur.fetchone()

    if not invoice:
        flash("Invoice not found.", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    # Get payment history
    cur.execute("SELECT * FROM invoice_payments WHERE invoice_id=%s", (invoice_id,))
    payments = cur.fetchall()

    if request.method == "POST":
        amount = float(request.form["amount"])

        service.add_payment({
            "invoice_id": invoice_id,
            "amount": amount
        })

        flash("Payment added successfully.", "success")
        return redirect(url_for("payment.pay_invoice", invoice_id=invoice_id))

    return render_template(
        "payments/pay.html",
        invoice=invoice,
        payments=payments
    )
