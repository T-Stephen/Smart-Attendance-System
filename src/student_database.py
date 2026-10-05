import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3


# ============================================================
# DATABASE PATH
# ============================================================

DATABASE_PATH = "database/attendance.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_db():
    return sqlite3.connect(DATABASE_PATH)


# ============================================================
# CLEAR TREEVIEW
# ============================================================

def clear_tree():

    for row in tree.get_children():
        tree.delete(row)


# ============================================================
# LOAD ALL STUDENTS
# ============================================================

def load_students():

    clear_tree()

    try:

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                student_id,
                student_name,
                department,
                year
            FROM students
            ORDER BY student_id
        """)

        students = cursor.fetchall()

        conn.close()

        for student in students:

            tree.insert(
                "",
                tk.END,
                values=student
            )

        total_label.config(
            text=f"Total Students : {len(students)}"
        )

    except Exception as e:

        messagebox.showerror(
            "Database Error",
            f"Unable to load students.\n\n{e}"
        )


# ============================================================
# SEARCH STUDENTS
# ============================================================

def search_student():

    search_text = search_entry.get().strip()

    clear_tree()

    try:

        conn = connect_db()
        cursor = conn.cursor()

        if search_text == "":

            cursor.execute("""
                SELECT
                    student_id,
                    student_name,
                    department,
                    year
                FROM students
                ORDER BY student_id
            """)

        else:

            search_pattern = f"%{search_text}%"

            cursor.execute("""
                SELECT
                    student_id,
                    student_name,
                    department,
                    year
                FROM students
                WHERE
                    CAST(student_id AS TEXT) LIKE ?
                    OR student_name LIKE ?
                    OR department LIKE ?
                ORDER BY student_id
            """, (
                search_pattern,
                search_pattern,
                search_pattern
            ))

        students = cursor.fetchall()

        conn.close()

        for student in students:

            tree.insert(
                "",
                tk.END,
                values=student
            )

        total_label.config(
            text=f"Students Found : {len(students)}"
        )

    except Exception as e:

        messagebox.showerror(
            "Search Error",
            f"Unable to search students.\n\n{e}"
        )


# ============================================================
# CLEAR SEARCH
# ============================================================

def clear_search():

    search_entry.delete(
        0,
        tk.END
    )

    load_students()

    search_entry.focus()


# ============================================================
# REFRESH TABLE
# ============================================================

def refresh_table():

    clear_edit_fields()

    search_entry.delete(
        0,
        tk.END
    )

    load_students()


# ============================================================
# CLEAR EDIT FIELDS
# ============================================================

def clear_edit_fields():

    name_entry.delete(
        0,
        tk.END
    )

    department_combo.set("")

    year_combo.set("")


# ============================================================
# LOAD SELECTED STUDENT
# ============================================================

def load_selected_student(event=None):

    selected = tree.selection()

    if not selected:
        return

    values = tree.item(
        selected[0],
        "values"
    )

    if not values:
        return

    name_entry.delete(
        0,
        tk.END
    )

    department_combo.set("")

    year_combo.set("")

    name_entry.insert(
        0,
        values[1]
    )

    department_combo.set(
        values[2]
    )

    year_combo.set(
        values[3]
    )


# ============================================================
# ADD STUDENT
# ============================================================

def add_student():

    student_id = add_id_entry.get().strip()
    student_name = add_name_entry.get().strip()
    department = add_department_combo.get().strip()
    year = add_year_combo.get().strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if (
        student_id == ""
        or student_name == ""
        or department == ""
        or year == ""
    ):

        messagebox.showerror(
            "Missing Information",
            "Please fill in all student details."
        )

        return

    # Student ID must contain numbers only

    if not student_id.isdigit():

        messagebox.showerror(
            "Invalid Student ID",
            "Student ID must contain numbers only."
        )

        return

    try:

        conn = connect_db()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # CHECK DUPLICATE ID
        # ----------------------------------------------------

        cursor.execute("""
            SELECT student_id
            FROM students
            WHERE student_id=?
        """, (student_id,))

        existing_student = cursor.fetchone()

        if existing_student:

            conn.close()

            messagebox.showerror(
                "Duplicate Student",
                f"Student ID {student_id} already exists."
            )

            return

        # ----------------------------------------------------
        # INSERT STUDENT
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO students (
                student_id,
                student_name,
                department,
                year
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            student_name,
            department,
            year
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            "Student added successfully."
        )

        # Clear fields

        add_id_entry.delete(
            0,
            tk.END
        )

        add_name_entry.delete(
            0,
            tk.END
        )

        add_department_combo.set("")

        add_year_combo.set("")

        # Refresh table

        load_students()

    except sqlite3.IntegrityError:

        messagebox.showerror(
            "Database Error",
            "Student ID already exists."
        )

    except Exception as e:

        messagebox.showerror(
            "Database Error",
            f"Unable to add student.\n\n{e}"
        )


# ============================================================
# UPDATE STUDENT
# ============================================================

def update_student():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "No Student Selected",
            "Please select a student from the table."
        )

        return

    values = tree.item(
        selected[0],
        "values"
    )

    student_id = values[0]

    new_name = name_entry.get().strip()
    new_department = department_combo.get().strip()
    new_year = year_combo.get().strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if (
        new_name == ""
        or new_department == ""
        or new_year == ""
    ):

        messagebox.showerror(
            "Missing Information",
            "All student fields are required."
        )

        return

    confirm = messagebox.askyesno(
        "Confirm Update",
        f"Update student details?\n\n"
        f"Student ID : {student_id}\n"
        f"Name : {new_name}\n"
        f"Department : {new_department}\n"
        f"Year : {new_year}"
    )

    if not confirm:
        return

    try:

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE students
            SET
                student_name=?,
                department=?,
                year=?
            WHERE student_id=?
        """, (
            new_name,
            new_department,
            new_year,
            student_id
        ))

        conn.commit()

        updated_rows = cursor.rowcount

        conn.close()

        if updated_rows == 0:

            messagebox.showerror(
                "Update Failed",
                "Student could not be updated."
            )

            return

        messagebox.showinfo(
            "Success",
            "Student details updated successfully."
        )

        load_students()

        clear_edit_fields()

    except Exception as e:

        messagebox.showerror(
            "Update Error",
            f"Unable to update student.\n\n{e}"
        )


