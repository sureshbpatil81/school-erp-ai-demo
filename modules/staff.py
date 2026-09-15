"""
STAFF.PY - Staff Module
========================

This module handles all staff-related queries (teachers, admin, support).

LEARNING POINTS:
1. Staff has different roles with different queries
2. We separate concerns (teaching vs admin vs support)
3. Salary calculations are common queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query


class StaffModule:
    """
    Handles all staff-related database operations.
    """

    @staticmethod
    def get_total_count() -> int:
        """Get total number of staff members."""
        result = execute_query("SELECT COUNT(*) as count FROM staff")
        return result[0]['count'] if result else 0

    @staticmethod
    def get_count_by_role() -> dict:
        """Get staff count by role (teacher/admin/support)."""
        result = execute_query("""
            SELECT role, COUNT(*) as count
            FROM staff
            GROUP BY role
        """)
        return {row['role']: row['count'] for row in result}

    @staticmethod
    def get_all_teachers() -> list:
        """Get all teaching staff."""
        query = """
            SELECT id, name, designation, department, subject, phone, salary
            FROM staff
            WHERE role = 'teacher' AND status = 'active'
            ORDER BY designation, name
        """
        return execute_query(query)

    @staticmethod
    def get_teachers_by_subject(subject: str) -> list:
        """Get teachers who teach a specific subject."""
        query = """
            SELECT name, designation, department, phone
            FROM staff
            WHERE role = 'teacher' AND subject LIKE ?
            ORDER BY designation
        """
        return execute_query(query, (f'%{subject}%',))

    @staticmethod
    def get_teachers_by_department(department: str) -> list:
        """Get teachers in a specific department."""
        query = """
            SELECT name, designation, subject, phone
            FROM staff
            WHERE role = 'teacher' AND department LIKE ?
            ORDER BY designation, name
        """
        return execute_query(query, (f'%{department}%',))

    @staticmethod
    def get_admin_staff() -> list:
        """Get all administrative staff."""
        query = """
            SELECT name, designation, phone, salary
            FROM staff
            WHERE role = 'admin' AND status = 'active'
            ORDER BY designation
        """
        return execute_query(query)

    @staticmethod
    def get_support_staff() -> list:
        """Get all support staff."""
        query = """
            SELECT name, designation, phone, salary
            FROM staff
            WHERE role = 'support' AND status = 'active'
            ORDER BY designation
        """
        return execute_query(query)

    @staticmethod
    def get_total_monthly_salary() -> float:
        """Get total monthly salary expense."""
        result = execute_query("""
            SELECT SUM(salary) as total FROM staff
            WHERE status = 'active'
        """)
        return result[0]['total'] or 0 if result else 0

    @staticmethod
    def get_salary_by_role() -> list:
        """Get total salary expense by role."""
        query = """
            SELECT role, SUM(salary) as total, COUNT(*) as count
            FROM staff
            WHERE status = 'active'
            GROUP BY role
        """
        return execute_query(query)

    @staticmethod
    def get_staff_on_leave() -> list:
        """Get staff currently on leave."""
        query = """
            SELECT s.name, s.designation, s.role, l.date, l.leave_type
            FROM staff s
            JOIN leave_requests l ON s.id = l.staff_id
            WHERE l.status = 'approved'
            AND l.date >= date('now')
            ORDER BY l.date
        """
        return execute_query(query)

    @staticmethod
    def get_leave_balance(staff_id: int = None) -> list:
        """Get leave balance for staff."""
        if staff_id:
            query = """
                SELECT name, designation, leave_balance
                FROM staff
                WHERE id = ? AND status = 'active'
            """
            return execute_query(query, (staff_id,))
        else:
            query = """
                SELECT name, designation, leave_balance
                FROM staff
                WHERE status = 'active'
                ORDER BY leave_balance
            """
            return execute_query(query)

    @staticmethod
    def search_staff(name: str) -> list:
        """Search staff by name."""
        query = """
            SELECT * FROM staff
            WHERE name LIKE ?
            ORDER BY role, name
        """
        return execute_query(query, (f'%{name}%',))

    @staticmethod
    def get_staff_details(staff_id: int) -> dict:
        """Get detailed information for a specific staff member."""
        result = execute_query("""
            SELECT * FROM staff WHERE id = ?
        """, (staff_id,))
        return result[0] if result else None

    @staticmethod
    def get_highest_paid() -> list:
        """Get top 10 highest paid staff members."""
        query = """
            SELECT name, designation, role, salary
            FROM staff
            WHERE status = 'active'
            ORDER BY salary DESC
            LIMIT 10
        """
        return execute_query(query)

    @staticmethod
    def get_new_joiners(year: int = 2024) -> list:
        """Get staff who joined in a specific year."""
        query = """
            SELECT name, designation, role, joining_date
            FROM staff
            WHERE strftime('%Y', joining_date) = ?
            ORDER BY joining_date DESC
        """
        return execute_query(query, (str(year),))

    @staticmethod
    def get_summary() -> dict:
        """Get overall staff summary for dashboard."""
        total = StaffModule.get_total_count()
        by_role = StaffModule.get_count_by_role()
        salary_total = StaffModule.get_total_monthly_salary()

        return {
            'total_staff': total,
            'teachers': by_role.get('teacher', 0),
            'admin': by_role.get('admin', 0),
            'support': by_role.get('support', 0),
            'monthly_salary': salary_total,
            'annual_salary': salary_total * 12
        }
