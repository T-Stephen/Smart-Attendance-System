import sqlite3
import os

DATABASE_PATH = "database/attendance.db"


def create_database():

    # Create database folder
    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # =====================================================
    # STUDENTS TABLE
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL
    )
    """)

    # =====================================================
    # ATTENDANCE TABLE
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,

        department TEXT NOT NULL,
        year TEXT NOT NULL,

        date TEXT NOT NULL,
        time TEXT NOT NULL,

        confidence REAL NOT NULL,

        status TEXT NOT NULL,

        FOREIGN KEY(student_id)
        REFERENCES students(student_id)
    )
    """)

    conn.commit()
    conn.close()

    print("=" * 60)
    print("        DATABASE CREATED SUCCESSFULLY")
    print("=" * 60)
    print("Students Table   : Ready")
    print("Attendance Table : Ready")
    print("Database File    :", DATABASE_PATH)
    print("=" * 60)


if __name__ == "__main__":
    create_database()