from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from MySQLdb.cursors import DictCursor

from app import mysql
from app.services.invoice_service import InvoiceService
from app.repositories.customer_repo import CustomerRepo
from app.utils.pdf_generator import generate_invoice_pdf

invoice_bp = Blueprint("invoice", __name__)
service = InvoiceService()
customer_repo = CustomerRepo()
# ========================================
# Invoice routes and logic
# ========================================
def get_cursor(cursor_class=None):
    """ Helper to get a MySQL cursor, optionally as a DictCursor. Returns a tuple of (cursor, is_dict). """
    try:
        if cursor_class:
            return mysql.connection.cursor(cursor_class), True
        return mysql.connection.cursor(), False
    except TypeError:
        return mysql.connection.cursor(), False

# =================================
# Helper functions
# ================================
def fetchall_dict(cur):
    """ Helper to convert cursor results to list of dicts."""
    columns = [col[0] for col in cur.description] if cur.description else []
    return [dict(zip(columns, row)) for row in cur.fetchall()]

# ================================
# Invoice UI routes
# ================================

def fetchone_dict(cur):
    """ Helper to convert a single cursor result to a dict."""
    row = cur.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cur.description]
    return dict(zip(columns, row))


def get_company_settings():
    cur, use_dict = get_cursor(DictCursor)
    cur.execute("SELECT * FROM company_settings LIMIT 1")
    return cur.fetchone() if use_dict else fetchone_dict(cur)

# ================================
# Invoice UI routes
# ================================
@invoice_bp.route("/ui")
def invoice_ui():
    """ Main invoice listing page. Fetches all invoices and company details for display."""
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM invoices ORDER BY id DESC")
    invoices = cur.fetchall()

    company = get_company_settings()
    
    return render_template("invoices/list.html", invoices=invoices, company=company)

# ================================
# Invoice creation UI
# ================================
@invoice_bp.route("/create-ui", methods=["GET", "POST"])
def create_invoice_ui():
    """ UI for creating a new invoice. On GET, shows form with customers and CRM leads. On POST, validates input and creates invoice."""
    company = get_company_settings()
    if not company:
        flash("Please complete company setup before creating invoices.", "warning")
        return redirect(url_for("company.company_settings"))

    cur, use_dict = get_cursor(DictCursor)
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall() if use_dict else fetchall_dict(cur)
    cur.execute(
        """
        SELECT
            id,
            company_name,
            email,
            auth_person_name,
            auth_person_number,
            auth_person_email,
            service,
            status
        FROM leads
        ORDER BY id DESC
        """
    )
    crm_leads = cur.fetchall() if use_dict else fetchall_dict(cur)
    selected_lead_id = request.args.get("lead_id", type=int)
    selected_lead = next((lead for lead in crm_leads if lead["id"] == selected_lead_id), None)

    if request.method == "POST":
        names = request.form.getlist("name[]")
        qtys = request.form.getlist("qty[]")
        prices = request.form.getlist("price[]")

        items = []
        for i in range(len(names)):
            item_name = (names[i] or "").strip()
            qty_raw = (qtys[i] or "").strip()
            price_raw = (prices[i] or "").strip()

            if not item_name and not qty_raw and not price_raw:
                continue

            if not item_name or not qty_raw or not price_raw:
                flash("Each invoice item must include a name, quantity, and price.", "warning")
                return render_template(
                    "invoices/create.html",
                    customers=customers,
                    crm_leads=crm_leads,
                    selected_lead=selected_lead,
                    company_state=company.get("state", ""),
                )

            try:
                qty = int(qty_raw)
                price = float(price_raw)
            except ValueError:
                flash("Please enter valid numeric values for quantity and price.", "warning")
                return render_template(
                    "invoices/create.html",
                    customers=customers,
                    crm_leads=crm_leads,
                    selected_lead=selected_lead,
                    company_state=company.get("state", ""),
                )

            items.append({
                "name": item_name,
                "qty": qty,
                "price": price,
            })

        if not items:
            flash("Add at least one invoice item.", "warning")
            return render_template(
                "invoices/create.html",
                customers=customers,
                crm_leads=crm_leads,
                selected_lead=selected_lead,
                company_state=company.get("state", ""),
            )

        customer_id = request.form.get("customer_id", type=int)

        if not customer_id:
            customer_name = (request.form.get("customer_name") or "").strip()
            customer_email = (request.form.get("customer_email") or "").strip()
            customer_contact = (request.form.get("customer_contact") or "").strip()
            customer_gstin = (request.form.get("customer_gstin") or "").strip()
            customer_address = (request.form.get("customer_address") or "").strip()
            customer_state = (request.form.get("customer_state") or "").strip()

            if not customer_name:
                flash("Customer name is required.", "warning")
                return render_template(
                    "invoices/create.html",
                    customers=customers,
                    crm_leads=crm_leads,
                    selected_lead=selected_lead,
                    company_state=company.get("state", ""),
                )

            if not customer_state:
                flash("Customer state is required.", "warning")
                return render_template(
                    "invoices/create.html",
                    customers=customers,
                    crm_leads=crm_leads,
                    selected_lead=selected_lead,
                    company_state=company.get("state", ""),
                )

            existing_customer = customer_repo.find_by_name_email(customer_name, customer_email or None)
            if existing_customer:
                customer_id = existing_customer["id"]
            else:
                customer_id = customer_repo.create_and_return_id(
                    {
                        "name": customer_name,
                        "email": customer_email,
                        "gstin": customer_gstin,
                        "address": customer_address,
                        "contact": customer_contact,
                        "state": customer_state,
                    }
                )

        invoice_type = (request.form.get("invoice_type") or "").strip().upper()
        if invoice_type not in ("PI", "TAX"):
            flash("Please select a valid invoice type.", "warning")
            return render_template(
                "invoices/create.html",
                customers=customers,
                crm_leads=crm_leads,
                selected_lead=selected_lead,
                company_state=company.get("state", ""),
            )

        data = {
            "customer_id": customer_id,
            "invoice_type": invoice_type,
            "items": items,
            "po_number": request.form.get("po_number", "").strip(),
            "place_of_supply": request.form.get("place_of_supply", "").strip(),
            "payment_terms": request.form.get("payment_terms", "").strip(),
            "due_date": request.form.get("due_date", "").strip(),
            "hsn_code": request.form.get("hsn_code", "").strip(),
        }

        try:
            service.create_invoice(data)
        except ValueError as ex:
            flash(str(ex), "danger")
            return render_template(
                "invoices/create.html",
                customers=customers,
                crm_leads=crm_leads,
                selected_lead=selected_lead,
                company_state=company.get("state", ""),
            )
        except Exception as ex:
            flash("Unable to create invoice. " + str(ex), "danger")
            return render_template(
                "invoices/create.html",
                customers=customers,
                crm_leads=crm_leads,
                selected_lead=selected_lead,
                company_state=company.get("state", ""),
            )

        return redirect(url_for("invoice.invoice_ui"))

    return render_template(
        "invoices/create.html",
        customers=customers,
        crm_leads=crm_leads,
        selected_lead=selected_lead,
        company_state=company.get("state", ""),
    )

