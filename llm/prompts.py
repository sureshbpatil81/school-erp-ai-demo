"""
PROMPTS.PY - LLM Prompt Templates
==================================

This file contains all the prompts used to communicate with the LLM.

LEARNING POINTS:
1. System prompts set the AI's behavior and role
2. Context prompts provide data for the AI to use
3. Good prompts = Better AI responses
4. Be specific about what you want the AI to do

PROMPT ENGINEERING TIPS:
- Be clear about the AI's role
- Provide relevant context/data
- Specify the output format you want
- Give examples when helpful
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import SCHOOL_NAME


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
# This tells the AI who it is and how to behave

SYSTEM_PROMPT = f"""You are a helpful AI assistant for {SCHOOL_NAME}'s administrative system.

Your role is to help school staff quickly find information and answer questions about:
- Students (enrollment, classes, fees, contact details)
- Staff (teachers, admin, support, salaries)
- Accounts (income, expenses, balance, fee collection)
- Attendance (daily attendance, percentages, absentees)

IMPORTANT GUIDELINES:
1. Be concise and direct in your answers
2. Use Indian Rupee (₹) for all currency
3. Format numbers with commas (e.g., ₹1,00,000 not ₹100000)
4. When showing lists, use bullet points or tables
5. If data is not available, say so clearly
6. Be helpful and professional

FORMATTING RULES:
- For money: ₹45,000 (with ₹ symbol)
- For percentages: 94.5%
- For dates: Use DD-MMM-YYYY format (e.g., 15-Aug-2024)
- For lists: Use bullet points (•)
- Keep responses under 300 words unless detailed data is requested

You have access to real-time school data. Answer based ONLY on the provided data context.
"""


def build_context_prompt(data: dict) -> str:
    """
    Build the context prompt with actual data.

    LEARNING POINT:
    - We pass real data to the LLM so it can answer accurately
    - The LLM doesn't access the database directly
    - We control what information the LLM sees

    Args:
        data: Dictionary containing various school statistics

    Returns:
        Formatted context string for the LLM
    """

    context = f"""
=== CURRENT SCHOOL DATA ===

STUDENT SUMMARY:
• Total Students: {data.get('students', {}).get('total_students', 'N/A'):,}
• Male: {data.get('students', {}).get('male_count', 'N/A'):,}
• Female: {data.get('students', {}).get('female_count', 'N/A'):,}
• Students with Pending Fees: {data.get('students', {}).get('students_with_pending', 'N/A')}
• Total Pending Amount: ₹{data.get('students', {}).get('fees_pending', 0):,.0f}
• Fee Collection Rate: {data.get('students', {}).get('fee_collection_rate', 0)}%

STAFF SUMMARY:
• Total Staff: {data.get('staff', {}).get('total_staff', 'N/A')}
• Teachers: {data.get('staff', {}).get('teachers', 'N/A')}
• Admin Staff: {data.get('staff', {}).get('admin', 'N/A')}
• Support Staff: {data.get('staff', {}).get('support', 'N/A')}
• Monthly Salary Expense: ₹{data.get('staff', {}).get('monthly_salary', 0):,.0f}

ACCOUNTS SUMMARY:
• Total Income: ₹{data.get('accounts', {}).get('total_income', 0):,.0f}
• Total Expenses: ₹{data.get('accounts', {}).get('total_expenses', 0):,.0f}
• Current Balance: ₹{data.get('accounts', {}).get('balance', 0):,.0f}

INCOME BREAKDOWN:
"""

    # Add income breakdown
    for item in data.get('accounts', {}).get('income_breakdown', []):
        context += f"• {item.get('category', 'Unknown').title()}: ₹{item.get('total', 0):,.0f}\n"

    context += "\nEXPENSE BREAKDOWN:\n"

    # Add expense breakdown
    for item in data.get('accounts', {}).get('expense_breakdown', []):
        context += f"• {item.get('category', 'Unknown').title()}: ₹{item.get('total', 0):,.0f}\n"

    context += f"""
ATTENDANCE SUMMARY:
• Today's Date: {data.get('attendance', {}).get('today_date', 'N/A')}
• Today's Attendance: {data.get('attendance', {}).get('today_percentage', 0)}%
• Present Today: {data.get('attendance', {}).get('today_present', 0)}
• Absent Today: {data.get('attendance', {}).get('today_absent', 0)}
• Overall Attendance: {data.get('attendance', {}).get('overall_percentage', 0)}%
• Students Below 75% Attendance: {data.get('attendance', {}).get('chronic_absentees_count', 0)}
"""

    return context


def build_query_prompt(question: str, context: str, additional_data: str = "") -> str:
    """
    Build the complete prompt for answering a user question.

    Args:
        question: User's question
        context: Data context from build_context_prompt
        additional_data: Any additional data relevant to the question

    Returns:
        Complete prompt string
    """
    prompt = f"""{SYSTEM_PROMPT}

{context}

{additional_data if additional_data else ""}

USER QUESTION: {question}

Please provide a helpful, accurate response based on the data above. Be concise but complete.

RESPONSE:"""

    return prompt


# =============================================================================
# SPECIALIZED PROMPTS
# =============================================================================
# Different prompts for different types of queries

REPORT_PROMPT = """Generate a brief report based on the data provided.
Format it professionally with clear sections.
Include key numbers and insights.
Keep it under 200 words."""

COMPARISON_PROMPT = """Compare the values provided and highlight:
1. The differences (increase/decrease)
2. Percentage change if applicable
3. Any notable trends or concerns"""

SUGGESTION_PROMPT = """Based on the data, provide 2-3 actionable suggestions
for improvement. Be specific and practical."""
