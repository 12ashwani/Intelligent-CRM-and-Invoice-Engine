from db.mysql import get_connection

SERVICE_DOCUMENT_REQUIREMENTS = {
    "plastic epr registration": [
        "Company PAN card copy",
        "GST registration certificate",
        "MSME/Udyam registration if available",
        "Bank account details",
        "Authorization letter from authorized signatory",
        "List of plastic products manufactured or handled",
        "Purchase invoices for plastic raw materials",
        "Production records and manufacturing process details",
        "Details of the manufacturing facility and plant address",
        "Contact information for the authorized person"
    ],
    "gst registration": [
        "PAN card copy of the business or proprietor",
        "Aadhaar card of the proprietor or partners",
        "Proof of business address",
        "Bank account statement or cancelled cheque",
        "Business constitution document",
        "Photograph of the proprietor or partners",
        "Digital signature (if required)"
    ],
    "company registration": [
        "Director/partner identity proof",
        "Address proof of directors/partners",
        "Registered office address proof",
        "Memorandum and Articles of Association",
        "Digital signature certificate for directors",
        "No objection certificate from property owner"
    ],
    "Battery EPR Registration": [
        "Company PAN card copy",
        "GST registration certificate",
        "MSME/Udyam registration if available",
        "IEC code (if applicable)",
        "CTO declaration for battery manufacturing or import",
        "List of battery types and quantities handled",
        "Details of the manufacturing or import facility",
        "Contact information for the authorized person"]

}


def get_today_leads():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id,
        company_name AS name,
        auth_person_name AS contact_name,
        auth_person_number AS phone,
        status,
        created_at
    FROM leads
    WHERE DATE(created_at) = CURDATE()
    ORDER BY created_at DESC
    """

    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_leads_by_status(status):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id,
        company_name AS name,
        auth_person_name AS contact_name,
        auth_person_number AS phone,
        status,
        created_at
    FROM leads
    WHERE status = %s
    ORDER BY created_at DESC
    """

    cursor.execute(query, (status,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_lead_by_company(company_name):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id,
        company_name AS name,
        auth_person_name AS contact_name,
        auth_person_number AS phone,
        auth_person_email AS email,
        status,
        created_at
    FROM leads
    WHERE company_name LIKE %s
    ORDER BY created_at DESC
    LIMIT 10
    """

    cursor.execute(query, (f"%{company_name}%",))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_status_report():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT status, COUNT(*) AS total
    FROM leads
    GROUP BY status
    ORDER BY total DESC
    """

    cursor.execute(query)
    data = cursor.fetchall()

    # Add total count
    total_query = "SELECT COUNT(*) AS total_leads FROM leads"
    cursor.execute(total_query)
    total_result = cursor.fetchone()
    if total_result:
        data.insert(0, {"status": "TOTAL", "total": total_result["total_leads"]})

    cursor.close()
    conn.close()
    return data


def search_customer(query):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    like_query = f"%{query}%"
    sql = """
    SELECT
        id,
        company_name AS name,
        auth_person_name AS contact_name,
        auth_person_number AS phone,
        auth_person_email AS email,
        service,
        status,
        created_at
    FROM leads
    WHERE company_name LIKE %s
       OR auth_person_email LIKE %s
       OR auth_person_name LIKE %s
    LIMIT 20
    """

    cursor.execute(sql, (like_query, like_query, like_query))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_payment_history(query):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    like_query = f"%{query}%"
    sql = """
    SELECT
        p.id AS payment_id,
        l.company_name AS lead_company,
        l.auth_person_email AS lead_email,
        p.total_amount,
        p.govt_amount,
        p.professional_amount,
        p.govt_payment_status,
        p.professional_payment_status,
        p.payment_date,
        p.remarks,
        p.created_at
    FROM payments p
    LEFT JOIN leads l ON p.lead_id = l.id
    WHERE l.company_name LIKE %s
       OR l.auth_person_email LIKE %s
       OR l.auth_person_name LIKE %s
    ORDER BY p.created_at DESC
    LIMIT 50
    """

    cursor.execute(sql, (like_query, like_query, like_query))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_service_documents(service_text):
    normalized = service_text.lower().strip()
    if "all service" in normalized or "all services" in normalized or "all documents" in normalized:
        return SERVICE_DOCUMENT_REQUIREMENTS

    # Direct key matching
    for key in SERVICE_DOCUMENT_REQUIREMENTS:
        if key in normalized or normalized in key:
            return {key: SERVICE_DOCUMENT_REQUIREMENTS[key]}

    # Smart matching for common abbreviations
    if "epr" in normalized and "plastic" in normalized:
        key = "plastic epr registration"
        return {key: SERVICE_DOCUMENT_REQUIREMENTS[key]}

    # Handle "plastic epr" alone
    if normalized == "plastic epr" or normalized == "epr plastic":
        key = "plastic epr registration"
        return {key: SERVICE_DOCUMENT_REQUIREMENTS[key]}

    # Handle partial service names
    service_mappings = {
        "plastic epr": "plastic epr registration",
        "gst": "gst registration",
        "company": "company registration",
        "msme": "company registration",  # MSME is part of company registration
        "udyam": "company registration",  # Udyam is MSME
    }

    for abbr, full_key in service_mappings.items():
        if abbr in normalized and full_key in SERVICE_DOCUMENT_REQUIREMENTS:
            return {full_key: SERVICE_DOCUMENT_REQUIREMENTS[full_key]}

    return {"unknown_service": [
        "No predefined service found. Please specify the exact service name such as:",
        "'plastic epr registration', 'gst registration', 'company registration', or 'all services'."
    ]}


def get_pending_payments():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        p.id,
        l.company_name AS lead_company,
        p.total_amount,
        p.govt_amount,
        p.professional_amount,
        p.govt_payment_status,
        p.professional_payment_status,
        p.payment_date,
        p.remarks,
        p.created_at
    FROM payments p
    LEFT JOIN leads l ON p.lead_id = l.id
    WHERE p.govt_payment_status = 'pending'
       OR p.professional_payment_status = 'pending'
    ORDER BY p.created_at DESC
    """

    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data