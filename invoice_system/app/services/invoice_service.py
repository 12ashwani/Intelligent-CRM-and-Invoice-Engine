from app.repositories.customer_repo import CustomerRepo
from app.repositories.invoice_repo import InvoiceRepo
from app.services.tax_service import TaxService
from app.services.number_generator import generate_invoice_number

class InvoiceService:

    def __init__(self):
        self.repo = InvoiceRepo()
        self.tax = TaxService()
        self.customer_repo = CustomerRepo()
        self.seller_state = "Delhi"  # configure this

    def create_invoice(self, data):
        items = data["items"]
        invoice_type = data["invoice_type"]
        customer_id = data["customer_id"]

        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise ValueError("Selected customer was not found.")
        customer_state = customer["state"]

        subtotal = sum(i["qty"] * i["price"] for i in items)

        tax_data = self.tax.calculate_tax(
            subtotal,
            self.seller_state,
            customer_state
        )

        total = subtotal + tax_data["total_tax"]

        invoice_number = generate_invoice_number(invoice_type)

        # Generate amount in words
        from app.utils.number_to_words import number_to_words_indian
        total_in_words = number_to_words_indian(total)

        invoice_data = {
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "customer_id": customer_id,
            "subtotal": subtotal,
            "cgst": tax_data["cgst"],
            "sgst": tax_data["sgst"],
            "igst": tax_data["igst"],
            "cgst_rate": tax_data["cgst_rate"],
            "sgst_rate": tax_data["sgst_rate"],
            "igst_rate": tax_data["igst_rate"],
            "tax": tax_data["total_tax"],
            "total": total,
            "po_number": data.get("po_number", ""),
            "place_of_supply": data.get("place_of_supply", ""),
            "payment_terms": data.get("payment_terms", "Net 30 days"),
            "due_date": data.get("due_date", None),
            "total_in_words": total_in_words,
        }

        # Add HSN code to items if provided
        default_hsn = data.get("hsn_code", "998314")
        for item in items:
            if "hsn" not in item:
                item["hsn"] = default_hsn

        return self.repo.save(invoice_data, items)

    def get_invoice_details(self, invoice_id):
        
        return self.repo.get_full_invoice(invoice_id)
    def get_dashboard_data(self):
        stats = self.repo.get_dashboard_stats()
        monthly = self.repo.get_monthly_sales()
        types = self.repo.get_invoice_types()

        return {
            "stats": stats,
            "monthly": monthly,
            "types": types
        }
