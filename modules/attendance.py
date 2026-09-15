"""
ATTENDANCE.PY - Attendance Module
==================================

This module handles all attendance-related queries.

LEARNING POINTS:
1. Attendance is tracked daily per student
2. Percentage calculations are common
3. Identifying patterns (chronic absentees)
4. Date-based filtering is essential
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query
from datetime import datetime, timedelta


class AttendanceModule:
    """
    Handles all attendance-related database operations.
    """

    @staticmethod
    def get_today_attendance() -> dict:
        """Get today's attendance summary."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Get the most recent date with attendance data (for demo)
        latest = execute_query("""
            SELECT MAX(date) as latest_date FROM attendance
        """)
        use_date = latest[0]['latest_date'] if latest and latest[0]['latest_date'] else today

        query = """
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE date = ?
            GROUP BY status
        """
        result = execute_query(query, (use_date,))

        summary = {'present': 0, 'absent': 0, 'late': 0, 'date': use_date}
        for row in result:
            summary[row['status']] = row['count']

        total = summary['present'] + summary['absent'] + summary['late']
        summary['total'] = total
        summary['percentage'] = round(
            (summary['present'] + summary['late']) / total * 100, 1
        ) if total > 0 else 0

        return summary

    @staticmethod
    def get_absentees(date: str = None) -> list:
        """Get list of absent students for a date."""
        if not date:
            # Use latest date with data
            latest = execute_query("SELECT MAX(date) as d FROM attendance")
            date = latest[0]['d'] if latest else datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT s.name, s.class, s.section, s.roll_no, s.parent_phone
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ? AND a.status = 'absent'
            ORDER BY s.class, s.section, s.roll_no
        """
        return execute_query(query, (date,))

    @staticmethod
    def get_class_attendance(class_num: int, date: str = None) -> dict:
        """Get attendance for a specific class."""
        if not date:
            latest = execute_query("SELECT MAX(date) as d FROM attendance")
            date = latest[0]['d'] if latest else datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT a.status, COUNT(*) as count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ? AND s.class = ?
            GROUP BY a.status
        """
        result = execute_query(query, (date, class_num))

        summary = {'present': 0, 'absent': 0, 'late': 0, 'class': class_num, 'date': date}
        for row in result:
            summary[row['status']] = row['count']

        total = summary['present'] + summary['absent'] + summary['late']
        summary['total'] = total
        summary['percentage'] = round(
            (summary['present'] + summary['late']) / total * 100, 1
        ) if total > 0 else 0

        return summary

    @staticmethod
    def get_student_attendance(student_id: int, month: str = None) -> dict:
        """Get attendance for a specific student."""
        if month:
            query = """
                SELECT status, COUNT(*) as count
                FROM attendance
                WHERE student_id = ? AND strftime('%Y-%m', date) = ?
                GROUP BY status
            """
            result = execute_query(query, (student_id, month))
        else:
            query = """
                SELECT status, COUNT(*) as count
                FROM attendance
                WHERE student_id = ?
                GROUP BY status
            """
            result = execute_query(query, (student_id,))

        summary = {'present': 0, 'absent': 0, 'late': 0}
        for row in result:
            summary[row['status']] = row['count']

        total = summary['present'] + summary['absent'] + summary['late']
        summary['total_days'] = total
        summary['percentage'] = round(
            (summary['present'] + summary['late']) / total * 100, 1
        ) if total > 0 else 0

        return summary

    @staticmethod
    def get_monthly_attendance(month: str = None) -> dict:
        """Get overall attendance for a month."""
        if not month:
            month = datetime.now().strftime('%Y-%m')

        query = """
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY status
        """
        result = execute_query(query, (month,))

        summary = {'present': 0, 'absent': 0, 'late': 0, 'month': month}
        for row in result:
            summary[row['status']] = row['count']

        total = summary['present'] + summary['absent'] + summary['late']
        summary['total_records'] = total
        summary['percentage'] = round(
            (summary['present'] + summary['late']) / total * 100, 1
        ) if total > 0 else 0

        return summary

    @staticmethod
    def get_chronic_absentees(threshold: int = 75) -> list:
        """
        Get students with attendance below threshold percentage.

        Args:
            threshold: Minimum acceptable attendance percentage (default 75%)
        """
        query = """
            SELECT
                s.id,
                s.name,
                s.class,
                s.section,
                s.parent_phone,
                COUNT(*) as total_days,
                SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1 ELSE 0 END) as present_days,
                ROUND(SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as percentage
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            GROUP BY s.id
            HAVING percentage < ?
            ORDER BY percentage ASC
        """
        return execute_query(query, (threshold,))

    @staticmethod
    def get_class_wise_attendance() -> list:
        """Get attendance percentage by class."""
        query = """
            SELECT
                s.class,
                COUNT(*) as total_records,
                SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1 ELSE 0 END) as present_count,
                ROUND(SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as percentage
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            GROUP BY s.class
            ORDER BY s.class
        """
        return execute_query(query)

    @staticmethod
    def get_attendance_trend(days: int = 7) -> list:
        """Get daily attendance trend for recent days."""
        query = """
            SELECT
                date,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                ROUND(SUM(CASE WHEN status = 'present' OR status = 'late' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as percentage
            FROM attendance
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """
        return execute_query(query, (days,))

    @staticmethod
    def get_lowest_attendance_classes(limit: int = 5) -> list:
        """Get classes with lowest attendance."""
        query = """
            SELECT
                s.class,
                s.section,
                ROUND(SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as percentage
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            GROUP BY s.class, s.section
            ORDER BY percentage ASC
            LIMIT ?
        """
        return execute_query(query, (limit,))

    @staticmethod
    def get_summary() -> dict:
        """Get overall attendance summary for dashboard."""
        today = AttendanceModule.get_today_attendance()
        chronic = AttendanceModule.get_chronic_absentees()
        class_wise = AttendanceModule.get_class_wise_attendance()

        # Calculate overall average
        total_present = sum(c['present_count'] for c in class_wise)
        total_records = sum(c['total_records'] for c in class_wise)
        overall_percentage = round(total_present / total_records * 100, 1) if total_records > 0 else 0

        return {
            'today_percentage': today['percentage'],
            'today_present': today['present'],
            'today_absent': today['absent'],
            'today_date': today['date'],
            'overall_percentage': overall_percentage,
            'chronic_absentees_count': len(chronic),
            'lowest_class': class_wise[-1] if class_wise else None
        }
