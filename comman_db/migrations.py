from datetime import datetime  # ADD THIS IMPORT
from .connection import get_db_connection


# =========================================================
# HELPER FUNCTIONS & CONSTANTS (keep all your SELECT statements)
# =========================================================

LEAD_PAYMENT_SELECT = """
    COALESCE(p.total_amount, 0) AS total_fee,
    COALESCE(p.govt_amount, 0) AS govt_fee,
    COALESCE(p.professional_amount, 0) AS professional_fee,
    COALESCE(p.govt_amount, 0) + COALESCE(p.professional_amount, 0) AS paid_amount,
    GREATEST(COALESCE(p.total_amount, 0) - (COALESCE(p.govt_amount, 0) + COALESCE(p.professional_amount, 0)), 0) AS pending_amount
"""



LEAD_PENDING_DEPARTMENT_SELECT = """
    CASE
        WHEN l.status = 'New' THEN 'Marketing'
        WHEN l.status = 'Assigned to Operations' THEN 'Operations'
        WHEN l.status = 'Ready for Accounts' THEN 'Accounts'
        WHEN l.status = 'Assigned to Accounts' THEN 'Accounts'
        WHEN l.status = 'Pending' AND p.lead_id IS NOT NULL THEN 'Accounts'
        WHEN l.status = 'Pending' AND o.lead_id IS NOT NULL THEN 'Operations'
        WHEN l.status = 'Failed' AND p.lead_id IS NOT NULL THEN 'Accounts'
        WHEN l.status = 'Failed' AND o.lead_id IS NOT NULL THEN 'Operations'
        WHEN l.status = 'Completed' THEN 'Accounts'
        ELSE 'Marketing'
    END AS pending_department
"""

LATEST_OPERATION_REMARK_SELECT = """
    (
        SELECT r.remark
        FROM operation_remarks r
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark
"""

LATEST_OPERATION_REMARK_AT_SELECT = """
    (
        SELECT r.created_at
        FROM operation_remarks r
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark_created_at
"""

LATEST_OPERATION_REMARK_BY_SELECT = """
    (
        SELECT e.name
        FROM operation_remarks r
        LEFT JOIN employees e ON e.id = r.employee_id
        WHERE r.lead_id = l.id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 1
    ) AS operation_remark_by_name
"""


def _normalize_status_text(value):
    return (value or "").strip().lower()


def _normalize_payment_status(value):
    status = _normalize_status_text(value)
    if status in {"received", "done", "paid"}:
        return "Paid"
    if status == "failed":
        return "Failed"
    return "Pending"


def _matches_any(value, options):
    normalized = _normalize_status_text(value)
    return normalized in {_normalize_status_text(option) for option in options}


def _parse_datetime_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return datetime(value.year, value.month, value.day)

    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _format_datetime_display(value):
    parsed = _parse_datetime_value(value)
    if not parsed:
        return ""
    return parsed.strftime("%d %b %Y %I:%M %p")


