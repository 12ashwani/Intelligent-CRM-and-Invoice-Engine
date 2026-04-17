from tools.crm_tools import *
from llm.local_llm import ask_llm


def execute(action, user_text):

    if action == "today_leads":
        return get_today_leads()

    if action == "pending_payment":
        return get_pending_payments()

    if action == "status_report":
        return get_status_report()

    if action == "lead_details":
        return get_lead_by_company(user_text)

    if action == "customer_search":
        return search_customer(user_text)

    if action == "payment_history":
        return get_payment_history(user_text)

    if action == "service_documents":
        return get_service_documents(user_text)

    return get_service_documents(user_text)