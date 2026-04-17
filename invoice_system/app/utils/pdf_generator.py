import os
import tempfile
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from flask import render_template, current_app


def _pdfkit_configuration():
    if not PDFKIT_AVAILABLE:
        return None

    try:
        return pdfkit.configuration()
    except OSError:
        return None


def _resolve_image_path(image_path):
    """
    Convert relative image path to absolute file path for PDF processing.
    Handles URLs, relative paths, and direct file paths.
    Returns the path if it exists, otherwise returns the original path.
    """
    if not image_path:
        return None
    
    # If it's a URL (starts with http/https), return as-is for weasyprint/pdfkit
    if image_path.startswith(('http://', 'https://')):
        return image_path
    
    # Try to get the Flask app instance
    try:
        app_root = current_app.root_path if current_app else None
    except (RuntimeError, AttributeError):
        app_root = None
    
    # If it's a relative path like /static/..., convert to absolute file path
    if image_path.startswith('/'):
        if app_root:
            abs_path = os.path.join(app_root, image_path.lstrip('/'))
            if os.path.exists(abs_path):
                return f"file://{os.path.abspath(abs_path)}"
        return image_path
    
    # If it's already an absolute path, check if it exists
    if os.path.isabs(image_path):
        if os.path.exists(image_path):
            return f"file://{image_path}"
        return image_path
    
    # For relative paths without leading /, try from app root
    if app_root:
        abs_path = os.path.join(app_root, image_path)
        if os.path.exists(abs_path):
            return f"file://{os.path.abspath(abs_path)}"
    
    # Try to find the image in the static/uploads directory (for logo filenames)
    if app_root:
        uploads_path = os.path.join(app_root, "static", "uploads", image_path)
        if os.path.exists(uploads_path):
            return f"file://{os.path.abspath(uploads_path)}"
    
    return image_path


