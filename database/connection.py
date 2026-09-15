"""
CONNECTION.PY - Database Connection Manager
============================================

This file handles all database connections.

LEARNING POINTS:
1. SQLite is a file-based database (no server needed)
2. We use context managers (with statements) for safe connections
3. Always close connections after use to prevent memory leaks

HOW IT WORKS:
- get_connection() → Opens connection to database file
- execute_query() → Runs a SQL query and returns results
- execute_many() → Inserts multiple rows efficiently
"""

import sqlite3
from typing import List, Tuple, Any, Optional
import os

# Import settings
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """
    Create and return a database connection.

    LEARNING POINT:
    - sqlite3.connect() creates the database file if it doesn't exist
    - row_factory = sqlite3.Row allows us to access columns by name

    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This lets us use column names like row['name']
    return conn


def execute_query(query: str, params: Tuple = ()) -> List[dict]:
    """
    Execute a SELECT query and return results as list of dictionaries.

    LEARNING POINT:
    - Using parameterized queries (?) prevents SQL injection attacks
    - Never put user input directly in SQL strings!

    Args:
        query: SQL query string (use ? for parameters)
        params: Tuple of parameter values

    Returns:
        List of dictionaries, each representing a row

    Example:
        results = execute_query(
            "SELECT * FROM students WHERE class = ?",
            (10,)
        )
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        # Convert rows to dictionaries for easier use
        columns = [description[0] for description in cursor.description] if cursor.description else []
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results
    finally:
        conn.close()  # Always close connection!


def execute_write(query: str, params: Tuple = ()) -> int:
    """
    Execute an INSERT/UPDATE/DELETE query.

    Args:
        query: SQL query string
        params: Tuple of parameter values

    Returns:
        Number of rows affected
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()  # Save changes to database
        return cursor.rowcount
    finally:
        conn.close()


def execute_many(query: str, data: List[Tuple]) -> int:
    """
    Execute a query with multiple sets of parameters.
    Useful for bulk inserts.

    LEARNING POINT:
    - executemany() is much faster than running execute() in a loop
    - Use this when inserting many rows at once

    Args:
        query: SQL query string with ? placeholders
        data: List of tuples, each tuple is one row of data

    Returns:
        Number of rows affected

    Example:
        execute_many(
            "INSERT INTO students (name, class) VALUES (?, ?)",
            [("Rahul", 10), ("Priya", 9), ("Amit", 10)]
        )
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """
    result = execute_query(query, (table_name,))
    return len(result) > 0


def get_table_count(table_name: str) -> int:
    """
    Get the number of rows in a table.

    Args:
        table_name: Name of the table

    Returns:
        Number of rows
    """
    # Note: Using f-string here is safe because table_name is internal
    # Never use f-strings with user input!
    query = f"SELECT COUNT(*) as count FROM {table_name}"
    result = execute_query(query)
    return result[0]['count'] if result else 0
