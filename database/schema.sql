-- ============================================================
-- SMART CAMPUS AI ATTENDANCE SYSTEM
-- DATABASE INITIALIZATION SCHEMA (SQLite)
--
-- This script contains the DDL schema definitions derived from
-- the production application database (attendance.db).
--
-- NOTE: Contains no sensitive user credentials, student PII,
--       or private operational attendance records.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 1. STUDENTS TABLE
-- Stores enrolled student roster records.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    student_id   TEXT PRIMARY KEY,
    student_name TEXT NOT NULL,
    department   TEXT NOT NULL,
    year         TEXT NOT NULL
);

-- ------------------------------------------------------------
-- 2. ATTENDANCE TABLE
-- Stores verified automated and manual attendance logs.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    student_name TEXT NOT NULL,
    department   TEXT NOT NULL,
    year         TEXT NOT NULL,
    date         TEXT NOT NULL,
    time         TEXT NOT NULL,
    confidence   REAL NOT NULL,
    status       TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Index to optimize daily attendance deduplication queries
CREATE INDEX IF NOT EXISTS idx_attendance_student_date 
ON attendance (student_id, date);

-- ------------------------------------------------------------
-- 3. USERS TABLE
-- Stores role-based access control accounts (Admin, Staff, Student).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    username   TEXT PRIMARY KEY,
    password   TEXT,
    role       TEXT,
    student_id TEXT
);

-- ------------------------------------------------------------
-- 4. AUDIT LOGS TABLE
-- Records forensic audit events, security anomalies, and system operations.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    timestamp   TEXT,
    event_type  TEXT,
    description TEXT
);

-- ------------------------------------------------------------
-- 5. REVIEW QUEUE TABLE
-- Manages manual supervisory review items for verification disputes.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_queue (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT,
    student_name TEXT,
    confidence   REAL,
    date         TEXT,
    time         TEXT,
    status       TEXT DEFAULT 'Pending'
);

-- ------------------------------------------------------------
-- 6. AI REVIEW QUEUE TABLE
-- Staging queue for marginal AI detections requiring manual approval.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_review_queue (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT,
    student_name TEXT,
    confidence   TEXT,
    date         TEXT,
    time         TEXT,
    status       TEXT DEFAULT 'Pending'
);
