"""
STUDENTS.PY - Student Module
=============================

This module handles all student-related queries.

LEARNING POINTS:
1. Each module is a class with methods for specific queries
2. Methods return structured data (dictionaries)
3. SQL queries are parameterized for safety
4. Format functions prepare data for display
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query


class StudentModule:
    """
    Handles all student-related database operations.

    LEARNING POINT:
    - Using a class keeps related functions together
    - Makes it easy to add new student-related features
    """

    @staticmethod
    def get_total_count() -> int:
        """Get total number of students."""
        result = execute_query("SELECT COUNT(*) as count FROM students")
        return result[0]['count'] if result else 0

    @staticmethod
    def get_class_wise_count() -> list:
        """Get student count per class."""
        query = """
            SELECT class, COUNT(*) as count
            FROM students
            GROUP BY class
            ORDER BY class
        """
        return execute_query(query)

    @staticmethod
    def get_students_by_class(class_num: int, section: str = None) -> list:
        """Get all students in a specific class."""
        if section:
            query = """
                SELECT * FROM students
                WHERE class = ? AND section = ?
                ORDER BY roll_no
            """
            return execute_query(query, (class_num, section))
        else:
            query = """
                SELECT * FROM students
                WHERE class = ?
                ORDER BY section, roll_no
            """
            return execute_query(query, (class_num,))

    @staticmethod
    def get_fee_defaulters(class_num: int = None) -> list:
        """
        Get students with pending fees.

        Args:
            class_num: Optional - filter by class

        Returns:
            List of students with fees_status != 'paid'
        """
        if class_num:
            query = """
                SELECT name, class, section, fees_status, fees_pending,
                       parent_name, parent_phone
                FROM students
                WHERE fees_status != 'paid' AND class = ?
                ORDER BY fees_pending DESC
            """
            return execute_query(query, (class_num,))
        else:
            query = """
                SELECT name, class, section, fees_status, fees_pending,
                       parent_name, parent_phone
                FROM students
                WHERE fees_status != 'paid'
                ORDER BY fees_pending DESC
            """
            return execute_query(query)

    @staticmethod
    def get_total_pending_fees() -> float:
        """Get total pending fees amount."""
        result = execute_query("""
            SELECT SUM(fees_pending) as total FROM students
            WHERE fees_status != 'paid'
        """)
        return result[0]['total'] or 0 if result else 0

    @staticmethod
    def get_fee_summary() -> dict:
        """Get fee collection summary."""
        # Total fees expected
        total_expected = execute_query("""
            SELECT SUM(total_fees) as total FROM students
        """)[0]['total'] or 0

        # Total pending
        total_pending = execute_query("""
            SELECT SUM(fees_pending) as total FROM students
        """)[0]['total'] or 0

        # Count by status
        status_count = execute_query("""
            SELECT fees_status, COUNT(*) as count
            FROM students
            GROUP BY fees_status
        """)

        return {
            'total_expected': total_expected,
            'total_collected': total_expected - total_pending,
            'total_pending': total_pending,
            'status_breakdown': {row['fees_status']: row['count'] for row in status_count}
        }

    @staticmethod
    def search_student(name: str) -> list:
        """Search students by name (partial match)."""
        query = """
            SELECT * FROM students
            WHERE name LIKE ?
            ORDER BY class, section, roll_no
        """
        return execute_query(query, (f'%{name}%',))

    @staticmethod
    def get_student_details(student_id: int) -> dict:
        """Get detailed information for a specific student."""
        result = execute_query("""
            SELECT * FROM students WHERE id = ?
        """, (student_id,))
        return result[0] if result else None

    @staticmethod
    def get_gender_distribution() -> dict:
        """Get gender distribution of students."""
        result = execute_query("""
            SELECT gender, COUNT(*) as count
            FROM students
            GROUP BY gender
        """)
        return {row['gender']: row['count'] for row in result}

    @staticmethod
    def get_new_admissions(year: int = 2024) -> list:
        """Get students admitted in a specific year."""
        query = """
            SELECT name, class, section, admission_date
            FROM students
            WHERE strftime('%Y', admission_date) = ?
            ORDER BY admission_date DESC
        """
        return execute_query(query, (str(year),))

    @staticmethod
    def get_section_wise_count(class_num: int) -> list:
        """Get student count per section in a class."""
        query = """
            SELECT section, COUNT(*) as count
            FROM students
            WHERE class = ?
            GROUP BY section
            ORDER BY section
        """
        return execute_query(query, (class_num,))

    @staticmethod
    def get_summary() -> dict:
        """Get overall student summary for dashboard."""
        total = StudentModule.get_total_count()
        pending_fees = StudentModule.get_total_pending_fees()
        gender = StudentModule.get_gender_distribution()
        fee_summary = StudentModule.get_fee_summary()

        return {
            'total_students': total,
            'male_count': gender.get('M', 0),
            'female_count': gender.get('F', 0),
            'fees_pending': pending_fees,
            'students_with_pending': fee_summary['status_breakdown'].get('pending', 0) +
                                     fee_summary['status_breakdown'].get('partial', 0),
            'fee_collection_rate': round(
                (fee_summary['total_collected'] / fee_summary['total_expected'] * 100)
                if fee_summary['total_expected'] > 0 else 0, 1
            )
        }
