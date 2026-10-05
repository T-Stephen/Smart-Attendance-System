import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
import sys
import subprocess

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Campus - Enterprise Portal")
        self.root.geometry("550x650")
        self.root.resizable(False, False)
        
        # PRO Light UI Color Palette
        self.colors = {
            "bg_app": "#F8FAFC",         # Soft Slate Background
            "bg_card": "#FFFFFF",        # Pure White Card
            "text_main": "#0F172A",      # Deep Slate Text
            "text_sub": "#64748B",       # Muted Gray
            "input_bg": "#F1F5F9",       # Input Field Gray
            "border": "#E2E8F0",         # Soft Border
            "admin_accent": "#3B82F6",   # Enterprise Blue
            "staff_accent": "#10B981",   # Emerald Green
            "student_accent": "#F59E0B"  # Amber Orange
        }
        
        self.root.configure(bg=self.colors["bg_app"])
        self.current_role = "Admin" # Default selected role
        self.role_buttons = {}

        # Setup Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.base_dir, "database", "attendance.db")

        self.setup_database()
        self.build_ui()

    def setup_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, role TEXT, student_id TEXT
            )
        """)
        
        # Auto-generate Admin
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, student_id) VALUES ('admin', 'admin123', 'Admin', 'NONE')")
            
        # Auto-generate Staff (NEW)
        cursor.execute("SELECT * FROM users WHERE username='staff'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, student_id) VALUES ('staff', 'staff123', 'Staff', 'NONE')")
            
        # Auto-Sync Students
        try:
            cursor.execute("SELECT student_id FROM students")
            for (s_id,) in cursor.fetchall():
                cursor.execute("SELECT * FROM users WHERE username=?", (s_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (username, password, role, student_id) VALUES (?, 'student123', 'Student', ?)", (s_id, s_id))
        except Exception:
            pass
            
        conn.commit()
        conn.close()

    def build_ui(self):
        # --- HEADER BRANDING ---
        header = tk.Frame(self.root, bg=self.colors["bg_app"])
        header.pack(fill="x", pady=(40, 20))
        
        tk.Label(
            header, text="SMART CAMPUS AI", 
            font=("Segoe UI", 22, "bold"), bg=self.colors["bg_app"], fg=self.colors["text_main"]
        ).pack()
        
        tk.Label(
            header, text="Enterprise Attendance Management System", 
            font=("Segoe UI", 11), bg=self.colors["bg_app"], fg=self.colors["text_sub"]
        ).pack(pady=(5, 0))

        # --- LOGIN CARD ---
        self.card = tk.Frame(self.root, bg=self.colors["bg_card"], highlightbackground=self.colors["border"], highlightthickness=1)
        self.card.pack(expand=False, fill="both", padx=60, pady=10)
        self.card.pack_propagate(False)
        self.card.configure(height=420)

        # ROLE SELECTION TABS
        tab_frame = tk.Frame(self.card, bg=self.colors["bg_card"])
        tab_frame.pack(fill="x", padx=30, pady=(30, 25))

        roles = [
            ("Admin", self.colors["admin_accent"]), 
            ("Staff", self.colors["staff_accent"]), 
            ("Student", self.colors["student_accent"])
        ]
        
        for role, color in roles:
            btn = tk.Button(
                tab_frame, text=role, font=("Segoe UI", 11, "bold"), 
                bg=self.colors["input_bg"], fg=self.colors["text_sub"], 
                bd=0, cursor="hand2", width=10,
                command=lambda r=role, c=color: self.switch_role(r, c)
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self.role_buttons[role] = btn

        # INPUT FIELDS
        form_frame = tk.Frame(self.card, bg=self.colors["bg_card"])
        form_frame.pack(fill="both", expand=True, padx=30)

        self.lbl_title = tk.Label(form_frame, text="Admin Portal Login", font=("Segoe UI", 14, "bold"), bg=self.colors["bg_card"], fg=self.colors["text_main"])
        self.lbl_title.pack(anchor="w", pady=(0, 20))

        tk.Label(form_frame, text="Username / ID", font=("Segoe UI", 10, "bold"), bg=self.colors["bg_card"], fg=self.colors["text_sub"]).pack(anchor="w")
        self.username_var = tk.StringVar()
        tk.Entry(
            form_frame, textvariable=self.username_var, font=("Segoe UI", 12), 
            bg=self.colors["input_bg"], fg=self.colors["text_main"], insertbackground=self.colors["text_main"], 
            relief="flat", highlightbackground=self.colors["border"], highlightthickness=1
        ).pack(fill="x", pady=(5, 15), ipady=6)

        tk.Label(form_frame, text="Password", font=("Segoe UI", 10, "bold"), bg=self.colors["bg_card"], fg=self.colors["text_sub"]).pack(anchor="w")
        self.password_var = tk.StringVar()
        
        self.pwd_entry = tk.Entry(
            form_frame, textvariable=self.password_var, show="•", font=("Segoe UI", 12), 
            bg=self.colors["input_bg"], fg=self.colors["text_main"], insertbackground=self.colors["text_main"], 
            relief="flat", highlightbackground=self.colors["border"], highlightthickness=1
        )
        self.pwd_entry.pack(fill="x", pady=(5, 25), ipady=6)
        
        # Wire up the Enter key
        self.root.bind('<Return>', lambda event: self.authenticate())

        self.login_btn = tk.Button(
            form_frame, text="Secure Login", command=self.authenticate, 
            font=("Segoe UI", 12, "bold"), bg=self.colors["admin_accent"], fg="white", 
            bd=0, pady=12, cursor="hand2"
        )
        self.login_btn.pack(fill="x")

        # Initialize Default State
        self.switch_role("Admin", self.colors["admin_accent"])

    def switch_role(self, selected_role, active_color):
        self.current_role = selected_role
        self.lbl_title.config(text=f"{selected_role} Portal Login")
        self.login_btn.config(bg=active_color)
        
        # Reset all buttons to inactive gray
        for role, btn in self.role_buttons.items():
            if role == selected_role:
                btn.config(bg=active_color, fg="white")
            else:
                btn.config(bg=self.colors["input_bg"], fg=self.colors["text_sub"])
                
        # Clear fields on switch for security
        self.username_var.set("")
        self.password_var.set("")
        self.pwd_entry.focus()

    def authenticate(self):
        user = self.username_var.get().strip()
        pwd = self.password_var.get().strip()
        role = self.current_role

        if not user or not pwd:
            messagebox.showwarning("Required", "Please enter both credentials.")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # VERY SECURE: It now checks if their Role actually matches the tab they clicked!
        cursor.execute("SELECT student_id FROM users WHERE username=? AND password=? AND role=?", (user, pwd, role))
        result = cursor.fetchone()
        conn.close()

        if result:
            student_id = result[0]
            
            if role == "Admin":
                # ========================================================
                # SPA TRANSITION: Load Dashboard in the SAME window
                # ========================================================
                
                # 1. Clear every widget (buttons, text) from the login screen
                for widget in self.root.winfo_children():
                    widget.destroy() 
                
                # 2. Import the dashboard locally to prevent loading errors
                import admin_dashboard 
                
                # 3. Pass this exact same window to the Admin Dashboard
                # The dashboard will automatically resize the window and draw its own UI!
                admin_dashboard.AdminDashboard(self.root)
                
            elif role == "Student":
                # Students can remain as a separate launch for security isolation
                self.root.destroy()
                student_path = os.path.join(self.base_dir, "src", "student_profile.py")
                subprocess.Popen([sys.executable, student_path, student_id])
                
            elif role == "Staff":
                # Placeholder until you want to build the Staff dashboard!
                messagebox.showinfo("Staff Portal", "Welcome Staff Member!\n\n(Staff Dashboard module is ready to be developed!)")
        else:
            messagebox.showerror("Access Denied", f"Invalid credentials for {role} account.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()