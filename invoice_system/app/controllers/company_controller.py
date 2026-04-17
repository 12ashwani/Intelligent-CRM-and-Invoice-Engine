import os
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request
from werkzeug.utils import secure_filename

from app import mysql

company_bp = Blueprint("company", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@company_bp.route("/company", methods=["GET", "POST"])
def company_settings():
    cur = mysql.connection.cursor()

    if request.method == "POST":
        name = request.form["name"]
        gstin = request.form["gstin"]
        address = request.form["address"]
        bank_account = request.form.get("bank_account", "")
        bank_name = request.form.get("bank_name", "")
        ifsc_code = request.form.get("ifsc_code", "")

        file = request.files.get("logo")
        filename = None

        if file and file.filename and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            name_part, ext = os.path.splitext(original_filename)
            filename = f"{name_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        cur.execute("SELECT * FROM company_settings LIMIT 1")
        existing = cur.fetchone()

        try:
            if existing:
                cur.execute(
                    """
                    UPDATE company_settings
                    SET name=%s, gstin=%s, address=%s, logo_path=%s, bank_account=%s, bank_name=%s, ifsc_code=%s
                    WHERE id=%s
                    """,
                    (
                        name,
                        gstin,
                        address,
                        filename if filename else existing[4],
                        bank_account,
                        bank_name,
                        ifsc_code,
                        existing[0],
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO company_settings (name, gstin, address, logo_path, bank_account, bank_name, ifsc_code)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (name, gstin, address, filename, bank_account, bank_name, ifsc_code),
                )
        except Exception as e:
            if "Unknown column" in str(e):
                try:
                    if existing:
                        cur.execute(
                            """
                            UPDATE company_settings
                            SET name=%s, gstin=%s, address=%s, logo_path=%s
                            WHERE id=%s
                            """,
                            (name, gstin, address, filename if filename else existing[4], existing[0]),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO company_settings (name, gstin, address, logo_path)
                            VALUES (%s,%s,%s,%s)
                            """,
                            (name, gstin, address, filename),
                        )

                    flash(
                        "Settings saved, but bank details columns were not found in the database. Please run the migrations.",
                        "warning",
                    )
                except Exception as inner_error:
                    mysql.connection.rollback()
                    flash(f"Error saving company settings: {inner_error}", "danger")
                    return redirect("/company")
            else:
                mysql.connection.rollback()
                flash(f"Error saving company settings: {e}", "danger")
                return redirect("/company")

        mysql.connection.commit()
        flash("Company settings saved successfully.", "success")
        return redirect("/company")

    cur.execute("SELECT * FROM company_settings LIMIT 1")
    company = cur.fetchone()

    return render_template("company/settings.html", company=company)
