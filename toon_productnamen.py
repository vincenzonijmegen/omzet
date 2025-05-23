import sqlite3
import pandas as pd

conn = sqlite3.connect("sales_data.db")
df = pd.read_sql_query("SELECT DISTINCT product FROM sales ORDER BY product", conn)
conn.close()

# Print de eerste 100 unieke productnamen
print(df.head(100).to_string(index=False))
