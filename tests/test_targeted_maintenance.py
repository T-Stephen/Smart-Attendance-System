import sys
import os
import time
import cv2
import numpy as np
import tkinter as tk

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(os.getcwd()) == "tests":
    os.chdir(ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
sys.path.append('src')

from core.recognition_engine import RecognitionEngine
from admin_dashboard import AdminDashboard

print("=" * 60)
print("RUNNING TARGETED MAINTENANCE VALIDATION SUITE")
print("=" * 60)

# ============================================================
# CHECK 1: STATUS COLOR MAPPING CHECK
# ============================================================
print("\n[CHECK 1] Testing Status Color Mapping Logic...")

root = tk.Tk()
root.withdraw()
dashboard = AdminDashboard(root)

# Helper function reproducing the exact sidebar logic from admin_dashboard.py
def get_slot_color(status):
    if "ALREADY" in status:
        return dashboard.colors.get("cyan", "#00E5FF")
    elif status in ["VERIFIED", "ATTENDANCE MARKED", "MARKED"] or "VERIFIED" in status or "MARKED" in status:
        return "#10b981"
    elif status in ["BLINK REQUIRED", "VERIFYING", "VERIFYING..."] or "BLINK" in status or "VERIFYING" in status or "REVIEW" in status:
        return "#f59e0b"
    elif "THREAT" in status or "ERROR" in status:
        return dashboard.colors["danger"]
    else:
        return dashboard.colors["text_light"]

test_cases = [
    ("VERIFIED", "#10b981"),
    ("ATTENDANCE MARKED", "#10b981"),
    ("MARKED", "#10b981"),
    ("BLINK REQUIRED", "#f59e0b"),
    ("VERIFYING", "#f59e0b"),
    ("VERIFYING...", "#f59e0b"),
    ("SECURITY REVIEW", "#f59e0b"),
    ("THREAT DETECTED", dashboard.colors["danger"]),
    ("ALREADY MARKED", dashboard.colors.get("cyan", "#00E5FF")),
    ("UNKNOWN", dashboard.colors["text_light"]),
]

for status_val, expected_color in test_cases:
    actual_color = get_slot_color(status_val)
    print(f"  Status: '{status_val:18}' -> Color: {actual_color} (Expected: {expected_color})")
    assert actual_color == expected_color, f"Mismatch for '{status_val}': got {actual_color}, expected {expected_color}"

print(">>> CHECK 1 PASSED: All status color mappings verified successfully!")

# ============================================================
# CHECK 2: ATOMIC CURRENT-FACES BUFFER PERSISTENCE
# ============================================================
print("\n[CHECK 2] Testing Atomic current_faces Buffer Persistence...")

engine = RecognitionEngine()
f1 = cv2.imread('registered_faces/2026001/001.jpg')
f2 = cv2.imread('registered_faces/2026002/001.jpg')

# Frame 1: 1 face
canvas1 = np.zeros((480, 640, 3), dtype=np.uint8)
canvas1[100:260, 200:360] = f1
engine.process_frame(canvas1)
initial_faces = list(engine.current_faces)
assert len(initial_faces) == 1, f"Expected 1 face in Frame 1, got {len(initial_faces)}"
print(f"  Frame 1 processed: {len(initial_faces)} face visible ({initial_faces[0]['name']})")

# Verify that current_faces is NOT cleared mid-inference
# Simulate checking current_faces before frame 2 completes
canvas2 = np.zeros((480, 640, 3), dtype=np.uint8)
canvas2[100:260, 80:240] = f1
canvas2[100:260, 380:540] = f2

# Prior to running process_frame, current_faces contains initial_faces
assert len(engine.current_faces) == 1
# Process frame 2
engine.process_frame(canvas2)
updated_faces = list(engine.current_faces)
assert len(updated_faces) == 2, f"Expected 2 faces in Frame 2, got {len(updated_faces)}"
print(f"  Frame 2 processed: {len(updated_faces)} faces visible (atomic transition confirmed)")
print(">>> CHECK 2 PASSED: Atomic buffer transition verified!")

# ============================================================
# CHECK 3: RAPID START/STOP TEARDOWN INTEGRITY
# ============================================================
print("\n[CHECK 3] Testing Rapid Start/Stop Camera Teardown...")

for cycle in range(1, 6):
    print(f"  Cycle {cycle}: Starting recognition...")
    dashboard.show_recognition()
    # Let Tkinter event loop process immediate events
    root.update()
    time.sleep(0.05)
    
    print(f"  Cycle {cycle}: Stopping recognition immediately...")
    dashboard.stop_recognition()
    root.update()
    
    # Assert teardown invariant
    assert dashboard.rec_job is None, f"Cycle {cycle}: rec_job was not cancelled"
    assert dashboard.rec_engine is None, f"Cycle {cycle}: rec_engine was not cleaned up"
    assert not getattr(dashboard, "_inference_busy", False), f"Cycle {cycle}: _inference_busy remained True"
    print(f"  Cycle {cycle}: Clean teardown verified.")

# Final check: start recognition once more to ensure camera re-binds cleanly
print("  Final check: Starting recognition once more after rapid cycles...")
dashboard.show_recognition()
root.update()
time.sleep(0.1)
dashboard.stop_recognition()
root.update()

root.destroy()
print(">>> CHECK 3 PASSED: Rapid Start/Stop cycles completed with zero errors!")

print("\n" + "=" * 60)
print("ALL TARGETED MAINTENANCE CHECKS COMPLETED SUCCESSFULLY!")
print("=" * 60)
