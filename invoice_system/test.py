from app import create_app
from app.db import MySQLConnection

app = create_app()
# check DB connection on startup
try:
    with MySQLConnection(app).connection as conn:
        print("✅ Database connected successfully")
except Exception as e:
    print("❌ DB Error:", e)

if __name__ == "__main__":
    app.run(
        debug=False,
        host=app.config["APP_HOST"],
        port=app.config["APP_PORT"],
    )