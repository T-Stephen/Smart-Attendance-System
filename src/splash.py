import tkinter as tk
from tkinter import ttk
import os
import sys
import subprocess

class SplashScreen:
    def __init__(self, root):
        self.root = root
        # Create a borderless window
        self.root.overrideredirect(True)
        
        # Dimensions
        width = 600
        height = 350
        
        # Center the window on the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        
        # Colors
        self.bg_color = "#0B0F14"       # Deep Charcoal
        self.text_main = "#F8FAFC"      # Crisp White
        self.text_sub = "#94A3B8"       # Slate Gray
        self.accent = "#2563EB"         # Enterprise Blue
        
        self.root.configure(bg=self.bg_color)
        
        self.build_ui()
        
    def build_ui(self):
        # Main Container
        container = tk.Frame(self.root, bg=self.bg_color, highlightbackground=self.accent, highlightthickness=2)
        container.pack(fill="both", expand=True)
        
        # Spacer
        tk.Label(container, text="", bg=self.bg_color).pack(pady=20)
        
        # App Title
        tk.Label(
            container, text="SMART CAMPUS AI", 
            font=("Segoe UI", 28, "bold"), bg=self.bg_color, fg=self.text_main
        ).pack(pady=(20, 0))
        
        tk.Label(
            container, text="Intelligent Identity & Attendance Platform", 
            font=("Segoe UI", 12), bg=self.bg_color, fg=self.accent
        ).pack(pady=(5, 30))
        
        # Dynamic Loading Text
        self.loading_text = tk.StringVar()
        self.loading_text.set("Initializing System...")
        
        self.lbl_status = tk.Label(
            container, textvariable=self.loading_text, 
            font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_sub
        )
        self.lbl_status.pack(pady=(20, 5))
        
        # Custom Progress Bar Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=6, background=self.accent, troughcolor="#171D25", bordercolor=self.bg_color, lightcolor=self.accent, darkcolor=self.accent)
        
        self.progress = ttk.Progressbar(
            container, style="TProgressbar", orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(pady=10)
        
        # Developer Credit
        tk.Label(
            container, text="Engineered for 2026 Portfolio Deployment", 
            font=("Segoe UI", 8), bg=self.bg_color, fg="#334155"
        ).pack(side="bottom", pady=15)
        
        # Start the loading sequence
        self.progress_value = 0
        self.load_sequence()

    def load_sequence(self):
        # Simulate heavy-duty system checks
        tasks = [
            (15, "Warming up MTCNN Face Detector..."),
            (35, "Initializing 512-D FaceNet Embeddings..."),
            (60, "Loading SVM Classification Models..."),
            (85, "Securing SQLite Database Connections..."),
            (100, "System Ready. Launching Secure Portal...")
        ]
        
        for target_val, text in tasks:
            if self.progress_value < target_val:
                self.progress_value += 1
                self.progress["value"] = self.progress_value
                
                # Update text at specific milestones
                if self.progress_value == target_val:
                    self.loading_text.set(text)
                
                # Adjust speed (smaller number = faster loading)
                self.root.after(25, self.load_sequence)
                return
                
        # When 100% is reached, launch the main login and destroy splash
        self.root.after(500, self.launch_main_app)

    def launch_main_app(self):
        # Close the splash screen
        self.root.destroy()
        
        # Launch the enterprise login portal
        base_dir = os.path.dirname(os.path.abspath(__file__))
        login_path = os.path.join(base_dir, "main_login.py")
        subprocess.Popen([sys.executable, login_path])

if __name__ == "__main__":
    root = tk.Tk()
    app = SplashScreen(root)
    root.mainloop()