def _row_get(row, index, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(index, default)
    try:
        return row[index]
    except (IndexError, KeyError, TypeError):
        return default


def _to_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


def _format_money(value):
    return f"{_to_decimal(value):.2f}"


def _normalize_invoice(invoice):
    return {
        "id": _row_get(invoice, 0),
        "invoice_number": _row_get(invoice, 1, ""),
        "invoice_type": _row_get(invoice, 2, "PI"),
        "customer_id": _row_get(invoice, 3),
        "subtotal": _to_decimal(_row_get(invoice, 4, 0)),
        "tax_amount": _to_decimal(_row_get(invoice, 5, 0)),
        "total": _to_decimal(_row_get(invoice, 6, 0)),
        "cgst": _to_decimal(_row_get(invoice, 7, 0)),
        "sgst": _to_decimal(_row_get(invoice, 8, 0)),
        "igst": _to_decimal(_row_get(invoice, 9, 0)),
        "status": _row_get(invoice, 10, "unpaid"),
        "lead_id": _row_get(invoice, 11),
        "created_at": _row_get(invoice, 12, ""),
        "po_number": _row_get(invoice, 13, ""),
        "place_of_supply": _row_get(invoice, 14, ""),
        "payment_terms": _row_get(invoice, 15, "Net 30 days"),
        "due_date": _row_get(invoice, 16, ""),
        "total_in_words": _row_get(invoice, 17, ""),
    }


def _normalize_customer(customer):
    if isinstance(customer, dict):
        return {
            "name": customer.get("name", ""),
            "email": customer.get("email", ""),
            "gstin": customer.get("gstin", ""),
            "state": customer.get("state", ""),
            "address": customer.get("address", ""),
            "contact": customer.get("contact") or customer.get("phone", ""),
        }

    return {
        "name": _row_get(customer, 1, ""),
        "email": _row_get(customer, 2, ""),
        "gstin": _row_get(customer, 3, ""),
        "state": _row_get(customer, 4, ""),
        "address": _row_get(customer, 5, ""),
        "contact": _row_get(customer, 6, _row_get(customer, 5, "")),
    }


def _normalize_company(company):
    if isinstance(company, dict):
        return {
            "name": company.get("name", ""),
            "gstin": company.get("gstin", ""),
            "address": company.get("address", ""),
            "logo_path": company.get("logo_path", ""),
            "email": company.get("email", ""),
            "phone": company.get("phone", ""),
            "bank_name": company.get("bank_name", ""),
            "bank_account": company.get("bank_account", ""),
            "ifsc_code": company.get("ifsc_code", ""),
        }

    return {
        "name": _row_get(company, 1, ""),
        "gstin": _row_get(company, 2, ""),
        "address": _row_get(company, 3, ""),
        "logo_path": _row_get(company, 4, ""),
        "email": _row_get(company, 5, ""),
        "phone": _row_get(company, 6, ""),
        "bank_name": _row_get(company, 8, ""),
        "bank_account": _row_get(company, 9, ""),
        "ifsc_code": _row_get(company, 10, ""),
    }


def _normalize_items(items):
    normalized = []
    for item in items or []:
        name = _row_get(item, "name", _row_get(item, 2, ""))
        qty = _to_decimal(_row_get(item, "qty", _row_get(item, 3, 0)))
        price = _to_decimal(_row_get(item, "price", _row_get(item, 4, 0)))
        hsn = _row_get(item, "hsn", _row_get(item, 5, "998314"))
        normalized.append(
            {
                "name": name,
                "qty": qty,
                "price": price,
                "line_total": qty * price,
                "hsn": hsn,
            }
        )
    return normalized


def _build_context(invoice, customer, items, company):
    invoice_data = _normalize_invoice(invoice)
    company_data = _normalize_company(company)
    # Resolve logo path for PDF generation
    if company_data.get("logo_path"):
        company_data["logo_path"] = _resolve_image_path(company_data["logo_path"])
    
    return {
        "invoice": invoice_data,
        "customer": _normalize_customer(customer),
        "items": _normalize_items(items),
        "company": company_data,
        "document_title": "PROFORMA INVOICE" if invoice_data["invoice_type"] == "PI" else "TAX INVOICE",
    }


def _draw_wrapped_text(pdf, text, x, y, max_width, line_height=12):
    text = (text or "").strip()
    if not text:
        return y

    words = text.split()
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if pdf.stringWidth(candidate, "Helvetica", 10) <= max_width:
            current.append(word)
        else:
            pdf.drawString(x, y, " ".join(current))
            y -= line_height
            current = [word]

    if current:
        pdf.drawString(x, y, " ".join(current))
        y -= line_height

    return y


def _generate_reportlab_pdf(context, file_path):
    pdf = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    left = 18 * mm
    right = width - (18 * mm)
    logo_x = right - 50 * mm
    y = height - (20 * mm)

    invoice = context["invoice"]
    customer = context["customer"]
    company = context["company"]
    items = context["items"]

    # Draw logo if available
    if company.get("logo_path"):
        try:
            logo_path = company["logo_path"]
            # Handle file:// URLs
            if logo_path.startswith("file://"):
                logo_path = logo_path[7:]  # Remove file:// prefix
            
            if os.path.exists(logo_path):
                img = ImageReader(logo_path)
                img_width, img_height = img.getSize()
                # Scale logo to fit (max 40mm width, 15mm height)
                max_width = 40 * mm
                max_height = 15 * mm
                scale = min(max_width / img_width, max_height / img_height, 1.0)
                final_width = img_width * scale
                final_height = img_height * scale
                
                pdf.drawImage(logo_path, logo_x, y - final_height, 
                            width=final_width, height=final_height, 
                            preserveAspectRatio=True)
                y -= (final_height + 5 * mm)
        except Exception as e:
            print(f"Warning: Could not load logo: {e}")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(left, y, company["name"] or "Company")
    pdf.setFont("Helvetica", 10)
    y -= 14
    y = _draw_wrapped_text(pdf, company["address"], left, y, 95 * mm)
    if company["gstin"]:
        pdf.drawString(left, y, f"GSTIN: {company['gstin']}")
        y -= 12
    if company["phone"]:
        pdf.drawString(left, y, f"Phone: {company['phone']}")
        y -= 12
    if company["email"]:
        pdf.drawString(left, y, f"Email: {company['email']}")
        y -= 12

    title_y = height - (20 * mm)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawRightString(right, title_y, context["document_title"])
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(right, title_y - 16, f"Invoice No: {invoice['invoice_number']}")
    pdf.drawRightString(right, title_y - 30, f"Date: {invoice['created_at']}")

    y -= 10
    pdf.setStrokeColor(colors.grey)
    pdf.line(left, y, right, y)
    y -= 20

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left, y, "Bill To")
    y -= 14
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y, customer["name"] or "Customer")
    y -= 12
    pdf.setFont("Helvetica", 10)
    y = _draw_wrapped_text(pdf, customer["address"], left, y, 110 * mm)
    if customer["contact"]:
        pdf.drawString(left, y, f"Contact: {customer['contact']}")
        y -= 12
    if customer["email"]:
        pdf.drawString(left, y, f"Email: {customer['email']}")
        y -= 12
    if customer["gstin"]:
        pdf.drawString(left, y, f"GSTIN: {customer['gstin']}")
        y -= 12
    y -= 10

    table_top = y
    row_height = 10 * mm
    col_x = [left, left + 15 * mm, left + 95 * mm, left + 120 * mm, left + 150 * mm, right]

    pdf.setFillColor(colors.HexColor("#f2f2f2"))
    pdf.rect(left, table_top - row_height + 2, right - left, row_height, fill=1, stroke=0)
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 10)
    headers = ["#", "Item", "Qty", "Price", "Total"]
    header_positions = [col_x[0] + 3, col_x[1] + 3, col_x[2] + 3, col_x[3] + 3, col_x[4] + 3]
    for header, position in zip(headers, header_positions):
        pdf.drawString(position, table_top - 5 * mm, header)

    y = table_top - row_height - 2
    pdf.setFont("Helvetica", 10)
    for index, item in enumerate(items, start=1):
        if y < 55 * mm:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - (25 * mm)
        pdf.drawString(col_x[0] + 3, y, str(index))
        pdf.drawString(col_x[1] + 3, y, str(item["name"]))
        pdf.drawRightString(col_x[3] - 4, y, str(item["qty"]))
        pdf.drawRightString(col_x[4] - 4, y, _format_money(item["price"]))
        pdf.drawRightString(right - 4, y, _format_money(item["line_total"]))
        y -= 14

    y -= 8
    summary_x_label = left + 115 * mm
    summary_x_value = right
    summary_rows = [("Subtotal", invoice["subtotal"])]
    if invoice["cgst"] > 0 or invoice["sgst"] > 0:
        summary_rows.append(("CGST", invoice["cgst"]))
        summary_rows.append(("SGST", invoice["sgst"]))
    elif invoice["igst"] > 0:
        summary_rows.append(("IGST", invoice["igst"]))
    elif invoice["tax_amount"] > 0:
        summary_rows.append(("Tax", invoice["tax_amount"]))
    summary_rows.append(("Total", invoice["total"]))

    for label, value in summary_rows:
        font_name = "Helvetica-Bold" if label == "Total" else "Helvetica"
        pdf.setFont(font_name, 10)
        pdf.drawString(summary_x_label, y, label)
        pdf.drawRightString(summary_x_value, y, _format_money(value))
        y -= 14

    y -= 16
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y, "Terms & Conditions")
    y -= 14
    pdf.setFont("Helvetica", 10)
    pdf.drawString(left, y, "1. Payment due within 7 days.")
    y -= 12
    pdf.drawString(left, y, "2. No refund after service delivery.")
    y -= 24

    if company["bank_name"] or company["bank_account"] or company["ifsc_code"]:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, y, "Bank Details")
        y -= 14
        pdf.setFont("Helvetica", 10)
        if company["bank_name"]:
            pdf.drawString(left, y, f"Bank: {company['bank_name']}")
            y -= 12
        if company["bank_account"]:
            pdf.drawString(left, y, f"Account No: {company['bank_account']}")
            y -= 12
        if company["ifsc_code"]:
            pdf.drawString(left, y, f"IFSC: {company['ifsc_code']}")
            y -= 12

    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(right, 25 * mm, f"Authorized Signatory - {company['name'] or 'Company'}")
    pdf.save()


