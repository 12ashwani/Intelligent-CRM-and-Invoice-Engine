from flask import Blueprint, render_template, request, redirect
from app.repositories.customer_repo import CustomerRepo

customer_bp = Blueprint("customer", __name__)
repo = CustomerRepo()

@customer_bp.route("/ui", methods=["GET", "POST"])
def customer_ui():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "gstin": request.form["gstin"],
            "state": request.form["state"],
            "address": request.form.get("address", ""),
            "contact": request.form.get("contact", "")
        }
        repo.create(data)
        return redirect("/customers/ui")

    customers = repo.get_all()
    return render_template("customers/list.html", customers=customers)

@customer_bp.route("/delete/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):
    repo.delete(customer_id)
    return redirect("/customers/ui")
