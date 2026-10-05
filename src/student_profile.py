import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
from PIL import Image, ImageTk

class StudentProfile:
    def __init__(self, root, student_id):
        self.root = root
        self.student_id = student_id
        self.root.title(f"Student Portal - {student_id}")
        self.root.geometry("1000x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#010409")

        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.base_dir, "database", "attendance.db")
        self.face_folder = os.path.join(self.base_dir, "registered_faces", self.student_id)

        self.colors = {
            "primary": "#0D1117", "bg": "#010409", "cards": "#161B22",
            "accent": "#00FFA3", "text_light": "#E6EDF3", "text_muted": "#8B949E"
        }

        self.build_ui()
        self.load_student_data()

    def build_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg=self.colors["primary"], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="STUDENT PORTAL", font=("Segoe UI", 20, "bold"), 
            bg=self.colors["primary"], fg=self.colors["text_light"]
        ).pack(side="left", padx=30, pady=20)
        
        tk.Button(
            header, text="🚪 Logout", command=self.root.destroy,
            font=("Segoe UI", 10, "bold"), bg="#FF0055", fg="white", bd=0, padx=15, pady=5, cursor="hand2"
        ).pack(side="right", padx=30, pady=20)

        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # --- LEFT PANEL (Profile Card) ---
        profile_card = tk.Frame(main_frame, bg=self.colors["cards"], width=300)
        profile_card.pack(side="left", fill="y", padx=(0, 20))
        profile_card.pack_propagate(False)
        
        # Neon Top Accent
        tk.Frame(profile_card, bg=self.colors["accent"], height=3).pack(fill="x")

        self.lbl_image = tk.Label(profile_card, bg=self.colors["cards"])
        self.lbl_image.pack(pady=(30, 10))

        self.lbl_name = tk.Label(profile_card, text="Loading...", font=("Segoe UI", 16, "bold"), bg=self.colors["cards"], fg=self.colors["text_light"])
        self.lbl_name.pack(pady=(5, 0))
        
        self.lbl_id = tk.Label(profile_card, text=f"ID: {self.student_id}", font=("Segoe UI", 11), bg=self.colors["cards"], fg=self.colors["accent"])
        self.lbl_id.pack(pady=(0, 20))

        self.lbl_dept = tk.Label(profile_card, text="Dept: -", font=("Segoe UI", 11), bg=self.colors["cards"], fg=self.colors["text_muted"])
        self.lbl_dept.pack(anchor="w", padx=30, pady=5)
        
        self.lbl_year = tk.Label(profile_card, text="Year: -", font=("Segoe UI", 11), bg=self.colors["cards"], fg=self.colors["text_muted"])
        self.lbl_year.pack(anchor="w", padx=30, pady=5)
        
        self.lbl_total_present = tk.Label(profile_card, text="Total Present: 0 Days", font=("Segoe UI", 11, "bold"), bg=self.colors["cards"], fg="#00E5FF")
        self.lbl_total_present.pack(anchor="w", padx=30, pady=20)

        # --- RIGHT PANEL (Attendance Log) ---
        log_card = tk.Frame(main_frame, bg=self.colors["cards"])
        log_card.pack(side="left", fill="both", expand=True)
        tk.Frame(log_card, bg=self.colors["accent"], height=3).pack(fill="x")

        tk.Label(
            log_card, text="My Attendance History", font=("Segoe UI", 14, "bold"), 
            bg=self.colors["cards"], fg=self.colors["text_light"]
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Table Styling
        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.colors["primary"], foreground=self.colors["accent"], borderwidth=0)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=35, background=self.colors["cards"], fieldbackground=self.colors["cards"], foreground=self.colors["text_light"], borderwidth=0)
        
        columns = ("Date", "Time", "Status")
        self.tree = ttk.Treeview(log_card, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_student_data(self):
        # 1. Try to load profile picture
        try:
            if os.path.exists(self.face_folder):
                images = [f for f in os.listdir(self.face_folder) if f.endswith(('.jpg', '.png'))]
                if images:
                    img_path = os.path.join(self.face_folder, images[0])
                    img = Image.open(img_path).resize((120, 120))
                    photo = ImageTk.PhotoImage(img)
                    self.lbl_image.configure(image=photo)
                    self.lbl_image.image = photo
        except Exception:
            pass

        # 2. Load Database Records
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get Details
            cursor.execute("SELECT student_name, department, year FROM students WHERE student_id=?", (self.student_id,))
            student_info = cursor.fetchone()
            if student_info:
                self.lbl_name.config(text=student_info[0])
                self.lbl_dept.config(text=f"Dept: {student_info[1]}")
                self.lbl_year.config(text=f"Year: {student_info[2]}")

            # Get Attendance Log
            cursor.execute("SELECT date, time, status FROM attendance WHERE student_id=? ORDER BY date DESC, time DESC", (self.student_id,))
            records = cursor.fetchall()
            
            # Count unique days present
            unique_days = len(set([r[0] for r in records]))
            self.lbl_total_present.config(text=f"Total Present: {unique_days} Days")

            for row in records:
                self.tree.insert("", tk.END, values=row)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()

if __name__ == "__main__":
    # If run directly via login screen, sys.argv[1] will be the student ID
    student_id = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    root = tk.Tk()
    app = StudentProfile(root, student_id)
    root.mainloop()