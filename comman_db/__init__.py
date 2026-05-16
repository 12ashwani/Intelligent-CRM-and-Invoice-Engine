# Expose commonly used functions for easy import
from .crm_core import *

from .crm_employees import (
    insert_employee, get_all_employees, get_employees_by_department,is_username_taken,update_user_theme,
    get_user_for_login, save_user_credentials, get_user_by_identifier, get_user_credentials, 
     get_employee_by_id,update_employee,delete_employee,
    update_user_password,create_default_admin
)
# FROM CRM LEADS
from .crm_leads import (
    create_lead,get_all_leads,get_lead_by_id,
    update_lead_status,get_scoped_lead,return_lead_to_previous_stage
)

# from .crm_operations import assign_to_operations, update_operation, add_operation_remark, get_operation_by_lead_id, get_operation_remarks

from .crm_operations import( assign_to_operations, update_operation,add_operation_remark
   , get_operation_by_lead_id, get_operation_remarks

)
# from .crm_tasks import create_task, get_tasks_by_lead_id, update_task_status, delete_task
from .crm_payments import *

from .crm_attendance import (
    mark_attendance, get_attendance_records, submit_leave_request,update_leave_status,get_pending_leave_requests,
    get_payroll_report, add_holiday, get_holidays, get_leave_requests
    ,ensure_attendance_records_for_date,get_employee_attendance_summary,get_employee_leave_balance
    ,upsert_employee_salary,get_employee_salary_settings,delete_holiday
)
from .invoice import (generate_invoice_number,delete_invoice,add_invoice_payment,get_invoice_payments,
    create_invoice, get_invoice_by_id, get_all_invoices,
    update_invoice_status, get_company_settings_for_invoice,update_company_settings
)
from .crm_tables import (create_tables,get_department_dashboard,get_admin_leads_overview,get_export_rows
)
# Optional: expose a function to create all tables
#from .migrations import create_tables