from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash
from .crm_core import get_db_connection, fetchall_dict

# =========================================================
# EMPLOYEE MANAGEMENT
# =========================================================

def insert_employee(name: str, email: str, phone: str, department: str, role: str):
    """Add a new employee."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO employees (name, email, phone, department, role)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, phone, department, role))
    conn.commit()
    cur.close()
    conn.close()

def get_all_employees() -> List[Dict]:
    """Retrieve all employees."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees ORDER BY id DESC")
    rows = fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows

def get_employees_by_department(department: str) -> List[Dict]:
    """Get employees filtered by department."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM employees WHERE department=%s", (department,))
    rows = fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows

def get_employee_by_id(employee_id: int) -> Optional[Dict]:
    """Get a single employee by ID."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_employee(employee_id: int, name: str, email: str, phone: str, department: str, role: str):
    """Update employee details."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE employees 
        SET name=%s, email=%s, phone=%s, department=%s, role=%s
        WHERE id=%s
    """, (name, email, phone, department, role, employee_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_employee(employee_id: int):
    """Delete an employee."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (employee_id,))
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# USER AUTHENTICATION & CREDENTIALS
# =========================================================

def get_user_for_login(username: str):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.*, COALESCE(u.department, e.department) AS department, e.name AS employee_name
        FROM users u
        LEFT JOIN employees e ON e.id = u.employee_id
        WHERE u.username = %s
        LIMIT 1
    """, (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_identifier(identifier: str):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if identifier.isdigit():
        cur.execute("""
            SELECT u.*, COALESCE(u.department, e.department) AS department, e.name AS employee_name
            FROM users u
            LEFT JOIN employees e ON e.id = u.employee_id
            WHERE u.username = %s OR u.employee_id = %s
            ORDER BY u.id ASC
            LIMIT 1
        """, (identifier, int(identifier)))
    else:
        cur.execute("""
            SELECT u.*, COALESCE(u.department, e.department) AS department, e.name AS employee_name
            FROM users u
            LEFT JOIN employees e ON e.id = u.employee_id
            WHERE u.username = %s
            LIMIT 1
        """, (identifier,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_credentials(employee_id: int):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            e.id AS employee_id,
            e.name,
            e.email,
            e.department,
            e.role AS employee_role,
            u.id AS user_id,
            u.username,
            u.role AS user_role,
            u.is_active
        FROM employees e
        LEFT JOIN users u ON u.employee_id = e.id
        WHERE e.id = %s
        LIMIT 1
    """, (employee_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def is_username_taken(username: str, exclude_user_id: Optional[int] = None) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    if exclude_user_id:
        cur.execute(
            "SELECT id FROM users WHERE username = %s AND id != %s LIMIT 1",
            (username, exclude_user_id)
        )
    else:
        cur.execute(
            "SELECT id FROM users WHERE username = %s LIMIT 1",
            (username,)
        )
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def update_user_password(user_id: int, password_hash: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password = %s WHERE id = %s",
        (password_hash, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def save_user_credentials(employee_id: int, username: str, role: str, password_hash: Optional[str] = None,
                          is_active: bool = True):
    conn = get_db_connection()
    lookup_cur = conn.cursor(dictionary=True)
    lookup_cur.execute("SELECT id FROM users WHERE employee_id = %s LIMIT 1", (employee_id,))
    existing = lookup_cur.fetchone()
    lookup_cur.close()

    write_cur = conn.cursor()
    if existing:
        user_id = existing["id"]
        if password_hash:
            write_cur.execute("""
                UPDATE users
                SET username = %s, role = %s, password = %s, is_active = %s
                WHERE id = %s
            """, (username, role, password_hash, int(is_active), user_id))
        else:
            write_cur.execute("""
                UPDATE users
                SET username = %s, role = %s, is_active = %s
                WHERE id = %s
            """, (username, role, int(is_active), user_id))
    else:
        if not password_hash:
            write_cur.close()
            conn.close()
            raise ValueError("Password is required to create a login account.")
        write_cur.execute("""
            INSERT INTO users (username, password, role, employee_id, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password_hash, role, employee_id, int(is_active)))
    conn.commit()
    write_cur.close()
    conn.close()

def update_user_theme(user_id: int, theme: str):
    """Update user's theme preference."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET theme = %s WHERE id = %s", (theme, user_id))
    conn.commit()
    cur.close()
    conn.close()

def create_default_admin():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username='admin'")
    admin_user = cur.fetchone()
    hashed_password = generate_password_hash("admin123")
    if admin_user:
        existing_password = admin_user["password"]
        if existing_password == "admin123":
            cur.execute("UPDATE users SET password=%s WHERE username='admin'", (hashed_password,))
            conn.commit()
            print("✅ Admin password updated to hashed admin123")
        else:
            print("Admin already exists")
        cur.close()
        conn.close()
        return
    cur.execute("""
        INSERT INTO employees (name, email, phone, department, role)
        VALUES (%s, %s, %s, %s, %s)
    """, ("Admin User", "admin@example.com", "9999999999", "admin", "admin"))
    employee_id = cur.lastrowid
    cur.execute("""
        INSERT INTO users (username, password, role, employee_id)
        VALUES (%s, %s, %s, %s)
    """, ("admin", hashed_password, "admin", employee_id))
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Admin created: admin / admin123")