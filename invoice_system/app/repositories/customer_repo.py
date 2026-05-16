from app.db_compat import DictCursor

from app import mysql

class CustomerRepo:
    @staticmethod
    def _row_to_dict(cur, row):
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        columns = [col[0] for col in cur.description] if cur.description else []
        return dict(zip(columns, row))

    @staticmethod
    def _rows_to_dicts(cur, rows):
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return rows
        columns = [col[0] for col in cur.description] if cur.description else []
        return [dict(zip(columns, row)) for row in rows]

    def _get_customer_columns(self):
        cur = mysql.connection.cursor()
        try:
            cur.execute("SHOW COLUMNS FROM customers")
            return {row[0] for row in cur.fetchall()}
        finally:
            cur.close()

    def _build_customer_insert(self, data):
        available_columns = self._get_customer_columns()
        requested_values = {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "gstin": data.get("gstin", ""),
            "state": data.get("state", ""),
            "state_code": data.get("state_code", ""),
            "address": data.get("address", ""),
        }

        contact_value = data.get("contact", "")
        if "contact" in available_columns:
            requested_values["contact"] = contact_value
        elif "phone" in available_columns:
            requested_values["phone"] = contact_value

        columns = [column for column in requested_values if column in available_columns]
        placeholders = ", ".join(["%s"] * len(columns))
        values = tuple(requested_values[column] for column in columns)
        sql = f"INSERT INTO customers ({', '.join(columns)}) VALUES ({placeholders})"
        return sql, values

    def create(self, data):
        cur = mysql.connection.cursor()
        try:
            sql, values = self._build_customer_insert(data)
            cur.execute(sql, values)
            mysql.connection.commit()
            return {"message": "Customer created"}
        finally:
            cur.close()

    def get_all(self):
        cur = mysql.connection.cursor(DictCursor)
        try:
            cur.execute("SELECT * FROM customers")
            return self._rows_to_dicts(cur, cur.fetchall())
        finally:
            cur.close()

    def get_by_id(self, customer_id):
        cur = mysql.connection.cursor(DictCursor)
        try:
            cur.execute("SELECT * FROM customers WHERE id=%s", (customer_id,))
            return self._row_to_dict(cur, cur.fetchone())
        finally:
            cur.close()

    def delete(self, customer_id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        mysql.connection.commit()
        cur.close()

    def find_by_name_email(self, name, email=None):
        cur = mysql.connection.cursor(DictCursor)
        try:
            if email:
                cur.execute(
                    "SELECT * FROM customers WHERE name=%s AND email=%s LIMIT 1",
                    (name, email),
                )
            else:
                cur.execute(
                    "SELECT * FROM customers WHERE name=%s LIMIT 1",
                    (name,),
                )
            return self._row_to_dict(cur, cur.fetchone())
        finally:
            cur.close()

    def create_and_return_id(self, data):
        cur = mysql.connection.cursor()
        try:
            sql, values = self._build_customer_insert(data)
            cur.execute(sql, values)
            mysql.connection.commit()
            return cur.lastrowid
        finally:
            cur.close()
