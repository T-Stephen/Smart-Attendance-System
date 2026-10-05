import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "attendance.db"
)


# ============================================================
# REGISTER STUDENT WINDOW
# ============================================================

class RegisterStudentWindow:

    def __init__(self, parent):

        self.parent = parent

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Register Student - Smart Attendance System"
        )

        self.window.geometry(
            "650x600"
        )

        self.window.resizable(
            False,
            False
        )

        self.window.configure(
            bg="#EAF2F8"
        )

        self.window.transient(parent)

        self.window.grab_set()

        self.build_ui()


    # ========================================================
    # BUILD USER INTERFACE
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self.window,
            bg="#0B3C5D",
            height=90
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )


        tk.Label(
            header,
            text="STUDENT REGISTRATION",
            font=(
                "Segoe UI",
                22,
                "bold"
            ),
            bg="#0B3C5D",
            fg="white"
        ).pack(
            pady=(15, 3)
        )


        tk.Label(
            header,
            text="Register a new student into the attendance system",
            font=(
                "Segoe UI",
                10
            ),
            bg="#0B3C5D",
            fg="#D6EAF8"
        ).pack()


        # ----------------------------------------------------
        # MAIN FRAME
        # ----------------------------------------------------

        main_frame = tk.Frame(
            self.window,
            bg="#EAF2F8"
        )

        main_frame.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=25
        )


        # ----------------------------------------------------
        # FORM FRAME
        # ----------------------------------------------------

        form_frame = tk.LabelFrame(
            main_frame,
            text="Student Information",
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            bg="white",
            fg="#0B3C5D",
            padx=25,
            pady=20
        )

        form_frame.pack(
            fill="x"
        )


        # ----------------------------------------------------
        # STUDENT ID
        # ----------------------------------------------------

        tk.Label(
            form_frame,
            text="Student ID",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="white",
            fg="#34495E"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )


        self.id_entry = tk.Entry(
            form_frame,
            width=35,
            font=(
                "Segoe UI",
                11
            )
        )

        self.id_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )


        # ----------------------------------------------------
        # STUDENT NAME
        # ----------------------------------------------------

        tk.Label(
            form_frame,
            text="Student Name",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="white",
            fg="#34495E"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )


        self.name_entry = tk.Entry(
            form_frame,
            width=35,
            font=(
                "Segoe UI",
                11
            )
        )

        self.name_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10
        )


        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        tk.Label(
            form_frame,
            text="Department",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="white",
            fg="#34495E"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=10,
            pady=10
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


        self.department_combo = ttk.Combobox(
            form_frame,
            values=departments,
            width=32,
            state="readonly",
            font=(
                "Segoe UI",
                10
            )
        )

        self.department_combo.grid(
            row=2,
            column=1,
            padx=10,
            pady=10
        )


        # ----------------------------------------------------
        # YEAR
        # ----------------------------------------------------

        tk.Label(
            form_frame,
            text="Year",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="white",
            fg="#34495E"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )


        years = [
            "I",
            "II",
            "III",
            "IV"
        ]


        self.year_combo = ttk.Combobox(
            form_frame,
            values=years,
            width=32,
            state="readonly",
            font=(
                "Segoe UI",
                10
            )
        )

        self.year_combo.grid(
            row=3,
            column=1,
            padx=10,
            pady=10
        )


        # ----------------------------------------------------
        # STATUS LABEL
        # ----------------------------------------------------

        self.status_label = tk.Label(
            main_frame,
            text="",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="#EAF2F8"
        )

        self.status_label.pack(
            pady=10
        )


        # ----------------------------------------------------
        # BUTTON FRAME
        # ----------------------------------------------------

        button_frame = tk.Frame(
            main_frame,
            bg="#EAF2F8"
        )

        button_frame.pack(
            pady=15
        )


        # ----------------------------------------------------
        # REGISTER BUTTON
        # ----------------------------------------------------

        tk.Button(
            button_frame,
            text="➕ Register Student",
            width=20,
            bg="#27AE60",
            fg="white",
            activebackground="#229954",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bd=0,
            cursor="hand2",
            command=self.register_student
        ).grid(
            row=0,
            column=0,
            padx=10
        )


        # ----------------------------------------------------
        # CLEAR BUTTON
        # ----------------------------------------------------

        tk.Button(
            button_frame,
            text="🔄 Clear",
            width=15,
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bd=0,
            cursor="hand2",
            command=self.clear_fields
        ).grid(
            row=0,
            column=1,
            padx=10
        )


        # ----------------------------------------------------
        # CLOSE BUTTON
        # ----------------------------------------------------

        tk.Button(
            button_frame,
            text="❌ Close",
            width=15,
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bd=0,
            cursor="hand2",
            command=self.window.destroy
        ).grid(
            row=0,
            column=2,
            padx=10
        )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        tk.Label(
            self.window,
            text="Smart Attendance System • SQLite Student Management",
            font=(
                "Segoe UI",
                8
            ),
            bg="#EAF2F8",
            fg="#777777"
        ).pack(
            pady=8
        )


        # Focus Student ID

        self.id_entry.focus()


    # ========================================================
    # REGISTER STUDENT
    # ========================================================

    def register_student(self):

        student_id = self.id_entry.get().strip()

        student_name = self.name_entry.get().strip()

        department = self.department_combo.get().strip()

        year = self.year_combo.get().strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if (
            student_id == ""
            or student_name == ""
            or department == ""
            or year == ""
        ):

            self.status_label.config(
                text="Please fill in all student details.",
                fg="#E74C3C"
            )

            messagebox.showerror(
                "Missing Information",
                "Please fill in all student details.",
                parent=self.window
            )

            return


        # ----------------------------------------------------
        # STUDENT ID VALIDATION
        # ----------------------------------------------------

        if not student_id.isdigit():

            self.status_label.config(
                text="Student ID must contain numbers only.",
                fg="#E74C3C"
            )

            messagebox.showerror(
                "Invalid Student ID",
                "Student ID must contain numbers only.",
                parent=self.window
            )

            return


        conn = None

        try:

            conn = sqlite3.connect(
                DATABASE_PATH
            )

            cursor = conn.cursor()


            # ------------------------------------------------
            # CREATE TABLE IF NEEDED
            # ------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    student_name TEXT,
                    department TEXT,
                    year TEXT
                )
            """)


            # ------------------------------------------------
            # CHECK DUPLICATE
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT student_id
                FROM students
                WHERE student_id=?
                """,
                (student_id,)
            )


            existing = cursor.fetchone()


            if existing:

                self.status_label.config(
                    text="Student ID already exists.",
                    fg="#E74C3C"
                )

                messagebox.showwarning(
                    "Duplicate Student",
                    f"Student ID {student_id} already exists.",
                    parent=self.window
                )

                return


            # ------------------------------------------------
            # INSERT STUDENT
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO students (
                    student_id,
                    student_name,
                    department,
                    year
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    student_id,
                    student_name,
                    department,
                    year
                )
            )


            conn.commit()


            self.status_label.config(
                text="Student registered successfully!",
                fg="#27AE60"
            )


            messagebox.showinfo(
                "Registration Successful",
                f"Student registered successfully.\n\n"
                f"Student ID : {student_id}\n"
                f"Name : {student_name}\n"
                f"Department : {department}\n"
                f"Year : {year}",
                parent=self.window
            )


            # Clear form

            self.clear_fields()


        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Database Error",
                "Student ID already exists.",
                parent=self.window
            )


        except Exception as e:

            messagebox.showerror(
                "Database Error",
                f"Unable to register student.\n\n{e}",
                parent=self.window
            )


        finally:

            if conn:

                conn.close()


    # ========================================================
    # CLEAR FIELDS
    # ========================================================

    def clear_fields(self):

        self.id_entry.delete(
            0,
            tk.END
        )

        self.name_entry.delete(
            0,
            tk.END
        )

        self.department_combo.set(
            ""
        )

        self.year_combo.set(
            ""
        )

        self.status_label.config(
            text=""
        )

        self.id_entry.focus()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    root.title(
        "Smart Attendance System"
    )

    root.geometry(
        "400x300"
    )

    root.withdraw()

    RegisterStudentWindow(root)

    root.mainloop()