def _build_workflow_fields(row):
    lead_status = _normalize_status_text(row.get("status"))
    file_status = _normalize_status_text(row.get("file_status"))
    pending_department = row.get("pending_department") or "Marketing"
    account_remark = row.get("account_remark") or ""

    certificate_done = _matches_any(
        account_remark,
        {"certificate done", "certificate received", "certificate downloaded"},
    )
    professional_fee_pending = _matches_any(
        account_remark,
        {"professional fee pending"},
    )
    government_fee_pending = _matches_any(
        account_remark,
        {"government fee pending", "gov fee pending"},
    )

    govt_status_label = _normalize_payment_status(row.get("govt_payment_status"))
    prof_status_label = _normalize_payment_status(row.get("professional_payment_status"))

    if certificate_done:
        workflow_status = "Certificate Done"
        certificate_status = "Done"
    elif professional_fee_pending or (
        govt_status_label == "Paid" and prof_status_label == "Pending"
    ):
        workflow_status = "Professional Fee Pending"
        certificate_status = "Pending"
    elif government_fee_pending or govt_status_label == "Pending":
        workflow_status = "Government Fee Pending"
        certificate_status = "Pending"
    elif lead_status == "pending":
        workflow_status = f"Pending at {pending_department}"
        certificate_status = "Pending"
    elif lead_status == "completed":
        workflow_status = "Completed"
        certificate_status = "Done"
    elif file_status == "failed" or lead_status == "failed":
        workflow_status = "Failed"
        certificate_status = "Pending"
    elif file_status == "done":
        workflow_status = "Ready for Accounts"
        certificate_status = "Pending"
    elif file_status == "pending":
        workflow_status = "Pending at Operations"
        certificate_status = "Pending"
    elif lead_status == "assigned to accounts":
        workflow_status = "Pending at Accounts"
        certificate_status = "Pending"
    elif lead_status == "assigned to operations":
        workflow_status = "Pending at Operations"
        certificate_status = "Pending"
    else:
        workflow_status = row.get("status") or "Pending at Marketing"
        certificate_status = "Pending"

    if workflow_status.startswith("Pending at "):
        pending_label = workflow_status
    elif lead_status == "new":
        pending_label = "Pending at Marketing"
    else:
        pending_label = f"Pending at {pending_department}" if lead_status == "pending" else ""

    if workflow_status in {"Certificate Done", "Professional Fee Pending", "Government Fee Pending"}:
        department_remark = row.get("account_remark") or row.get("operation_remark") or ""
    elif pending_department == "Operations":
        department_remark = row.get("operation_remark") or row.get("account_remark") or ""
    elif pending_department == "Accounts":
        department_remark = row.get("account_remark") or row.get("operation_remark") or ""
    else:
        department_remark = row.get("operation_remark") or row.get("account_remark") or ""

    payment_status_label = "Pending"
    if govt_status_label == "Failed" or prof_status_label == "Failed":
        payment_status_label = "Failed"
    elif govt_status_label == "Paid" and prof_status_label == "Paid":
        payment_status_label = "Paid"
    elif govt_status_label == "Paid" or prof_status_label == "Paid":
        payment_status_label = "Partial"

    return {
        "govt_fee_status_label": govt_status_label,
        "professional_fee_status_label": prof_status_label,
        "workflow_status_label": workflow_status,
        "pending_label": pending_label,
        "certificate_status": certificate_status,
        "department_remark": department_remark,
        "payment_status_label": payment_status_label,
    }


