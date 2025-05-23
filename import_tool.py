import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import sqlite3
import os
import re

DB_NAME = "sales_data.db"
TABLE_NAME = "sales"

# Zorg dat de tabel bestaat
def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT NOT NULL,
            tijdstip TEXT NOT NULL,
            product TEXT NOT NULL,
            aantal INTEGER NOT NULL,
            verkoopprijs REAL NOT NULL,
            jaar INTEGER NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

def import_csv(file_path):
    try:
        jaar_match = re.search(r"(\d{4})", os.path.basename(file_path))
        if not jaar_match:
            raise ValueError("Kon geen jaartal vinden in de bestandsnaam.")
        jaar = int(jaar_match.group(1))

        chunks = pd.read_csv(file_path, sep=";", usecols=["datum", "tijdstip", "product", "aantal", "verkoopprijs"], chunksize=1000)

        conn = sqlite3.connect(DB_NAME)
        total_inserted = 0
        for chunk in chunks:
            chunk.columns = chunk.columns.str.strip()
            chunk["verkoopprijs"] = chunk["verkoopprijs"].astype(str).str.replace(",", ".", regex=False)
            chunk["verkoopprijs"] = pd.to_numeric(chunk["verkoopprijs"], errors="coerce")
            chunk["aantal"] = pd.to_numeric(chunk["aantal"], errors="coerce").fillna(0).astype(int)
            chunk["jaar"] = jaar
            chunk.dropna(subset=["datum", "tijdstip", "product", "verkoopprijs"], inplace=True)
            chunk.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
            total_inserted += len(chunk)

        conn.close()
        return total_inserted
    except Exception as e:
        raise e

def clear_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME};")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise e

def view_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} LIMIT 100", conn)
        conn.close()
        return df
    except Exception as e:
        raise e

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV bestanden", "*.csv")])
    if not file_path:
        return
    try:
        inserted = import_csv(file_path)
        messagebox.showinfo("Succes", f"Gegevens succesvol geïmporteerd. {inserted} rijen toegevoegd.")
        df = view_data()
        update_tree(df)
    except Exception as e:
        messagebox.showerror("Fout", str(e))

def leeg_database():
    try:
        if messagebox.askyesno("Bevestigen", "Weet je zeker dat je alle data wilt verwijderen?"):
            clear_database()
            update_tree(pd.DataFrame())
            messagebox.showinfo("Succes", "Database geleegd.")
    except Exception as e:
        messagebox.showerror("Fout", str(e))

def update_tree(df):
    for item in tree.get_children():
        tree.delete(item)
    if df.empty:
        return
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

# GUI setup
create_database()
root = tk.Tk()
root.title("Omzet Import Tool")
root.geometry("900x500")

frame = tk.Frame(root)
frame.pack(pady=10)

btn_select = tk.Button(frame, text="CSV importeren", command=select_file)
btn_select.grid(row=0, column=0, padx=10)

btn_leeg = tk.Button(frame, text="Database legen", command=leeg_database)
btn_leeg.grid(row=0, column=1, padx=10)

btn_exit = tk.Button(frame, text="Afsluiten", command=root.quit)
btn_exit.grid(row=0, column=2, padx=10)

# Treeview voor dataweergave
tree = ttk.Treeview(root)
tree.pack(expand=True, fill="both")

root.mainloop()