# ================================
# Additional invoice-related routes (e.g. dashboard, PDF download)
# ================================
@invoice_bp.route("/dashboard")
def dashboard():
    """ Example dashboard route that aggregates data for display."""
    data = service.get_dashboard_data()
    return render_template("dashboard.html", data=data)
# ================================
# Additional invoice-related routes (e.g. dashboard, PDF download)
# ================================
@invoice_bp.route("/<int:invoice_id>/view")
def view_invoice(invoice_id):
    """ Route to view an invoice in HTML format in the browser."""
    details = service.get_invoice_details(invoice_id)
    if not details:
        flash("Invoice not found.", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    invoice, customer, items = details

    # Get company details
    if not mysql.connection:
        flash("Database connection not available.", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    company = get_company_settings()
    if not company:
        flash("Please complete company setup before viewing invoices.", "warning")
        return redirect(url_for("company.company_settings"))

    # Normalize data for template
    from app.utils.pdf_generator import _normalize_invoice, _normalize_customer, _normalize_items, _normalize_company
    invoice_data = _normalize_invoice(invoice)
    customer_data = _normalize_customer(customer)
    items_data = _normalize_items(items)
    company_data = _normalize_company(company)

    return render_template("invoices/tax.html", 
                         invoice=invoice_data, 
                         customer=customer_data, 
                         items=items_data, 
                         company=company_data)

@invoice_bp.route("/<int:invoice_id>/pdf")
def download_invoice(invoice_id):
    """ Route to download the PDF version of an invoice. Fetches invoice details and company info, generates PDF, and sends it as a file download."""
    details = service.get_invoice_details(invoice_id)
    if not details:
        flash("Invoice not found.", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    invoice, customer, items = details

    # Get company details
    if not mysql.connection:
        flash("Database connection not available.", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    company = get_company_settings()
    if not company:
        flash("Please complete company setup before downloading invoices.", "warning")
        return redirect(url_for("company.company_settings"))

    try:
        file_path = generate_invoice_pdf(invoice, customer, items, company)
    except Exception as ex:
        flash(f"Unable to generate invoice PDF: {ex}", "danger")
        return redirect(url_for("invoice.invoice_ui"))

    return send_file(file_path, as_attachment=True, download_name=f"{invoice[1]}.pdf")

@invoice_bp.route("/<int:invoice_id>/delete", methods=["POST"])
def delete_invoice(invoice_id):
    """ Route to delete an invoice and its associated items."""
    try:
        from app.repositories.invoice_repo import InvoiceRepo
        invoice_repo = InvoiceRepo()
        invoice_repo.delete(invoice_id)
        flash("Invoice deleted successfully.", "success")
    except Exception as ex:
        flash(f"Unable to delete invoice: {ex}", "danger")
    
    return redirect(url_for("invoice.invoice_ui"))