# ============================================================
# DELETE STUDENT
# ============================================================

def delete_student():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "No Student Selected",
            "Please select a student from the table."
        )

        return

    values = tree.item(
        selected[0],
        "values"
    )

    student_id = values[0]
    student_name = values[1]

    # --------------------------------------------------------
    # CONFIRM DELETE
    # --------------------------------------------------------

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete this student?\n\n"
        f"Student ID : {student_id}\n"
        f"Name : {student_name}\n\n"
        f"All attendance records for this student "
        f"will also be deleted."
    )

    if not confirm:
        return

    try:

        conn = connect_db()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # DELETE ATTENDANCE RECORDS FIRST
        # ----------------------------------------------------

        cursor.execute("""
            DELETE FROM attendance
            WHERE student_id=?
        """, (student_id,))

        deleted_attendance = cursor.rowcount

        # ----------------------------------------------------
        # DELETE STUDENT
        # ----------------------------------------------------

        cursor.execute("""
            DELETE FROM students
            WHERE student_id=?
        """, (student_id,))

        deleted_student = cursor.rowcount

        conn.commit()

        conn.close()

        if deleted_student == 0:

            messagebox.showerror(
                "Delete Failed",
                "Student could not be deleted."
            )

            return

        messagebox.showinfo(
            "Student Deleted",
            f"Student deleted successfully.\n\n"
            f"Student ID : {student_id}\n"
            f"Attendance records deleted : "
            f"{deleted_attendance}"
        )

        clear_edit_fields()

        load_students()

    except Exception as e:

        messagebox.showerror(
            "Delete Error",
            f"Unable to delete student.\n\n{e}"
        )


