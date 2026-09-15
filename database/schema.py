"""
SCHEMA.PY - Database Table Definitions
=======================================

This file defines the structure of all database tables.

LEARNING POINTS:
1. Each table represents an entity (students, staff, etc.)
2. PRIMARY KEY = unique identifier for each row
3. FOREIGN KEY = links to another table (relationships)
4. We use TEXT for strings, INTEGER for numbers, REAL for decimals

DATABASE DESIGN TIPS:
- Keep tables focused (one purpose each)
- Use meaningful column names
- Always have a primary key
- Think about what queries you'll need
"""

import sqlite3
from .connection import get_connection


def create_tables():
    """
    Create all database tables if they don't exist.

    LEARNING POINT:
    - CREATE TABLE IF NOT EXISTS = only creates if table doesn't exist
    - This is safe to run multiple times
    """
    conn = get_connection()
    cursor = conn.cursor()

    # =========================================================================
    # STUDENTS TABLE
    # =========================================================================
    # Stores all student information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class INTEGER NOT NULL,
            section TEXT NOT NULL,
            roll_no INTEGER NOT NULL,
            gender TEXT NOT NULL,
            dob TEXT,
            admission_date TEXT,
            parent_name TEXT NOT NULL,
            parent_phone TEXT NOT NULL,
            parent_email TEXT,
            address TEXT,
            fees_status TEXT DEFAULT 'pending',
            fees_pending REAL DEFAULT 0,
            total_fees REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================================
    # STAFF TABLE
    # =========================================================================
    # Stores all staff information (teachers, admin, support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            designation TEXT NOT NULL,
            department TEXT,
            subject TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            salary REAL NOT NULL,
            joining_date TEXT,
            leave_balance INTEGER DEFAULT 12,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================================
    # INCOME TABLE
    # =========================================================================
    # Stores all money coming IN (fees, donations, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            student_id INTEGER,
            description TEXT,
            payment_mode TEXT DEFAULT 'cash',
            receipt_no TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')

    # =========================================================================
    # EXPENSES TABLE
    # =========================================================================
    # Stores all money going OUT (salaries, bills, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_to TEXT NOT NULL,
            description TEXT,
            payment_mode TEXT DEFAULT 'bank',
            voucher_no TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =========================================================================
    # ATTENDANCE TABLE
    # =========================================================================
    # Stores daily attendance records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            marked_by INTEGER,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (marked_by) REFERENCES staff (id)
        )
    ''')

    # =========================================================================
    # LEAVE REQUESTS TABLE
    # =========================================================================
    # Stores staff leave requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            leave_type TEXT DEFAULT 'casual',
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff (id)
        )
    ''')

    # =========================================================================
    # CREATE INDEXES FOR FASTER QUERIES
    # =========================================================================
    # Indexes speed up searching on frequently used columns

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_class ON students(class)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_fees ON students(fees_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_date ON income(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_category ON income(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')

    conn.commit()
    conn.close()

    print("✅ All tables created successfully!")


def drop_all_tables():
    """
    Drop all tables (use with caution - deletes all data!)

    LEARNING POINT:
    - Use this only for testing/resetting demo data
    - In production, NEVER drop tables without backups
    """
    conn = get_connection()
    cursor = conn.cursor()

    tables = ['attendance', 'leave_requests', 'income', 'expenses', 'students', 'staff']

    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
        print(f"Dropped table: {table}")

    conn.commit()
    conn.close()
    print("✅ All tables dropped!")


def reset_database():
    """
    Reset the database (drop all tables and recreate).
    Use for fresh start with new demo data.
    """
    drop_all_tables()
    create_tables()
    print("✅ Database reset complete!")