def _build_last_updated_fields(row):
    candidates = [
        (
            _parse_datetime_value(row.get("payment_updated_at")),
            row.get("payment_updated_by_name") or row.get("account_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("operation_updated_at")),
            row.get("operation_updated_by_name") or row.get("operation_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("operation_remark_created_at")),
            row.get("operation_remark_by_name") or row.get("operation_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("payment_date")),
            row.get("payment_updated_by_name") or row.get("account_executive_name"),
        ),
        (
            _parse_datetime_value(row.get("created_at")),
            row.get("marketing_executive_name"),
        ),
    ]

    latest_timestamp = None
    latest_name = ""

    for timestamp, name in candidates:
        if not timestamp:
            continue
        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_name = name or ""

    return {
        "last_updated_by_name": latest_name,
        "last_updated_at": latest_timestamp,
        "last_updated_at_display": _format_datetime_display(latest_timestamp),
    }


def enrich_lead_row(row):
    enriched = dict(row)
    enriched.update(_build_workflow_fields(enriched))
    enriched.update(_build_last_updated_fields(enriched))
    return enriched


def enrich_lead_rows(rows):
    return [enrich_lead_row(row) for row in rows]

# =========================================================
# TABLE CREATION (including new invoice schema)
# =========================================================

def create_tables():
    """Create all necessary tables if they do not exist in MySQL."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Employees table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            department VARCHAR(100),
            role VARCHAR(50)
        )
    ''')

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255),
            department VARCHAR(100),
            role VARCHAR(50),
            employee_id INT,
            theme VARCHAR(10) DEFAULT 'light',
            is_active TINYINT(1) DEFAULT 1,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')

    # Leads table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE,
            company_name VARCHAR(255),
            email VARCHAR(255),
            auth_person_name VARCHAR(255),
            auth_person_number VARCHAR(50),
            auth_person_email VARCHAR(255),
            marketing_executive INT,
            service VARCHAR(255),
            status VARCHAR(50) DEFAULT 'New',
            account_executive INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(marketing_executive) REFERENCES employees(id),
            FOREIGN KEY(account_executive) REFERENCES employees(id)
        )
    ''')

    # Operations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT UNIQUE,
            client_login VARCHAR(255),
            client_password VARCHAR(255),
            file_status VARCHAR(50) DEFAULT 'pending',
            filing_date DATE,
            operation_executive INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            updated_by INT,
            FOREIGN KEY(lead_id) REFERENCES leads(id),
            FOREIGN KEY(operation_executive) REFERENCES employees(id),
            FOREIGN KEY(updated_by) REFERENCES employees(id)
        )
    ''')

    # Payments table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT UNIQUE,
            govt_payment_status VARCHAR(50) DEFAULT 'pending',
            professional_payment_status VARCHAR(50) DEFAULT 'pending',
            total_amount DECIMAL(10,2),
            govt_amount DECIMAL(10,2),
            professional_amount DECIMAL(10,2),
            payment_date DATE,
            remarks TEXT,
            account_executive INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            updated_by INT,
            FOREIGN KEY(lead_id) REFERENCES leads(id),
            FOREIGN KEY(account_executive) REFERENCES employees(id),
            FOREIGN KEY(updated_by) REFERENCES employees(id)
        )
    ''')

    # Operation remarks table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS operation_remarks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT,
            employee_id INT,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')

    # Attendance table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT,
            date DATE,
            status ENUM('present', 'absent', 'late', 'half_day') DEFAULT 'present',
            check_in_time TIME,
            check_out_time TIME,
            working_hours DECIMAL(4,2),
            remarks TEXT,
            marked_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(id),
            FOREIGN KEY(marked_by) REFERENCES employees(id),
            UNIQUE KEY unique_employee_date (employee_id, date)
        )
    ''')

    # Leave requests table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT,
            leave_type ENUM('casual', 'sick', 'annual', 'maternity', 'paternity', 'emergency') DEFAULT 'casual',
            start_date DATE,
            end_date DATE,
            total_days INT,
            reason TEXT,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by INT,
            approved_on TIMESTAMP NULL,
            remarks TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id),
            FOREIGN KEY(approved_by) REFERENCES employees(id)
        )
    ''')

    # Employee salary settings
    cur.execute('''
        CREATE TABLE IF NOT EXISTS employee_salary_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT NOT NULL UNIQUE,
            monthly_salary DECIMAL(10,2) NOT NULL,
            effective_from DATE NOT NULL,
            updated_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            FOREIGN KEY(updated_by) REFERENCES employees(id) ON DELETE SET NULL
        )
    ''')

    # Holidays table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INT AUTO_INCREMENT PRIMARY KEY,
            holiday_date DATE NOT NULL UNIQUE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES employees(id) ON DELETE SET NULL
        )
    ''')

    # ----- INVOICE MODULE TABLES -----
    
    # Customers table
    cur.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        gstin VARCHAR(50),
        state VARCHAR(100),
        address TEXT,
        phone VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Add shipping columns to customers if not exist
    for col, col_def in [("shipping_name", "VARCHAR(255)"), ("shipping_address", "TEXT")]:
        try:
            cur.execute(f"ALTER TABLE customers ADD COLUMN {col} {col_def}")
        except:
            pass

    # Company table (for multi-company billing)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            address TEXT,
            gstin VARCHAR(20),
            state VARCHAR(100),
            email VARCHAR(150),
            phone VARCHAR(20),
            logo_src TEXT,
            bank_account_name VARCHAR(255),
            bank_name VARCHAR(255),
            account_number VARCHAR(50),
            ifsc_code VARCHAR(20),
            upi_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Company settings (legacy)
    cur.execute("""CREATE TABLE IF NOT EXISTS company_settings (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255),
        gstin VARCHAR(50),
        address TEXT,
        logo_path VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(50),
        bank_name VARCHAR(255),
        bank_account VARCHAR(100),
        bank_ifsc VARCHAR(20),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )""")

    # Invoices table
    cur.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_number VARCHAR(50) UNIQUE NOT NULL,
        invoice_type ENUM('PI', 'TAX') NOT NULL,
        customer_id INT,
        company_id INT,
        subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        cgst DECIMAL(10,2) DEFAULT 0.00,
        sgst DECIMAL(10,2) DEFAULT 0.00,
        igst DECIMAL(10,2) DEFAULT 0.00,
        cgst_rate DECIMAL(5,2) DEFAULT 0,
        sgst_rate DECIMAL(5,2) DEFAULT 0,
        igst_rate DECIMAL(5,2) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'unpaid',
        lead_id INT NULL,
        date DATE,
        due_date DATE,
        po_number VARCHAR(100),
        order_number VARCHAR(100),
        payment_terms VARCHAR(100),
        transport_details VARCHAR(255),
        place_of_supply VARCHAR(100),
        tax_total DECIMAL(12,2) DEFAULT 0,
        round_off DECIMAL(10,2) DEFAULT 0,
        total_in_words TEXT,
        tax_in_words TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
        FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE SET NULL
    )''')

    # Invoice items table
    cur.execute('''CREATE TABLE IF NOT EXISTS invoice_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        hsn VARCHAR(50),
        unit VARCHAR(50),
        qty INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        line_total DECIMAL(12,2) DEFAULT 0,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )''')

    # Invoice payments table
    cur.execute('''CREATE TABLE IF NOT EXISTS invoice_payments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_id INT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        payment_date DATE,
        status VARCHAR(50) DEFAULT 'paid',
        transaction_id VARCHAR(100),
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )''')

    # Invoice sequence table
    cur.execute("""CREATE TABLE IF NOT EXISTS invoice_sequence (
        year INT NOT NULL,
        type ENUM('PI', 'TAX') NOT NULL,
        last_number INT NOT NULL DEFAULT 0,
        PRIMARY KEY (year, type)
    )""")

    # Invoice tax table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_tax (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_id INT NOT NULL,
            hsn VARCHAR(50),
            taxable_value DECIMAL(12,2) DEFAULT 0,
            rate DECIMAL(5,2),
            cgst_rate DECIMAL(5,2),
            cgst_amount DECIMAL(12,2),
            sgst_rate DECIMAL(5,2),
            sgst_amount DECIMAL(12,2),
            igst_rate DECIMAL(5,2),
            igst_amount DECIMAL(12,2),
            amount DECIMAL(12,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )
    """)

    # Create indexes (MySQL 5.6+ compatible - without IF NOT EXISTS)
    try:
        cur.execute("CREATE INDEX idx_invoice_customer ON invoices(customer_id)")
    except:
        pass
    try:
        cur.execute("CREATE INDEX idx_invoice_company ON invoices(company_id)")
    except:
        pass
    try:
        cur.execute("CREATE INDEX idx_items_invoice ON invoice_items(invoice_id)")
    except:
        pass
    try:
        cur.execute("CREATE INDEX idx_tax_invoice ON invoice_tax(invoice_id)")
    except:
        pass

    conn.commit()
    cur.close()
    conn.close()
    print("✅ All tables ready")