def _pdf_escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _generate_basic_pdf(context, file_path):
    invoice = context["invoice"]
    customer = context["customer"]
    company = context["company"]
    items = context["items"]

    lines = [
        (16, 50, 800, company["name"] or "Company"),
        (11, 50, 784, company["address"] or ""),
        (11, 50, 768, f"GSTIN: {company['gstin']}" if company["gstin"] else ""),
        (14, 380, 800, context["document_title"]),
        (11, 380, 784, f"Invoice No: {invoice['invoice_number']}"),
        (11, 380, 768, f"Date: {invoice['created_at']}"),
        (12, 50, 730, "Bill To"),
        (11, 50, 714, customer["name"] or "Customer"),
        (11, 50, 698, customer["address"] or ""),
        (11, 50, 682, f"GSTIN: {customer['gstin']}" if customer["gstin"] else ""),
        (11, 50, 660, "Items"),
    ]

    y = 642
    for index, item in enumerate(items, start=1):
        line = f"{index}. {item['name']} | Qty: {item['qty']} | Price: {_format_money(item['price'])} | Amount: {_format_money(item['line_total'])}"
        lines.append((10, 50, y, line))
        y -= 16

    y -= 8
    lines.append((11, 320, y, f"Subtotal: {_format_money(invoice['subtotal'])}"))
    y -= 16
    if invoice["cgst"] > 0 or invoice["sgst"] > 0:
        lines.append((11, 320, y, f"CGST: {_format_money(invoice['cgst'])}"))
        y -= 16
        lines.append((11, 320, y, f"SGST: {_format_money(invoice['sgst'])}"))
        y -= 16
    elif invoice["igst"] > 0:
        lines.append((11, 320, y, f"IGST: {_format_money(invoice['igst'])}"))
        y -= 16
    lines.append((12, 320, y, f"Total: {_format_money(invoice['total'])}"))
    y -= 28

    if company["bank_name"] or company["bank_account"] or company["ifsc_code"]:
        lines.append((11, 50, y, "Bank Details"))
        y -= 16
        if company["bank_name"]:
            lines.append((10, 50, y, f"Bank: {company['bank_name']}"))
            y -= 14
        if company["bank_account"]:
            lines.append((10, 50, y, f"Account: {company['bank_account']}"))
            y -= 14
        if company["ifsc_code"]:
            lines.append((10, 50, y, f"IFSC: {company['ifsc_code']}"))
            y -= 14

    lines.append((10, 50, max(y - 20, 60), f"Authorized Signatory - {company['name'] or 'Company'}"))

    content_parts = ["BT\n"]
    for font_size, x, line_y, text in lines:
        if not text:
            continue
        content_parts.append(f"/F1 {font_size} Tf 1 0 0 1 {x} {line_y} Tm ({_pdf_escape(text)}) Tj\n")
    content_parts.append("ET\n")
    content = "".join(content_parts).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("latin-1")
    )

    with open(file_path, "wb") as pdf_file:
        pdf_file.write(pdf)


def generate_invoice_pdf(invoice, customer, items, company):
    context = _build_context(invoice, customer, items, company)
    invoice_number = context["invoice"]["invoice_number"] or "invoice"
    safe_invoice_number = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(invoice_number))
    file_path = os.path.join(tempfile.gettempdir(), f"{safe_invoice_number}.pdf")
    template = "invoices/pi.html" if context["invoice"]["invoice_type"] == "PI" else "invoices/tax.html"
    html = render_template(template, **context)

    if WEASYPRINT_AVAILABLE:
        HTML(string=html).write_pdf(file_path)
    elif PDFKIT_AVAILABLE:
        config = _pdfkit_configuration()
        if config:
            pdfkit.from_string(html, file_path, configuration=config)
        elif REPORTLAB_AVAILABLE:
            _generate_reportlab_pdf(context, file_path)
        else:
            _generate_basic_pdf(context, file_path)
    elif REPORTLAB_AVAILABLE:
        _generate_reportlab_pdf(context, file_path)
    else:
        _generate_basic_pdf(context, file_path)

    return file_path
