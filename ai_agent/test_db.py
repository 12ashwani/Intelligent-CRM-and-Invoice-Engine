from ai_agent.db.mysql import get_connection

try:
    conn = get_connection()
    print("✅ Database connected successfully")
    conn.close()
except Exception as e:
    print("❌ DB Error:", e)