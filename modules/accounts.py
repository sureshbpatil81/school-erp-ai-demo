"""
ACCOUNTS.PY - Accounts Module
==============================

This module handles all financial queries (income and expenses).

LEARNING POINTS:
1. Separate income and expense tracking
2. Category-wise breakdowns are important
3. Time-based comparisons (monthly, yearly)
4. Financial calculations need precision
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query
from datetime import datetime


class AccountsModule:
    """
    Handles all accounts-related database operations.
    """

    # =========================================================================
    # INCOME QUERIES
    # =========================================================================

    @staticmethod
    def get_total_income(start_date: str = None, end_date: str = None) -> float:
        """Get total income, optionally filtered by date range."""
        if start_date and end_date:
            query = """
                SELECT SUM(amount) as total FROM income
                WHERE date BETWEEN ? AND ?
            """
            result = execute_query(query, (start_date, end_date))
        else:
            result = execute_query("SELECT SUM(amount) as total FROM income")

        return result[0]['total'] or 0 if result else 0

    @staticmethod
    def get_income_by_category(start_date: str = None, end_date: str = None) -> list:
        """Get income breakdown by category."""
        if start_date and end_date:
            query = """
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM income
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            """
            return execute_query(query, (start_date, end_date))
        else:
            query = """
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM income
                GROUP BY category
                ORDER BY total DESC
            """
            return execute_query(query)

    @staticmethod
    def get_monthly_income(year: int = None) -> list:
        """Get month-wise income."""
        year = year or datetime.now().year
        query = """
            SELECT strftime('%Y-%m', date) as month,
                   SUM(amount) as total,
                   COUNT(*) as transactions
            FROM income
            WHERE strftime('%Y', date) = ?
            GROUP BY month
            ORDER BY month
        """
        return execute_query(query, (str(year),))

    @staticmethod
    def get_fee_collection(month: str = None) -> dict:
        """Get fee collection details."""
        if month:
            query = """
                SELECT SUM(amount) as total, COUNT(*) as count
                FROM income
                WHERE category = 'fees'
                AND strftime('%Y-%m', date) = ?
            """
            result = execute_query(query, (month,))
        else:
            query = """
                SELECT SUM(amount) as total, COUNT(*) as count
                FROM income
                WHERE category = 'fees'
            """
            result = execute_query(query)

        return result[0] if result else {'total': 0, 'count': 0}

    @staticmethod
    def get_donations(year: int = None) -> list:
        """Get donation records."""
        if year:
            query = """
                SELECT date, amount, description, payment_mode
                FROM income
                WHERE category = 'donation'
                AND strftime('%Y', date) = ?
                ORDER BY date DESC
            """
            return execute_query(query, (str(year),))
        else:
            query = """
                SELECT date, amount, description, payment_mode
                FROM income
                WHERE category = 'donation'
                ORDER BY date DESC
            """
            return execute_query(query)

    # =========================================================================
    # EXPENSE QUERIES
    # =========================================================================

    @staticmethod
    def get_total_expenses(start_date: str = None, end_date: str = None) -> float:
        """Get total expenses, optionally filtered by date range."""
        if start_date and end_date:
            query = """
                SELECT SUM(amount) as total FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            result = execute_query(query, (start_date, end_date))
        else:
            result = execute_query("SELECT SUM(amount) as total FROM expenses")

        return result[0]['total'] or 0 if result else 0

    @staticmethod
    def get_expenses_by_category(start_date: str = None, end_date: str = None) -> list:
        """Get expense breakdown by category."""
        if start_date and end_date:
            query = """
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            """
            return execute_query(query, (start_date, end_date))
        else:
            query = """
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses
                GROUP BY category
                ORDER BY total DESC
            """
            return execute_query(query)

    @staticmethod
    def get_monthly_expenses(year: int = None) -> list:
        """Get month-wise expenses."""
        year = year or datetime.now().year
        query = """
            SELECT strftime('%Y-%m', date) as month,
                   SUM(amount) as total,
                   COUNT(*) as transactions
            FROM expenses
            WHERE strftime('%Y', date) = ?
            GROUP BY month
            ORDER BY month
        """
        return execute_query(query, (str(year),))

    @staticmethod
    def get_salary_expenses(month: str = None) -> dict:
        """Get salary expense details."""
        if month:
            query = """
                SELECT SUM(amount) as total, COUNT(*) as count
                FROM expenses
                WHERE category = 'salary'
                AND strftime('%Y-%m', date) = ?
            """
            result = execute_query(query, (month,))
        else:
            query = """
                SELECT SUM(amount) as total, COUNT(*) as count
                FROM expenses
                WHERE category = 'salary'
            """
            result = execute_query(query)

        return result[0] if result else {'total': 0, 'count': 0}

    @staticmethod
    def get_utility_expenses() -> list:
        """Get utility expense breakdown."""
        query = """
            SELECT description, SUM(amount) as total, COUNT(*) as count
            FROM expenses
            WHERE category = 'utilities'
            GROUP BY description
            ORDER BY total DESC
        """
        return execute_query(query)

    # =========================================================================
    # COMBINED QUERIES
    # =========================================================================

    @staticmethod
    def get_balance(start_date: str = None, end_date: str = None) -> dict:
        """Get income, expenses, and balance."""
        income = AccountsModule.get_total_income(start_date, end_date)
        expenses = AccountsModule.get_total_expenses(start_date, end_date)

        return {
            'total_income': income,
            'total_expenses': expenses,
            'balance': income - expenses,
            'profit_margin': round((income - expenses) / income * 100, 1) if income > 0 else 0
        }

    @staticmethod
    def get_monthly_comparison(year: int = None) -> list:
        """Get month-wise income vs expenses comparison."""
        year = year or datetime.now().year

        # Get monthly income
        income_query = """
            SELECT strftime('%Y-%m', date) as month, SUM(amount) as income
            FROM income
            WHERE strftime('%Y', date) = ?
            GROUP BY month
        """
        income_data = {row['month']: row['income'] for row in execute_query(income_query, (str(year),))}

        # Get monthly expenses
        expense_query = """
            SELECT strftime('%Y-%m', date) as month, SUM(amount) as expenses
            FROM expenses
            WHERE strftime('%Y', date) = ?
            GROUP BY month
        """
        expense_data = {row['month']: row['expenses'] for row in execute_query(expense_query, (str(year),))}

        # Combine
        months = sorted(set(list(income_data.keys()) + list(expense_data.keys())))
        comparison = []
        for month in months:
            inc = income_data.get(month, 0)
            exp = expense_data.get(month, 0)
            comparison.append({
                'month': month,
                'income': inc,
                'expenses': exp,
                'balance': inc - exp
            })

        return comparison

    @staticmethod
    def get_recent_transactions(limit: int = 10) -> dict:
        """Get recent income and expense transactions."""
        recent_income = execute_query("""
            SELECT date, category, amount, description
            FROM income
            ORDER BY date DESC, id DESC
            LIMIT ?
        """, (limit,))

        recent_expenses = execute_query("""
            SELECT date, category, amount, description
            FROM expenses
            ORDER BY date DESC, id DESC
            LIMIT ?
        """, (limit,))

        return {
            'recent_income': recent_income,
            'recent_expenses': recent_expenses
        }

    @staticmethod
    def get_summary() -> dict:
        """Get overall accounts summary for dashboard."""
        balance = AccountsModule.get_balance()
        income_by_cat = AccountsModule.get_income_by_category()
        expense_by_cat = AccountsModule.get_expenses_by_category()

        return {
            'total_income': balance['total_income'],
            'total_expenses': balance['total_expenses'],
            'balance': balance['balance'],
            'top_income_category': income_by_cat[0]['category'] if income_by_cat else 'N/A',
            'top_expense_category': expense_by_cat[0]['category'] if expense_by_cat else 'N/A',
            'income_breakdown': income_by_cat,
            'expense_breakdown': expense_by_cat
        }
