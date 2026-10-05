import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DATABASE_PATH = "database/attendance.db"


# =====================================================
# DATABASE
# =====================================================

def connect_db():
    return sqlite3.connect(DATABASE_PATH)


# =====================================================
# LOAD ATTENDANCE
# =====================================================

def load_attendance(records=None):

    for row in tree.get_children():
        tree.delete(row)

    if records is None:

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            student_id,
            student_name,
            department,
            year,
            date,
            time,
            confidence,
            status
        FROM attendance
        ORDER BY date DESC,time DESC
        """)

        records = cursor.fetchall()
        conn.close()

    for record in records:
        tree.insert("", tk.END, values=record)

    total_label.config(
        text=f"Total Records : {len(records)}"
    )


# =====================================================
# SEARCH
# =====================================================

def search_attendance():

    student_id = id_entry.get().strip()
    date = date_entry.get().strip()

    conn = connect_db()
    cursor = conn.cursor()

    query = """
    SELECT
        student_id,
        student_name,
        department,
        year,
        date,
        time,
        confidence,
        status
    FROM attendance
    WHERE 1=1
    """

    params = []

    if student_id:
        query += " AND student_id LIKE ?"
        params.append(f"%{student_id}%")

    if date:
        query += " AND date=?"
        params.append(date)

    query += " ORDER BY date DESC,time DESC"

    cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    load_attendance(rows)


# =====================================================
# DELETE RECORD
# =====================================================

def delete_record():

    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a record."
        )
        return

    values = tree.item(selected[0], "values")

    if not messagebox.askyesno(
        "Confirm",
        f"Delete attendance of {values[1]}?"
    ):
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM attendance
    WHERE student_id=?
    AND date=?
    AND time=?
    """, (
        values[0],
        values[4],
        values[5]
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Attendance record deleted successfully."
    )

    refresh()


# =====================================================
# REFRESH
# =====================================================

def refresh():

    id_entry.delete(0, tk.END)
    date_entry.delete(0, tk.END)

    load_attendance()


# =====================================================
# WINDOW
# =====================================================

root = tk.Tk()

root.title("Attendance Database")

root.geometry("1250x720")

root.configure(bg="#EAF2F8")

root.resizable(False, False)


# =====================================================
# TITLE
# =====================================================

title = tk.Label(
    root,
    text="ATTENDANCE DATABASE",
    font=("Segoe UI",24,"bold"),
    bg="#EAF2F8",
    fg="#0B3C5D"
)

title.pack(pady=15)


# =====================================================
# SEARCH FRAME
# =====================================================

search_frame = tk.Frame(
    root,
    bg="#EAF2F8"
)

search_frame.pack(pady=10)

tk.Label(
    search_frame,
    text="Student ID",
    font=("Segoe UI",11,"bold"),
    bg="#EAF2F8"
).grid(row=0,column=0,padx=5)

id_entry = tk.Entry(
    search_frame,
    width=20,
    font=("Segoe UI",11)
)

id_entry.grid(row=0,column=1,padx=10)

tk.Label(
    search_frame,
    text="Date (DD-MM-YYYY)",
    font=("Segoe UI",11,"bold"),
    bg="#EAF2F8"
).grid(row=0,column=2,padx=5)

date_entry = tk.Entry(
    search_frame,
    width=18,
    font=("Segoe UI",11)
)

date_entry.grid(row=0,column=3,padx=10)

tk.Button(
    search_frame,
    text="🔍 Search",
    bg="#27AE60",
    fg="white",
    font=("Segoe UI",11,"bold"),
    width=15,
    command=search_attendance
).grid(row=0,column=4,padx=10)


# =====================================================
# TABLE
# =====================================================

columns = (
    "Student ID",
    "Student Name",
    "Department",
    "Year",
    "Date",
    "Time",
    "Confidence",
    "Status"
)

tree = ttk.Treeview(
    root,
    columns=columns,
    show="headings",
    height=18
)

for column in columns:

    tree.heading(column, text=column)

    tree.column(
        column,
        anchor="center",
        width=140
    )

tree.pack(pady=15)


# =====================================================
# TOTAL
# =====================================================

total_label = tk.Label(
    root,
    text="Total Records : 0",
    font=("Segoe UI",12,"bold"),
    bg="#EAF2F8",
    fg="green"
)

total_label.pack()


# =====================================================
# BUTTONS
# =====================================================

button_frame = tk.Frame(
    root,
    bg="#EAF2F8"
)

button_frame.pack(pady=20)

tk.Button(
    button_frame,
    text="🔄 Refresh",
    width=18,
    bg="#3498DB",
    fg="white",
    font=("Segoe UI",11,"bold"),
    command=refresh
).grid(row=0,column=0,padx=10)

tk.Button(
    button_frame,
    text="🗑 Delete Attendance",
    width=18,
    bg="#F39C12",
    fg="white",
    font=("Segoe UI",11,"bold"),
    command=delete_record
).grid(row=0,column=1,padx=10)

tk.Button(
    button_frame,
    text="❌ Close",
    width=18,
    bg="#E74C3C",
    fg="white",
    font=("Segoe UI",11,"bold"),
    command=root.destroy
).grid(row=0,column=2,padx=10)


# =====================================================
# INITIAL LOAD
# =====================================================

load_attendance()

root.mainloop()