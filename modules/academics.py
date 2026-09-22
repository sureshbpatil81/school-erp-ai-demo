"""
ACADEMICS.PY - Academics Module
================================

This module handles exam results and academic performance queries.

LEARNING POINTS:
1. Averages alone hide problems - always look at the spread too
2. Joining results with attendance reveals *why* a student is struggling
3. Ranking queries (toppers, weakest subjects) drive the most useful reports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query
from config.settings import ATTENDANCE_THRESHOLD


class AcademicsModule:
    """Handles all exam/result related database operations."""

    PASS_MARK = 40

    @staticmethod
    def get_overall_average() -> float:
        """Get the school-wide average score."""
        result = execute_query("SELECT AVG(marks) as avg FROM exam_results")
        return round(result[0]['avg'], 1) if result and result[0]['avg'] else 0

    @staticmethod
    def get_subject_performance() -> list:
        """Average marks per subject - shows which subjects need attention."""
        query = """
            SELECT
                subject,
                ROUND(AVG(marks), 1) as average,
                ROUND(MIN(marks), 1) as lowest,
                ROUND(MAX(marks), 1) as highest,
                SUM(CASE WHEN marks < 40 THEN 1 ELSE 0 END) as fail_count,
                COUNT(*) as total
            FROM exam_results
            GROUP BY subject
            ORDER BY average DESC
        """
        return execute_query(query)

    @staticmethod
    def get_term_performance() -> list:
        """Average marks per term - shows improvement over the year."""
        query = """
            SELECT term, ROUND(AVG(marks), 1) as average, COUNT(*) as records
            FROM exam_results
            GROUP BY term
        """
        return execute_query(query)

    @staticmethod
    def get_class_performance() -> list:
        """Average marks per class."""
        query = """
            SELECT
                s.class,
                ROUND(AVG(r.marks), 1) as average,
                COUNT(DISTINCT s.id) as students
            FROM exam_results r
            JOIN students s ON r.student_id = s.id
            GROUP BY s.class
            ORDER BY s.class
        """
        return execute_query(query)

    @staticmethod
    def get_toppers(limit: int = 10, class_num: int = None) -> list:
        """Get the highest scoring students overall or within a class."""
        if class_num:
            query = """
                SELECT s.name, s.class, s.section,
                       ROUND(AVG(r.marks), 1) as average
                FROM exam_results r
                JOIN students s ON r.student_id = s.id
                WHERE s.class = ?
                GROUP BY s.id
                ORDER BY average DESC
                LIMIT ?
            """
            return execute_query(query, (class_num, limit))

        query = """
            SELECT s.name, s.class, s.section,
                   ROUND(AVG(r.marks), 1) as average
            FROM exam_results r
            JOIN students s ON r.student_id = s.id
            GROUP BY s.id
            ORDER BY average DESC
            LIMIT ?
        """
        return execute_query(query, (limit,))

    @staticmethod
    def get_students_needing_help(limit: int = 15) -> list:
        """
        Students who are failing AND have poor attendance.

        LEARNING POINT:
        - This is the single most valuable query in the whole demo: it combines
          two modules to produce an actionable list rather than a raw number.
        """
        query = """
            SELECT
                s.name,
                s.class,
                s.section,
                s.parent_phone,
                ROUND(AVG(r.marks), 1) as average,
                (
                    SELECT ROUND(
                        SUM(CASE WHEN a.status IN ('present','late') THEN 1.0 ELSE 0 END)
                        / COUNT(*) * 100, 1)
                    FROM attendance a
                    WHERE a.student_id = s.id
                ) as attendance
            FROM exam_results r
            JOIN students s ON r.student_id = s.id
            GROUP BY s.id
            HAVING average < 50 OR attendance < ?
            ORDER BY average ASC
            LIMIT ?
        """
        return execute_query(query, (ATTENDANCE_THRESHOLD, limit))

    @staticmethod
    def get_grade_distribution() -> list:
        """Count of each grade awarded - good for a bar chart."""
        query = """
            SELECT grade, COUNT(*) as count
            FROM exam_results
            GROUP BY grade
            ORDER BY
                CASE grade
                    WHEN 'A+' THEN 1 WHEN 'A' THEN 2 WHEN 'B+' THEN 3
                    WHEN 'B' THEN 4 WHEN 'C' THEN 5 WHEN 'D' THEN 6
                    ELSE 7
                END
        """
        return execute_query(query)

    @staticmethod
    def get_pass_rate() -> float:
        """Percentage of results at or above the pass mark."""
        result = execute_query("""
            SELECT ROUND(
                SUM(CASE WHEN marks >= 40 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1
            ) as rate
            FROM exam_results
        """)
        return result[0]['rate'] if result and result[0]['rate'] else 0

    @staticmethod
    def get_student_report(student_id: int) -> list:
        """Full term-wise report card for one student."""
        query = """
            SELECT term, subject, marks, grade
            FROM exam_results
            WHERE student_id = ?
            ORDER BY term, subject
        """
        return execute_query(query, (student_id,))

    @staticmethod
    def get_summary() -> dict:
        """Get overall academic summary for the dashboard."""
        subjects = AcademicsModule.get_subject_performance()

        return {
            'overall_average': AcademicsModule.get_overall_average(),
            'pass_rate': AcademicsModule.get_pass_rate(),
            'best_subject': subjects[0]['subject'] if subjects else 'N/A',
            'weakest_subject': subjects[-1]['subject'] if subjects else 'N/A',
            'subject_performance': subjects,
            'students_needing_help': len(AcademicsModule.get_students_needing_help(limit=500)),
        }
