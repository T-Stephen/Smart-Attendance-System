import sys
import tkinter as tk
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(os.getcwd()) == "tests":
    os.chdir(ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
sys.path.append('src')

from admin_dashboard import AdminDashboard

print("=" * 60)
print("TESTING ADMIN DASHBOARD REGRESSION INTEGRITY")
print("=" * 60)

root = tk.Tk()
root.withdraw() # Headless/offscreen

try:
    dashboard = AdminDashboard(root)
    print("AdminDashboard initialized successfully.")
    
    # 1. Check statistics
    print(f"Total students var: {dashboard.var_total_students.get()}")
    print(f"Total attendance var: {dashboard.var_total_attendance.get()}")
    
    # 2. Check page transitions
    dashboard.show_dashboard()
    print("Dashboard page loaded.")
    
    dashboard.show_student_database()
    print("Student database page loaded.")
    
    dashboard.show_attendance_database()
    print("Attendance database page loaded.")

    dashboard.show_reports()
    print("Reports page loaded.")

    dashboard.show_security_center()
    print("Security center page loaded.")
    
    # 3. Test Recognition Engine loading through dashboard
    dashboard._init_recognition_engine()
    assert dashboard.rec_engine is not None, "Recognition engine failed to instantiate in dashboard!"
    print("Recognition engine integrated into dashboard successfully.")
    print(f"Engine Online: {len(dashboard.rec_engine.db_labels)} reference prints loaded.")
    
    # Clean up
    if dashboard.rec_engine.cap:
        dashboard.rec_engine.cap.release()
    root.destroy()
    
    print("\nALL REGRESSION INTEGRITY CHECKS PASSED!")

except Exception as e:
    root.destroy()
    print(f"REGRESSION CHECK FAILED: {e}")
    sys.exit(1)
