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
            profile TEXT DEFAULT 'regular',
            transport_route TEXT,
            blood_group TEXT,
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
    # EXAM RESULTS TABLE
    # =========================================================================
    # Stores term-wise marks per student per subject.
    # This powers the "academics" view of the demo.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            subject TEXT NOT NULL,
            marks REAL NOT NULL,
            max_marks REAL DEFAULT 100,
            grade TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')

    # =========================================================================
    # CREATE INDEXES FOR FASTER QUERIES
    # =========================================================================
    # Indexes speed up searching on frequently used columns

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_class ON students(class)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_student ON exam_results(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_term ON exam_results(term)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_leave_staff ON leave_requests(staff_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_fees ON students(fees_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_date ON income(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_category ON income(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')

    conn.commit()
    conn.close()

    # Bring older database files up to date
    apply_migrations()

    print("✅ All tables created successfully!")


# =============================================================================
# MIGRATIONS
# =============================================================================
# Columns added after the first version of this app shipped.
#
# LEARNING POINT:
# CREATE TABLE IF NOT EXISTS does nothing when the table already exists - it
# will NOT add new columns. Anyone with an older school_data.db would hit
# "table students has no column named profile". Adding the column explicitly
# keeps existing databases working without forcing a delete.

NEW_COLUMNS = {
    'students': [
        ('profile', "TEXT DEFAULT 'regular'"),
        ('transport_route', 'TEXT'),
        ('blood_group', 'TEXT'),
    ],
}


def apply_migrations():
    """Add any columns that are missing from an existing database."""
    conn = get_connection()
    cursor = conn.cursor()

    for table, columns in NEW_COLUMNS.items():
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}

        for column_name, column_type in columns:
            if column_name not in existing:
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"
                )
                print(f"   🔧 Added column {table}.{column_name}")

    conn.commit()
    conn.close()


def drop_all_tables():
    """
    Drop all tables (use with caution - deletes all data!)

    LEARNING POINT:
    - Use this only for testing/resetting demo data
    - In production, NEVER drop tables without backups
    """
    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        'attendance', 'leave_requests', 'exam_results',
        'income', 'expenses', 'students', 'staff'
    ]

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
