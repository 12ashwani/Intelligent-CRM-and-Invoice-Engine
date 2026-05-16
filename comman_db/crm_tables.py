from .crm_core import get_db_connection, fetchall_dict
from typing import Dict, Any, List, Optional
# =========================================================
# TABLE CREATION (including new invoice schema)
# =========================================================

def create_tables():
    """Create all necessary tables if they do not exist in MySQL."""
    conn = get_db_connection()
    cur = conn.cursor()

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

# =================================================
# Invoice tables
# =================================================

    cur.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        gstin VARCHAR(50),
        state VARCHAR(100),
        address TEXT,
        phone VARCHAR(50),
        shipping_name VARCHAR(255),
        shipping_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_number VARCHAR(50) UNIQUE NOT NULL,
        invoice_type ENUM('PI', 'TAX') NOT NULL,
        customer_id INT,
        subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        cgst DECIMAL(10,2) DEFAULT 0.00,
        sgst DECIMAL(10,2) DEFAULT 0.00,
        igst DECIMAL(10,2) DEFAULT 0.00,
        status VARCHAR(20) DEFAULT 'unpaid',
        lead_id INT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        company_id INT,
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
        cgst_rate DECIMAL(5,2) DEFAULT 0,
        sgst_rate DECIMAL(5,2) DEFAULT 0,
        igst_rate DECIMAL(5,2) DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
        FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS invoice_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        qty INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        description TEXT,
        hsn VARCHAR(50),
        unit VARCHAR(50),
        line_total DECIMAL(12,2) DEFAULT 0,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )''')

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

    cur.execute("""CREATE TABLE IF NOT EXISTS invoice_sequence (
        year INT NOT NULL,
        type ENUM('PI', 'TAX') NOT NULL,
        last_number INT NOT NULL DEFAULT 0,
        PRIMARY KEY (year, type)
    )""")

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

    # Add foreign key for company_id in invoices
    try:
        cur.execute("ALTER TABLE invoices ADD CONSTRAINT fk_invoices_company FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE SET NULL")
    except:
        pass

    # Indexes
    def ensure_index(table_name, index_name, ddl_sql):
        cur.execute(
            "SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s LIMIT 1",
            (table_name, index_name),
        )
        if not cur.fetchone():
            cur.execute(ddl_sql)

    ensure_index("invoices", "idx_invoice_customer", "CREATE INDEX idx_invoice_customer ON invoices(customer_id)")
    ensure_index("invoices", "idx_invoice_company", "CREATE INDEX idx_invoice_company ON invoices(company_id)")
    ensure_index("invoice_items", "idx_items_invoice", "CREATE INDEX idx_items_invoice ON invoice_items(invoice_id)")
    ensure_index("invoice_tax", "idx_tax_invoice", "CREATE INDEX idx_tax_invoice ON invoice_tax(invoice_id)")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ MySQL tables ready")

# =========================================================
# DASHBOARDS
# =========================================================

def get_department_dashboard(role: str, employee_id: Optional[int] = None) -> List[Dict]:
    """Return dashboard data for a department role."""
    from .crm_core import enrich_lead_rows, LEAD_PENDING_DEPARTMENT_SELECT, LEAD_PAYMENT_SELECT, LATEST_OPERATION_REMARK_SELECT, LATEST_OPERATION_REMARK_AT_SELECT, LATEST_OPERATION_REMARK_BY_SELECT
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if role == "admin":
        cur.execute("""
            SELECT l.*, e.name as marketing_executive_name,
                   """ + LEAD_PENDING_DEPARTMENT_SELECT + """,
                   """ + LEAD_PAYMENT_SELECT + """
            FROM leads l
            LEFT JOIN employees e ON l.marketing_executive = e.id
            LEFT JOIN operations o ON l.id = o.lead_id
            LEFT JOIN payments p ON l.id = p.lead_id
            ORDER BY (l.status = 'New') DESC, l.created_at DESC
        """)
    elif role == "marketing":
        cur.execute("""
            SELECT l.*, e.name as marketing_executive_name,
                   op.name as operation_executive_name,
                   o.file_status, o.client_login, o.client_password, o.filing_date,
                   p.govt_payment_status, p.professional_payment_status,
                   p.payment_date, p.remarks AS account_remark,
                   p.total_amount, p.govt_amount, p.professional_amount,
                   opu.name AS operation_updated_by_name,
                   acu.name AS payment_updated_by_name,
                   o.updated_at AS operation_updated_at,
                   p.updated_at AS payment_updated_at,
                   """ + LATEST_OPERATION_REMARK_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_AT_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_BY_SELECT + """,
                   """ + LEAD_PENDING_DEPARTMENT_SELECT + """,
                   """ + LEAD_PAYMENT_SELECT + """
            FROM leads l
            LEFT JOIN employees e ON l.marketing_executive = e.id
            LEFT JOIN operations o ON l.id = o.lead_id
            LEFT JOIN employees op ON o.operation_executive = op.id
            LEFT JOIN payments p ON l.id = p.lead_id
            LEFT JOIN employees opu ON o.updated_by = opu.id
            LEFT JOIN employees acu ON p.updated_by = acu.id
            WHERE l.marketing_executive=%s
            ORDER BY (l.status = 'New') DESC, l.created_at DESC
        """, (employee_id,))
    elif role == "operations":
        cur.execute("""
            SELECT l.*, o.id as operation_id, o.file_status, o.client_login,
                   o.client_password, o.filing_date, o.operation_executive,
                   o.created_at as operation_created_at, o.updated_at AS operation_updated_at,
                   e.name as operation_executive_name, m.name as marketing_executive_name,
                   p.govt_payment_status, p.professional_payment_status,
                   p.payment_date, p.remarks AS account_remark, p.updated_at AS payment_updated_at,
                   acc.name AS account_executive_name, opu.name AS operation_updated_by_name,
                   acu.name AS payment_updated_by_name,
                   """ + LATEST_OPERATION_REMARK_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_AT_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_BY_SELECT + """,
                   """ + LEAD_PENDING_DEPARTMENT_SELECT + """,
                   """ + LEAD_PAYMENT_SELECT + """
            FROM leads l
            JOIN operations o ON l.id=o.lead_id
            LEFT JOIN employees e ON o.operation_executive = e.id
            LEFT JOIN employees m ON l.marketing_executive = m.id
            LEFT JOIN payments p ON l.id = p.lead_id
            LEFT JOIN employees acc ON p.account_executive = acc.id
            LEFT JOIN employees opu ON o.updated_by = opu.id
            LEFT JOIN employees acu ON p.updated_by = acu.id
            WHERE o.operation_executive=%s
            ORDER BY (l.status = 'New') DESC, l.created_at DESC
        """, (employee_id,))
    elif role == "accounts":
        cur.execute("""
            SELECT l.*, p.id as payment_id, p.govt_payment_status,
                   p.professional_payment_status, p.total_amount, p.govt_amount,
                   p.professional_amount, p.payment_date, p.remarks,
                   p.remarks as account_remark, p.account_executive,
                   p.created_at as payment_created_at, p.updated_at AS payment_updated_at,
                   o.client_login, o.client_password, o.file_status, o.filing_date,
                   o.updated_at AS operation_updated_at, e.name as account_executive_name,
                   m.name as marketing_executive_name, op.name as operation_executive_name,
                   opu.name AS operation_updated_by_name, acu.name AS payment_updated_by_name,
                   """ + LATEST_OPERATION_REMARK_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_AT_SELECT + """,
                   """ + LATEST_OPERATION_REMARK_BY_SELECT + """,
                   """ + LEAD_PENDING_DEPARTMENT_SELECT + """,
                   """ + LEAD_PAYMENT_SELECT + """
            FROM leads l
            JOIN payments p ON l.id=p.lead_id
            LEFT JOIN operations o ON l.id = o.lead_id
            LEFT JOIN employees e ON p.account_executive = e.id
            LEFT JOIN employees m ON l.marketing_executive = m.id
            LEFT JOIN employees op ON o.operation_executive = op.id
            LEFT JOIN employees opu ON o.updated_by = opu.id
            LEFT JOIN employees acu ON p.updated_by = acu.id
            WHERE p.account_executive=%s
            ORDER BY l.created_at DESC
        """, (employee_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return enrich_lead_rows(rows)

def get_admin_leads_overview(
    team: Optional[str] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    lead_date: Optional[str] = None,
) -> List[Dict]:
    """Return all leads with joined team ownership details for the admin dashboard."""
    from .crm_core import enrich_lead_rows, LEAD_PENDING_DEPARTMENT_SELECT, LEAD_PAYMENT_SELECT, LATEST_OPERATION_REMARK_SELECT, LATEST_OPERATION_REMARK_AT_SELECT, LATEST_OPERATION_REMARK_BY_SELECT
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    current_team_select = """
        CASE
            WHEN p.account_executive IS NOT NULL
                 OR l.status IN ('Ready for Accounts', 'Assigned to Accounts', 'Pending', 'Completed', 'Failed')
                THEN 'Accounts'
            WHEN o.operation_executive IS NOT NULL
                 OR l.status = 'Assigned to Operations'
                THEN 'Operations'
            ELSE 'Marketing'
        END
    """

    current_employee_id_select = f"""
        CASE
            WHEN ({current_team_select}) = 'Accounts' THEN p.account_executive
            WHEN ({current_team_select}) = 'Operations' THEN o.operation_executive
            ELSE l.marketing_executive
        END
    """

    current_employee_name_select = f"""
        CASE
            WHEN ({current_team_select}) = 'Accounts' THEN acc.name
            WHEN ({current_team_select}) = 'Operations' THEN op.name
            ELSE m.name
        END
    """

    query = f"""
        SELECT
            l.id, l.date, l.company_name, l.email, l.auth_person_name,
            l.auth_person_number, l.auth_person_email, l.marketing_executive,
            l.service, l.status, l.account_executive, l.created_at,
            o.file_status, o.client_login, o.client_password, o.filing_date,
            o.operation_executive, o.updated_at AS operation_updated_at,
            o.updated_by AS operation_updated_by,
            p.govt_payment_status, p.professional_payment_status,
            p.total_amount, p.govt_amount, p.professional_amount,
            p.payment_date, p.remarks AS account_remark, p.account_executive,
            p.updated_at AS payment_updated_at, p.updated_by AS payment_updated_by,
            m.name AS marketing_executive_name, op.name AS operation_executive_name,
            acc.name AS account_executive_name, opu.name AS operation_updated_by_name,
            acu.name AS payment_updated_by_name,
            {LATEST_OPERATION_REMARK_SELECT},
            {LATEST_OPERATION_REMARK_AT_SELECT},
            {LATEST_OPERATION_REMARK_BY_SELECT},
            {LEAD_PENDING_DEPARTMENT_SELECT},
            {LEAD_PAYMENT_SELECT},
            ({current_team_select}) AS current_team,
            ({current_employee_id_select}) AS current_employee_id,
            ({current_employee_name_select}) AS current_employee_name
        FROM leads l
        LEFT JOIN operations o ON l.id = o.lead_id
        LEFT JOIN payments p ON l.id = p.lead_id
        LEFT JOIN employees m ON l.marketing_executive = m.id
        LEFT JOIN employees op ON o.operation_executive = op.id
        LEFT JOIN employees acc ON p.account_executive = acc.id
        LEFT JOIN employees opu ON o.updated_by = opu.id
        LEFT JOIN employees acu ON p.updated_by = acu.id
    """

    conditions = []
    params = []

    if team:
        conditions.append(f"({current_team_select}) = %s")
        params.append(team)
    if employee_id:
        conditions.append(f"({current_employee_id_select}) = %s")
        params.append(employee_id)
    if status:
        conditions.append("l.status = %s")
        params.append(status)
    if lead_date:
        conditions.append("DATE(l.date) = %s")
        params.append(lead_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY current_team ASC, current_employee_name ASC, l.created_at DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return enrich_lead_rows(rows)

def get_export_rows(role: str, employee_id: int):
    """Return role-scoped rows ready for CSV export."""
    return get_department_dashboard(role, employee_id)