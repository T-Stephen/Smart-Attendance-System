import csv
import os
import sqlite3
from datetime import datetime

DATABASE_PATH = "database/attendance.db"

ATTENDANCE_FOLDER = "attendance"
ATTENDANCE_FILE = os.path.join(ATTENDANCE_FOLDER, "attendance.csv")


def create_attendance_file():
    os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)

    if not os.path.exists(ATTENDANCE_FILE):

        with open(ATTENDANCE_FILE, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Student_ID",
                "Student_Name",
                "Department",
                "Year",
                "Date",
                "Time",
                "Confidence",
                "Status"
            ])


def mark_attendance(student_id, confidence):

    create_attendance_file()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime("%d-%m-%Y")
    current_time = datetime.now().strftime("%H:%M:%S")

    # ==========================================
    # Get Student Details
    # ==========================================

    cursor.execute("""
        SELECT student_name, department, year
        FROM students
        WHERE student_id=?
    """, (student_id,))

    student = cursor.fetchone()

    if student is None:

        print(f"Student ID {student_id} not found in database.")

        conn.close()

        return False

    student_name, department, year = student

    # ==========================================
    # Check Duplicate Attendance (Database)
    # ==========================================

    cursor.execute("""
        SELECT *
        FROM attendance
        WHERE student_id=? AND date=?
    """, (student_id, today))

    if cursor.fetchone():

        conn.close()

        return False

    # ==========================================
    # Save Attendance into Database
    # ==========================================

    cursor.execute("""
        INSERT INTO attendance
        (
            student_id,
            student_name,
            department,
            year,
            date,
            time,
            confidence,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        student_name,
        department,
        year,
        today,
        current_time,
        confidence,
        "Present"
    ))

    conn.commit()

    conn.close()

    # ==========================================
    # Check Duplicate Attendance (CSV)
    # ==========================================

    duplicate = False

    with open(ATTENDANCE_FILE, "r", newline="") as file:

        reader = csv.reader(file)

        for row in reader:

            if len(row) >= 8:

                if row[0] == student_id and row[4] == today:

                    duplicate = True
                    break

    # ==========================================
    # Save Attendance into CSV
    # ==========================================

    if not duplicate:

        with open(ATTENDANCE_FILE, "a", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                student_id,
                student_name,
                department,
                year,
                today,
                current_time,
                f"{confidence:.2f}%",
                "Present"
            ])

    # ==========================================
    # Console Output
    # ==========================================

    print("\n" + "=" * 60)
    print("      ATTENDANCE MARKED SUCCESSFULLY")
    print("=" * 60)
    print(f"Student ID : {student_id}")
    print(f"Name       : {student_name}")
    print(f"Department : {department}")
    print(f"Year       : {year}")
    print(f"Date       : {today}")
    print(f"Time       : {current_time}")
    print(f"Confidence : {confidence:.2f}%")
    print("=" * 60)

    return True