# ============================================================
# VIEW ATTENDANCE HISTORY
# ============================================================

def view_attendance():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "No Student Selected",
            "Please select a student first."
        )

        return

    values = tree.item(
        selected[0],
        "values"
    )

    student_id = values[0]
    student_name = values[1]

    try:

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                date,
                time,
                confidence,
                status
            FROM attendance
            WHERE student_id=?
            ORDER BY
                substr(date, 7, 4) DESC,
                substr(date, 4, 2) DESC,
                substr(date, 1, 2) DESC,
                time DESC
        """, (student_id,))

        attendance_records = cursor.fetchall()

        conn.close()

    except Exception as e:

        messagebox.showerror(
            "Database Error",
            f"Unable to load attendance history.\n\n{e}"
        )

        return

    # ========================================================
    # ATTENDANCE WINDOW
    # ========================================================

    attendance_window = tk.Toplevel(
        root
    )

    attendance_window.title(
        f"Attendance History - {student_name}"
    )

    attendance_window.geometry(
        "700x520"
    )

    attendance_window.configure(
        bg="#EAF2F8"
    )

    attendance_window.resizable(
        True,
        True
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    tk.Label(
        attendance_window,
        text="ATTENDANCE HISTORY",
        font=("Segoe UI", 20, "bold"),
        bg="#EAF2F8",
        fg="#0B3C5D"
    ).pack(
        pady=(15, 5)
    )

    # --------------------------------------------------------
    # STUDENT INFORMATION
    # --------------------------------------------------------

    info_frame = tk.Frame(
        attendance_window,
        bg="#EAF2F8"
    )

    info_frame.pack(
        pady=5
    )

    tk.Label(
        info_frame,
        text=f"Student ID : {student_id}",
        font=("Segoe UI", 10, "bold"),
        bg="#EAF2F8",
        fg="#34495E"
    ).grid(
        row=0,
        column=0,
        padx=15
    )

    tk.Label(
        info_frame,
        text=f"Student Name : {student_name}",
        font=("Segoe UI", 10, "bold"),
        bg="#EAF2F8",
        fg="#34495E"
    ).grid(
        row=0,
        column=1,
        padx=15
    )

    # --------------------------------------------------------
    # TOTAL ATTENDANCE
    # --------------------------------------------------------

    tk.Label(
        attendance_window,
        text=f"Total Attendance Records : "
             f"{len(attendance_records)}",
        font=("Segoe UI", 11, "bold"),
        bg="#EAF2F8",
        fg="#27AE60"
    ).pack(
        pady=5
    )

    # --------------------------------------------------------
    # TABLE FRAME
    # --------------------------------------------------------

    history_frame = tk.Frame(
        attendance_window,
        bg="#EAF2F8"
    )

    history_frame.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    # --------------------------------------------------------
    # SCROLLBAR
    # --------------------------------------------------------

    history_scrollbar = ttk.Scrollbar(
        history_frame,
        orient="vertical"
    )

    history_scrollbar.pack(
        side="right",
        fill="y"
    )

    # --------------------------------------------------------
    # HISTORY TABLE
    # --------------------------------------------------------

    history_columns = (
        "date",
        "time",
        "confidence",
        "status"
    )

    history_tree = ttk.Treeview(
        history_frame,
        columns=history_columns,
        show="headings",
        yscrollcommand=history_scrollbar.set
    )

    history_scrollbar.config(
        command=history_tree.yview
    )

    history_tree.heading(
        "date",
        text="Date"
    )

    history_tree.heading(
        "time",
        text="Time"
    )

    history_tree.heading(
        "confidence",
        text="Confidence"
    )

    history_tree.heading(
        "status",
        text="Status"
    )

    history_tree.column(
        "date",
        width=150,
        anchor="center"
    )

    history_tree.column(
        "time",
        width=150,
        anchor="center"
    )

    history_tree.column(
        "confidence",
        width=150,
        anchor="center"
    )

    history_tree.column(
        "status",
        width=150,
        anchor="center"
    )

    history_tree.pack(
        fill="both",
        expand=True
    )

    # --------------------------------------------------------
    # INSERT RECORDS
    # --------------------------------------------------------

    for record in attendance_records:

        date_value = record[0]
        time_value = record[1]
        confidence_value = record[2]
        status_value = record[3]

        try:

            confidence_text = (
                f"{float(confidence_value):.2f}%"
            )

        except:

            confidence_text = str(
                confidence_value
            )

        history_tree.insert(
            "",
            tk.END,
            values=(
                date_value,
                time_value,
                confidence_text,
                status_value
            )
        )

    # --------------------------------------------------------
    # CLOSE BUTTON
    # --------------------------------------------------------

    tk.Button(
        attendance_window,
        text="❌ Close",
        width=18,
        bg="#E74C3C",
        fg="white",
        activebackground="#C0392B",
        font=("Segoe UI", 10, "bold"),
        bd=0,
        cursor="hand2",
        command=attendance_window.destroy
    ).pack(
        pady=10
    )


# ============================================================
# DOUBLE CLICK → VIEW ATTENDANCE
# ============================================================

def double_click_attendance(event):

    view_attendance()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Student Database - Smart Attendance System"
)

root.geometry(
    "1050x800"
)

root.minsize(
    950,
    700
)

root.configure(
    bg="#EAF2F8"
)

root.resizable(
    True,
    True
)


# ============================================================
# STYLE
# ============================================================

style = ttk.Style()

try:

    style.theme_use(
        "clam"
    )

except:

    pass


style.configure(
    "Treeview",
    font=("Segoe UI", 10),
    rowheight=30,
    background="white",
    fieldbackground="white"
)

style.configure(
    "Treeview.Heading",
    font=("Segoe UI", 10, "bold")
)

style.map(
    "Treeview",
    background=[
        ("selected", "#D6EAF8")
    ],
    foreground=[
        ("selected", "#0B3C5D")
    ]
)


# ============================================================
# TITLE
# ============================================================

title = tk.Label(
    root,
    text="STUDENT DATABASE",
    font=("Segoe UI", 25, "bold"),
    bg="#EAF2F8",
    fg="#0B3C5D"
)

title.pack(
    pady=(15, 5)
)


tk.Label(
    root,
    text="Student Management • Search • Edit • Attendance History",
    font=("Segoe UI", 10),
    bg="#EAF2F8",
    fg="#5D6D7E"
).pack(
    pady=(0, 10)
)


# ============================================================
# SEARCH FRAME
# ============================================================

search_frame = tk.Frame(
    root,
    bg="#EAF2F8"
)

search_frame.pack(
    pady=5
)


tk.Label(
    search_frame,
    text="Search:",
    font=("Segoe UI", 11, "bold"),
    bg="#EAF2F8",
    fg="#34495E"
).grid(
    row=0,
    column=0,
    padx=5
)


search_entry = tk.Entry(
    search_frame,
    width=30,
    font=("Segoe UI", 11)
)

search_entry.grid(
    row=0,
    column=1,
    padx=5
)


search_button = tk.Button(
    search_frame,
    text="🔍 Search",
    width=14,
    bg="#27AE60",
    fg="white",
    activebackground="#229954",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=search_student
)

search_button.grid(
    row=0,
    column=2,
    padx=5
)


clear_search_button = tk.Button(
    search_frame,
    text="✖ Clear",
    width=12,
    bg="#7F8C8D",
    fg="white",
    activebackground="#707B7C",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=clear_search
)

clear_search_button.grid(
    row=0,
    column=3,
    padx=5
)


# Press Enter to search

search_entry.bind(
    "<Return>",
    lambda event: search_student()
)


# ============================================================
# STUDENT TABLE FRAME
# ============================================================

table_container = tk.Frame(
    root,
    bg="#EAF2F8"
)

table_container.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=10
)


# ============================================================
# TABLE SCROLLBARS
# ============================================================

table_vertical_scrollbar = ttk.Scrollbar(
    table_container,
    orient="vertical"
)

table_vertical_scrollbar.pack(
    side="right",
    fill="y"
)


table_horizontal_scrollbar = ttk.Scrollbar(
    table_container,
    orient="horizontal"
)

table_horizontal_scrollbar.pack(
    side="bottom",
    fill="x"
)


# ============================================================
# STUDENT TABLE
# ============================================================

columns = (
    "Student ID",
    "Student Name",
    "Department",
    "Year"
)


tree = ttk.Treeview(
    table_container,
    columns=columns,
    show="headings",
    yscrollcommand=table_vertical_scrollbar.set,
    xscrollcommand=table_horizontal_scrollbar.set,
    selectmode="browse"
)


table_vertical_scrollbar.config(
    command=tree.yview
)

table_horizontal_scrollbar.config(
    command=tree.xview
)


# ============================================================
# TABLE HEADINGS
# ============================================================

tree.heading(
    "Student ID",
    text="Student ID"
)

tree.heading(
    "Student Name",
    text="Student Name"
)

tree.heading(
    "Department",
    text="Department"
)

tree.heading(
    "Year",
    text="Year"
)


# ============================================================
# TABLE COLUMN WIDTHS
# ============================================================

tree.column(
    "Student ID",
    width=180,
    minwidth=130,
    anchor="center"
)

tree.column(
    "Student Name",
    width=250,
    minwidth=180,
    anchor="center"
)

tree.column(
    "Department",
    width=220,
    minwidth=150,
    anchor="center"
)

tree.column(
    "Year",
    width=150,
    minwidth=100,
    anchor="center"
)


tree.pack(
    fill="both",
    expand=True
)


# Select student

tree.bind(
    "<<TreeviewSelect>>",
    load_selected_student
)


# Double-click student

tree.bind(
    "<Double-1>",
    double_click_attendance
)


# ============================================================
# ADD STUDENT FRAME
# ============================================================

add_frame = tk.LabelFrame(
    root,
    text="ADD NEW STUDENT",
    font=("Segoe UI", 11, "bold"),
    bg="#EAF2F8",
    fg="#0B3C5D",
    padx=10,
    pady=8
)

add_frame.pack(
    fill="x",
    padx=25,
    pady=5
)


# Student ID

tk.Label(
    add_frame,
    text="Student ID",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=0,
    padx=8,
    pady=5
)


add_id_entry = tk.Entry(
    add_frame,
    width=18,
    font=("Segoe UI", 10)
)

add_id_entry.grid(
    row=0,
    column=1,
    padx=8
)


# Name

tk.Label(
    add_frame,
    text="Name",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=2,
    padx=8
)


add_name_entry = tk.Entry(
    add_frame,
    width=25,
    font=("Segoe UI", 10)
)

add_name_entry.grid(
    row=0,
    column=3,
    padx=8
)


# Department

tk.Label(
    add_frame,
    text="Department",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=4,
    padx=8
)


departments = [
    "AI & DS",
    "CSE",
    "ECE",
    "EEE",
    "B.Com",
    "MECH",
    "CIVIL",
    "IT"
]


add_department_combo = ttk.Combobox(
    add_frame,
    values=departments,
    width=17,
    state="readonly"
)

add_department_combo.grid(
    row=0,
    column=5,
    padx=8
)


# Year

tk.Label(
    add_frame,
    text="Year",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=6,
    padx=8
)


years = [
    "I",
    "II",
    "III",
    "IV"
]


add_year_combo = ttk.Combobox(
    add_frame,
    values=years,
    width=8,
    state="readonly"
)

add_year_combo.grid(
    row=0,
    column=7,
    padx=8
)


# Add button

tk.Button(
    add_frame,
    text="➕ Add Student",
    width=16,
    bg="#2980B9",
    fg="white",
    activebackground="#2471A3",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=add_student
).grid(
    row=0,
    column=8,
    padx=12
)


# ============================================================
# EDIT STUDENT FRAME
# ============================================================

edit_frame = tk.LabelFrame(
    root,
    text="EDIT SELECTED STUDENT",
    font=("Segoe UI", 11, "bold"),
    bg="#EAF2F8",
    fg="#0B3C5D",
    padx=10,
    pady=8
)

edit_frame.pack(
    fill="x",
    padx=25,
    pady=5
)


# Name

tk.Label(
    edit_frame,
    text="Name",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=0,
    padx=8
)


name_entry = tk.Entry(
    edit_frame,
    width=25,
    font=("Segoe UI", 10)
)

name_entry.grid(
    row=0,
    column=1,
    padx=8
)


# Department

tk.Label(
    edit_frame,
    text="Department",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=2,
    padx=8
)


department_combo = ttk.Combobox(
    edit_frame,
    values=departments,
    width=17,
    state="readonly"
)

department_combo.grid(
    row=0,
    column=3,
    padx=8
)


# Year

tk.Label(
    edit_frame,
    text="Year",
    font=("Segoe UI", 9, "bold"),
    bg="#EAF2F8"
).grid(
    row=0,
    column=4,
    padx=8
)


year_combo = ttk.Combobox(
    edit_frame,
    values=years,
    width=8,
    state="readonly"
)

year_combo.grid(
    row=0,
    column=5,
    padx=8
)


# ============================================================
# TOTAL STUDENTS LABEL
# ============================================================

total_label = tk.Label(
    root,
    text="Total Students : 0",
    font=("Segoe UI", 11, "bold"),
    bg="#EAF2F8",
    fg="#27AE60"
)

total_label.pack(
    pady=5
)


# ============================================================
# BUTTON FRAME
# ============================================================

button_frame = tk.Frame(
    root,
    bg="#EAF2F8"
)

button_frame.pack(
    pady=8
)


# Refresh

tk.Button(
    button_frame,
    text="🔄 Refresh",
    width=17,
    bg="#3498DB",
    fg="white",
    activebackground="#2980B9",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=refresh_table
).grid(
    row=0,
    column=0,
    padx=6
)


# Update

tk.Button(
    button_frame,
    text="💾 Update Student",
    width=18,
    bg="#27AE60",
    fg="white",
    activebackground="#229954",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=update_student
).grid(
    row=0,
    column=1,
    padx=6
)


# Delete

tk.Button(
    button_frame,
    text="🗑 Delete Student",
    width=18,
    bg="#F39C12",
    fg="white",
    activebackground="#D68910",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=delete_student
).grid(
    row=0,
    column=2,
    padx=6
)


# Attendance

tk.Button(
    button_frame,
    text="📋 View Attendance",
    width=18,
    bg="#8E44AD",
    fg="white",
    activebackground="#7D3C98",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=view_attendance
).grid(
    row=0,
    column=3,
    padx=6
)


# Close

tk.Button(
    button_frame,
    text="❌ Close",
    width=14,
    bg="#E74C3C",
    fg="white",
    activebackground="#C0392B",
    font=("Segoe UI", 10, "bold"),
    bd=0,
    cursor="hand2",
    command=root.destroy
).grid(
    row=0,
    column=4,
    padx=6
)


# ============================================================
# FOOTER
# ============================================================

tk.Label(
    root,
    text="Smart Attendance System • SQLite Student Management",
    font=("Segoe UI", 8),
    bg="#EAF2F8",
    fg="#777777"
).pack(
    pady=5
)


# ============================================================
# INITIAL LOAD
# ============================================================

load_students()


# ============================================================
# START APPLICATION
# ============================================================

root.mainloop()