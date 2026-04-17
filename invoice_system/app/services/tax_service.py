class TaxService:

    def calculate_tax(self, amount, seller_state, customer_state):
        GST_RATE = 0.18

        if seller_state == customer_state:
            # CGST + SGST
            cgst = amount * (GST_RATE / 2)
            sgst = amount * (GST_RATE / 2)
            igst = 0
            cgst_rate = GST_RATE / 2
            sgst_rate = GST_RATE / 2
            igst_rate = 0
        else:
            # IGST
            cgst = 0
            sgst = 0
            igst = amount * GST_RATE
            cgst_rate = 0
            sgst_rate = 0
            igst_rate = GST_RATE

        return {
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "cgst_rate": cgst_rate,
            "sgst_rate": sgst_rate,
            "igst_rate": igst_rate,
            "total_tax": cgst + sgst + igst
        }