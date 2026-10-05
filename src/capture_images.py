import os
import sqlite3
import cv2
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk
from mtcnn import MTCNN


# ============================================================
# PATHS
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

SAVE_FOLDER = os.path.join(
    BASE_DIR,
    "registered_faces"
)

TOTAL_IMAGES = 100


# ============================================================
# DATABASE
# ============================================================

def get_student(student_id):

    try:

        conn = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT student_name, department, year
            FROM students
            WHERE student_id=?
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        conn.close()

        return student

    except Exception as e:

        print("Database error:", e)

        return None


# ============================================================
# CAPTURE IMAGES PAGE
# ============================================================

class CaptureImagesPage:

    def __init__(self, parent):

        self.parent = parent

        self.frame = tk.Frame(
            parent,
            bg="#EAF2F8"
        )

        self.frame.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # Camera variables
        # ----------------------------------------------------

        self.cap = None

        self.detector = None

        self.camera_running = False

        self.camera_job = None

        # ----------------------------------------------------
        # Student variables
        # ----------------------------------------------------

        self.student_id = ""

        self.student_name = ""

        # ----------------------------------------------------
        # Image counter
        # ----------------------------------------------------

        self.count = 0

        self.build_ui()


    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        tk.Label(
            self.frame,
            text="CAPTURE STUDENT FACE IMAGES",
            font=("Segoe UI", 22, "bold"),
            bg="#EAF2F8",
            fg="#0B3C5D"
        ).pack(
            pady=(15, 3)
        )


        tk.Label(
            self.frame,
            text="Capture face images for AI model training",
            font=("Segoe UI", 10),
            bg="#EAF2F8",
            fg="#666666"
        ).pack(
            pady=(0, 10)
        )


        # ----------------------------------------------------
        # STUDENT INFORMATION
        # ----------------------------------------------------

        student_frame = tk.LabelFrame(
            self.frame,
            text="Student Information",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#0B3C5D",
            padx=15,
            pady=10
        )

        student_frame.pack(
            fill="x",
            padx=25,
            pady=5
        )


        # Student ID

        tk.Label(
            student_frame,
            text="Student ID:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=5
        )


        self.student_id_entry = ttk.Entry(
            student_frame,
            width=25,
            font=("Segoe UI", 10)
        )

        self.student_id_entry.grid(
            row=0,
            column=1,
            padx=8,
            pady=5
        )


        # Load button

        self.load_button = tk.Button(
            student_frame,
            text="Load Student",
            command=self.load_student,
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2"
        )

        self.load_button.grid(
            row=0,
            column=2,
            padx=8
        )


        # Student name

        tk.Label(
            student_frame,
            text="Student Name:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=5
        )


        self.student_name_var = tk.StringVar(
            value="-"
        )


        tk.Label(
            student_frame,
            textvariable=self.student_name_var,
            font=("Segoe UI", 10),
            bg="white",
            fg="#0B3C5D"
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=8
        )


        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        camera_frame = tk.LabelFrame(
            self.frame,
            text="Live Camera",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#0B3C5D",
            padx=8,
            pady=8
        )

        camera_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=8
        )


        self.camera_label = tk.Label(
            camera_frame,
            text="Camera not started",
            font=("Segoe UI", 14),
            bg="#1C2833",
            fg="white"
        )

        self.camera_label.pack(
            fill="both",
            expand=True
        )


        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        self.progress_var = tk.IntVar(
            value=0
        )


        self.progress = ttk.Progressbar(
            self.frame,
            maximum=TOTAL_IMAGES,
            variable=self.progress_var,
            length=500
        )

        self.progress.pack(
            pady=(5, 3)
        )


        self.progress_label = tk.Label(
            self.frame,
            text=f"Captured: 0 / {TOTAL_IMAGES}",
            font=("Segoe UI", 11, "bold"),
            bg="#EAF2F8",
            fg="#0B3C5D"
        )

        self.progress_label.pack()


        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        button_frame = tk.Frame(
            self.frame,
            bg="#EAF2F8"
        )

        button_frame.pack(
            pady=10
        )


        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Capture",
            command=self.start_camera,
            width=18,
            bg="#27AE60",
            fg="white",
            activebackground="#229954",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2"
        )

        self.start_button.grid(
            row=0,
            column=0,
            padx=5
        )


        self.stop_button = tk.Button(
            button_frame,
            text="■ Stop Capture",
            command=self.stop_camera,
            width=18,
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2"
        )

        self.stop_button.grid(
            row=0,
            column=1,
            padx=5
        )


        # ----------------------------------------------------
        # INSTRUCTIONS
        # ----------------------------------------------------

        tk.Label(
            self.frame,
            text=(
                "Look directly at the camera • "
                "Move your head slowly • "
                "100 images will be captured automatically"
            ),
            font=("Segoe UI", 9),
            bg="#EAF2F8",
            fg="#666666"
        ).pack(
            pady=(0, 10)
        )


    # ========================================================
    # LOAD STUDENT
    # ========================================================

    def load_student(self):

        student_id = (
            self.student_id_entry
            .get()
            .strip()
        )


        if not student_id:

            messagebox.showwarning(
                "Student ID Required",
                "Please enter the Student ID."
            )

            return


        student = get_student(
            student_id
        )


        if student is None:

            self.student_id = ""

            self.student_name = ""

            self.student_name_var.set(
                "-"
            )

            messagebox.showerror(
                "Student Not Found",
                f"No student found with ID:\n\n{student_id}"
            )

            return


        self.student_id = student_id

        self.student_name = student[0]


        self.student_name_var.set(
            self.student_name
        )


        messagebox.showinfo(
            "Student Loaded",
            f"Student loaded successfully.\n\n"
            f"Student ID: {student_id}\n"
            f"Student Name: {self.student_name}"
        )


    # ========================================================
    # START CAMERA
    # ========================================================

    def start_camera(self):

        # ----------------------------------------------------
        # Student validation
        # ----------------------------------------------------

        if not self.student_id:

            messagebox.showwarning(
                "Student Required",
                "Please enter a Student ID and click "
                "'Load Student' first."
            )

            return


        if self.camera_running:
            return


        # ----------------------------------------------------
        # Initialize MTCNN
        # ----------------------------------------------------

        try:

            self.detector = MTCNN()

        except Exception as e:

            messagebox.showerror(
                "Face Detector Error",
                f"Unable to initialize MTCNN.\n\n{e}"
            )

            return


        # ----------------------------------------------------
        # Open webcam
        # ----------------------------------------------------

        self.cap = cv2.VideoCapture(
            0
        )


        if not self.cap.isOpened():

            self.cap.release()

            self.cap = None

            messagebox.showerror(
                "Camera Error",
                "Unable to open webcam.\n\n"
                "Make sure the camera is connected "
                "and not being used by another application."
            )

            return


        # ----------------------------------------------------
        # Create save folder
        # ----------------------------------------------------

        save_path = os.path.join(
            SAVE_FOLDER,
            self.student_id
        )


        os.makedirs(
            save_path,
            exist_ok=True
        )


        # ----------------------------------------------------
        # Reset counter
        # ----------------------------------------------------

        self.count = 0

        self.progress_var.set(
            0
        )

        self.progress_label.config(
            text=f"Captured: 0 / {TOTAL_IMAGES}"
        )


        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.camera_running = True


        self.start_button.config(
            state="disabled"
        )

        self.load_button.config(
            state="disabled"
        )

        self.student_id_entry.config(
            state="disabled"
        )


        self.update_camera()


    # ========================================================
    # UPDATE CAMERA
    # ========================================================

    def update_camera(self):

        if not self.camera_running:
            return


        if self.cap is None:
            return


        ret, frame = self.cap.read()


        if not ret:

            self.stop_camera()

            messagebox.showerror(
                "Camera Error",
                "Unable to read camera frame."
            )

            return


        # ----------------------------------------------------
        # Mirror camera
        # ----------------------------------------------------

        frame = cv2.flip(
            frame,
            1
        )


        # ----------------------------------------------------
        # Convert to RGB
        # ----------------------------------------------------

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        # ----------------------------------------------------
        # Face detection
        # ----------------------------------------------------

        try:

            faces = self.detector.detect_faces(
                rgb
            )

        except Exception:

            faces = []


        # ----------------------------------------------------
        # Process detected face
        # ----------------------------------------------------

        for face in faces:

            x, y, w, h = face["box"]


            # Correct negative MTCNN coordinates

            x = max(
                0,
                x
            )

            y = max(
                0,
                y
            )


            if w < 60 or h < 60:
                continue


            x2 = min(
                frame.shape[1],
                x + w
            )

            y2 = min(
                frame.shape[0],
                y + h
            )


            face_img = frame[
                y:y2,
                x:x2
            ]


            if face_img.size == 0:
                continue


            # ------------------------------------------------
            # Save face image
            # ------------------------------------------------

            if self.count < TOTAL_IMAGES:

                resized_face = cv2.resize(
                    face_img,
                    (160, 160)
                )


                self.count += 1


                save_path = os.path.join(
                    SAVE_FOLDER,
                    self.student_id
                )


                filename = os.path.join(
                    save_path,
                    f"{self.count:03d}.jpg"
                )


                cv2.imwrite(
                    filename,
                    resized_face
                )


                self.progress_var.set(
                    self.count
                )


                self.progress_label.config(
                    text=(
                        f"Captured: "
                        f"{self.count} / "
                        f"{TOTAL_IMAGES}"
                    )
                )


            # ------------------------------------------------
            # Draw rectangle
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x2, y2),
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                "FACE DETECTED",
                (x, max(25, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


            break


        # ----------------------------------------------------
        # Capture counter on camera
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"Captured: {self.count}/{TOTAL_IMAGES}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        # ----------------------------------------------------
        # Convert to Tkinter image
        # ----------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        image = Image.fromarray(
            rgb_frame
        )


        # Fit camera inside available area

        image.thumbnail(
            (850, 450)
        )


        photo = ImageTk.PhotoImage(
            image
        )


        self.camera_label.config(
            image=photo,
            text=""
        )


        self.camera_label.image = photo


        # ----------------------------------------------------
        # Check completion
        # ----------------------------------------------------

        if self.count >= TOTAL_IMAGES:

            self.stop_camera()


            messagebox.showinfo(
                "Capture Completed",
                f"Face capture completed successfully!\n\n"
                f"Student: {self.student_name}\n"
                f"Student ID: {self.student_id}\n"
                f"Images Captured: {self.count}\n\n"
                f"Images saved to:\n"
                f"{os.path.join(SAVE_FOLDER, self.student_id)}"
            )

            return


        # ----------------------------------------------------
        # Continue
        # ----------------------------------------------------

        self.camera_job = self.parent.after(
            30,
            self.update_camera
        )


    # ========================================================
    # STOP CAMERA
    # ========================================================

    def stop_camera(self):

        self.camera_running = False


        # ----------------------------------------------------
        # Cancel Tkinter camera loop
        # ----------------------------------------------------

        if self.camera_job is not None:

            try:

                self.parent.after_cancel(
                    self.camera_job
                )

            except:

                pass

            self.camera_job = None


        # ----------------------------------------------------
        # Release camera
        # ----------------------------------------------------

        if self.cap is not None:

            self.cap.release()

            self.cap = None


        # ----------------------------------------------------
        # Reset controls
        # ----------------------------------------------------

        self.start_button.config(
            state="normal"
        )

        self.load_button.config(
            state="normal"
        )

        self.student_id_entry.config(
            state="normal"
        )


        self.camera_label.config(
            image="",
            text="Camera stopped"
        )


        self.camera_label.image = None


    # ========================================================
    # DESTROY
    # ========================================================

    def destroy(self):

        self.stop_camera()

        self.frame.destroy()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    root.title(
        "Smart Attendance System - Capture Images"
    )

    root.geometry(
        "1000x750"
    )

    root.minsize(
        850,
        650
    )

    root.configure(
        bg="#EAF2F8"
    )


    app = CaptureImagesPage(
        root
    )


    def close_application():

        app.destroy()

        root.destroy()


    root.protocol(
        "WM_DELETE_WINDOW",
        close_application
    )


    root.mainloop()