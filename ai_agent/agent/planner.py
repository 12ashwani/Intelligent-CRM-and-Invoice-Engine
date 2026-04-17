def decide(text):

    text = text.lower()

    lead_phrases = ["today lead", "today leads", "show leads", "list leads", "lead report"]
    payment_phrases = ["pending payment", "pending payments", "payment due", "payments pending"]
    status_phrases = ["status report", "lead status", "status summary", "report by status", "how many leads", "total leads", "lead count", "leads count"]
    lead_detail_phrases = ["lead detail", "lead details", "lead lookup", "lead information", "lead by company"]
    customer_search_phrases = ["search customer", "customer search", "search by email", "find customer", "customer details"]
    payment_history_phrases = ["payment history", "invoice history", "payment records", "invoice details", "payments history"]
    document_phrases = ["documents required", "documents needed", "document list", "what documents", "required documents"]

    if any(phrase in text for phrase in document_phrases):
        return "service_documents"

    if any(phrase in text for phrase in status_phrases):
        return "status_report"

    if any(phrase in text for phrase in lead_detail_phrases) and "company" in text:
        return "lead_details"

    if any(phrase in text for phrase in customer_search_phrases):
        return "customer_search"

    if any(phrase in text for phrase in payment_history_phrases):
        return "payment_history"

    if any(phrase in text for phrase in lead_phrases):
        return "today_leads"

    if any(phrase in text for phrase in payment_phrases):
        return "pending_payment"

    if "lead" in text and "today" in text:
        return "today_leads"

    if "payment" in text:
        return "pending_payment"

    return "service_documents"