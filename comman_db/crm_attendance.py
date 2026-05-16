from typing import List, Dict, Optional
from datetime import datetime
from calendar import monthrange
from .crm_core import get_db_connection

# =========================================================
# ATTENDANCE MANAGEMENT
# =========================================================

def mark_attendance(employee_id: int, date: str, status: str, check_in_time: str = None,
                   check_out_time: str = None, working_hours: float = None,
                   remarks: str = None, marked_by: int = None):
    """Mark attendance for an employee on a specific date."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO attendance
            (employee_id, date, status, check_in_time, check_out_time, working_hours, remarks, marked_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            check_in_time = VALUES(check_in_time),
            check_out_time = VALUES(check_out_time),
            working_hours = VALUES(working_hours),
            remarks = VALUES(remarks),
            marked_by = VALUES(marked_by),
            updated_at = CURRENT_TIMESTAMP
        """, (employee_id, date, status, check_in_time, check_out_time, working_hours, remarks, marked_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_attendance_records(date: str = None, employee_id: int = None, month: str = None, year: str = None):
    """Get attendance records with optional filters."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT a.*, e.name as employee_name, e.department, e.role,
               m.name as marked_by_name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN employees m ON a.marked_by = m.id
    """
    conditions = []
    params = []
    if date:
        conditions.append("a.date = %s")
        params.append(date)
    if employee_id:
        conditions.append("a.employee_id = %s")
        params.append(employee_id)
    if month and year:
        conditions.append("MONTH(a.date) = %s AND YEAR(a.date) = %s")
        params.extend([month, year])
    elif year:
        conditions.append("YEAR(a.date) = %s")
        params.append(year)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.date DESC, e.name ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def ensure_attendance_records_for_date(target_date: str, marked_by: int = None):
    """Ensure every employee has an attendance row for the date, defaulting to absent."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur2 = conn.cursor()
    try:
        cur.execute("SELECT id FROM employees")
        employees = cur.fetchall()
        for employee in employees:
            cur2.execute("""
                INSERT INTO attendance (employee_id, date, status, marked_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = status
            """, (employee["id"], target_date, "absent", marked_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur2.close()
        cur.close()
        conn.close()

def get_employee_attendance_summary(employee_id: int, month: int, year: int):
    """Get attendance summary for an employee for a specific month."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            COUNT(*) as total_days,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days,
            SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_days,
            SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_days,
            SUM(CASE WHEN status = 'half_day' THEN 1 ELSE 0 END) as half_days,
            SUM(working_hours) as total_hours
        FROM attendance
        WHERE employee_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
    """, (employee_id, month, year))
    summary = cur.fetchone()
    cur.close()
    conn.close()
    return summary

# =========================================================
# LEAVE MANAGEMENT
# =========================================================

def submit_leave_request(employee_id: int, leave_type: str, start_date: str, end_date: str,
                        reason: str, total_days: int = None):
    """Submit a leave request."""
    if total_days is None:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        total_days = (end - start).days + 1
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO leave_requests
            (employee_id, leave_type, start_date, end_date, total_days, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (employee_id, leave_type, start_date, end_date, total_days, reason))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def update_leave_status(leave_id: int, status: str, approved_by: int, remarks: str = None):
    """Update leave request status."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE leave_requests
            SET status = %s, approved_by = %s, approved_on = CURRENT_TIMESTAMP, remarks = %s
            WHERE id = %s
        """, (status, approved_by, remarks, leave_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_leave_requests(employee_id: int = None, status: str = None):
    """Get leave requests with optional filters."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT lr.*, e.name as employee_name, e.department, e.role,
               a.name as approved_by_name
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        LEFT JOIN employees a ON lr.approved_by = a.id
    """
    conditions = []
    params = []
    if employee_id:
        conditions.append("lr.employee_id = %s")
        params.append(employee_id)
    if status:
        conditions.append("lr.status = %s")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY lr.applied_on DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_pending_leave_requests(employee_id: int = None):
    """Convenience helper for pending leave requests."""
    return get_leave_requests(employee_id=employee_id, status="pending")

def get_employee_leave_balance(employee_id: int):
    """Get leave balance for an employee."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    current_year = datetime.now().year
    cur.execute("""
        SELECT
            SUM(CASE WHEN leave_type = 'casual' AND status = 'approved' THEN total_days ELSE 0 END) as used_casual,
            SUM(CASE WHEN leave_type = 'sick' AND status = 'approved' THEN total_days ELSE 0 END) as used_sick,
            SUM(CASE WHEN leave_type = 'annual' AND status = 'approved' THEN total_days ELSE 0 END) as used_annual
        FROM leave_requests
        WHERE employee_id = %s AND YEAR(start_date) = %s AND status = 'approved'
    """, (employee_id, current_year))
    used_leaves = cur.fetchone()
    balances = {
        'casual': 12 - (used_leaves['used_casual'] or 0),
        'sick': 6 - (used_leaves['used_sick'] or 0),
        'annual': 20 - (used_leaves['used_annual'] or 0)
    }
    cur.close()
    conn.close()
    return balances

# =========================================================
# PAYROLL AND HOLIDAY MANAGEMENT
# =========================================================

def upsert_employee_salary(employee_id: int, monthly_salary: float, effective_from: str, updated_by: int = None):
    """Create or update salary settings for an employee."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO employee_salary_settings (employee_id, monthly_salary, effective_from, updated_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                monthly_salary = VALUES(monthly_salary),
                effective_from = VALUES(effective_from),
                updated_by = VALUES(updated_by),
                updated_at = CURRENT_TIMESTAMP
        """, (employee_id, monthly_salary, effective_from, updated_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_employee_salary_settings(employee_id: int = None):
    """Fetch salary settings with employee metadata."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT s.*, e.name AS employee_name, e.department, e.role
        FROM employee_salary_settings s
        JOIN employees e ON e.id = s.employee_id
    """
    params = []
    if employee_id:
        query += " WHERE s.employee_id = %s"
        params.append(employee_id)
    query += " ORDER BY e.name ASC"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_holiday(holiday_date: str, title: str, description: str = None, created_by: int = None):
    """Create or update a holiday by date."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO holidays (holiday_date, title, description, created_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                created_by = VALUES(created_by)
        """, (holiday_date, title, description, created_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_holidays(start_date: str = None, end_date: str = None):
    """Fetch holidays optionally filtered by date range."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
        SELECT h.*, e.name AS created_by_name
        FROM holidays h
        LEFT JOIN employees e ON e.id = h.created_by
    """
    conditions = []
    params = []
    if start_date:
        conditions.append("h.holiday_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("h.holiday_date <= %s")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY h.holiday_date ASC"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def delete_holiday(holiday_id: int):
    """Delete a holiday by ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM holidays WHERE id = %s", (holiday_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_payroll_report(month: int, year: int, employee_id: int = None):
    """Generate payroll rows based on attendance and configured monthly salary."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    attendance_cur = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT e.id AS employee_id, e.name AS employee_name, e.department, e.role,
                   s.monthly_salary, s.effective_from
            FROM employees e
            LEFT JOIN employee_salary_settings s ON s.employee_id = e.id
        """
        params = []
        if employee_id:
            query += " WHERE e.id = %s"
            params.append(employee_id)
        query += " ORDER BY e.name ASC"
        cur.execute(query, tuple(params))
        employees = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS holiday_count FROM holidays WHERE MONTH(holiday_date) = %s AND YEAR(holiday_date) = %s", (month, year))
        holiday_row = cur.fetchone() or {"holiday_count": 0}
        holiday_count = int(holiday_row.get("holiday_count") or 0)
        days_in_month = monthrange(year, month)[1]
        working_days = max(days_in_month - holiday_count, 0)
        report = []
        for employee in employees:
            attendance_cur.execute("""
                SELECT
                    SUM(CASE WHEN a.status IN ('present', 'late') THEN 1 WHEN a.status = 'half_day' THEN 0.5 ELSE 0 END) AS paid_days,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present_days,
                    SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) AS late_days,
                    SUM(CASE WHEN a.status = 'half_day' THEN 1 ELSE 0 END) AS half_days
                FROM attendance a
                WHERE a.employee_id = %s
                  AND MONTH(a.date) = %s
                  AND YEAR(a.date) = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM holidays h WHERE h.holiday_date = a.date
                  )
            """, (employee["employee_id"], month, year))
            attendance = attendance_cur.fetchone() or {}
            paid_days = float(attendance.get("paid_days") or 0)
            paid_days = min(paid_days, float(working_days))
            absent_days = max(float(working_days) - paid_days, 0)
            monthly_salary = float(employee.get("monthly_salary") or 0)
            per_day_salary = (monthly_salary / working_days) if working_days > 0 else 0
            net_salary = round(per_day_salary * paid_days, 2)
            deduction = round(monthly_salary - net_salary, 2) if monthly_salary else 0
            report.append({
                "employee_id": employee["employee_id"],
                "employee_name": employee["employee_name"],
                "department": employee["department"],
                "role": employee["role"],
                "monthly_salary": monthly_salary,
                "effective_from": employee.get("effective_from"),
                "days_in_month": days_in_month,
                "holiday_count": holiday_count,
                "working_days": working_days,
                "present_days": int(attendance.get("present_days") or 0),
                "late_days": int(attendance.get("late_days") or 0),
                "half_days": int(attendance.get("half_days") or 0),
                "paid_days": round(paid_days, 2),
                "absent_days": round(absent_days, 2),
                "deduction": deduction,
                "net_salary": net_salary,
            })
        return report
    finally:
        attendance_cur.close()
        cur.close()
        conn.close()