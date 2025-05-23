import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "sales_data.db")

def leeg_database_dashboard():
    print(f"🔄 Verbind met: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales;")  # Verwijder ALLE records
    conn.commit()
    conn.close()
    print("✅ Alle salesdata is gewist uit de juiste database!")

if __name__ == "__main__":
    leeg_database_dashboard()
