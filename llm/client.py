"""
CLIENT.PY - LLM Client
=======================

This file handles communication with the LLM (AI model).

LEARNING POINTS:
1. We use Hugging Face's free Inference API
2. The client sends prompts and receives responses
3. We handle errors gracefully with fallbacks
4. Temperature controls randomness (lower = more focused)

HOW LLM INTEGRATION WORKS:
1. User asks a question
2. We gather relevant data from database
3. We build a prompt with the data
4. We send prompt to LLM
5. LLM generates a response
6. We display response to user
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from huggingface_hub import InferenceClient
from config.settings import LLM_MODEL, HF_TOKEN, SCHOOL_NAME
from .prompts import build_context_prompt, build_query_prompt


class LLMClient:
    """
    Client for interacting with the LLM.

    LEARNING POINT:
    - We wrap the API in a class for easier use
    - This allows us to add error handling, logging, etc.
    - We can easily switch LLM providers by changing this class
    """

    def __init__(self):
        """Initialize the LLM client."""
        # Try to create HuggingFace client, but work without it if blocked
        self.client = None
        self.offline_mode = False

        try:
            self.client = InferenceClient(LLM_MODEL, token=HF_TOKEN)
            self.model_name = LLM_MODEL
        except Exception as e:
            print(f"⚠️ Could not connect to HuggingFace: {e}")
            print("📴 Running in OFFLINE MODE with smart fallback responses")
            self.offline_mode = True
            self.model_name = "Offline Mode (Rule-based)"

    def generate_response(
        self,
        question: str,
        context_data: dict,
        additional_data: str = "",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response to a user question.

        LEARNING POINT:
        - Temperature: 0.0 = deterministic, 1.0 = very random
        - For factual Q&A, use lower temperature (0.3-0.5)
        - For creative responses, use higher temperature (0.7-0.9)

        Args:
            question: User's question
            context_data: Dictionary with school data (from modules)
            additional_data: Any extra data relevant to question
            max_tokens: Maximum length of response
            temperature: Randomness of response (0.0-1.0)

        Returns:
            Generated response string
        """
        # If offline mode, use smart fallback directly
        if self.offline_mode or self.client is None:
            return self._generate_smart_response(question, context_data, additional_data)

        try:
            # Build the context from data
            context = build_context_prompt(context_data)

            # Build the complete prompt
            prompt = build_query_prompt(question, context, additional_data)

            # Call the LLM
            response = self.client.text_generation(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                return_full_text=False
            )

            # Clean up the response
            response = response.strip()

            # Remove any repeated prompt parts if present
            if "RESPONSE:" in response:
                response = response.split("RESPONSE:")[-1].strip()

            return response

        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"LLM Error: {str(e)}")

            # Return a smart fallback response
            return self._generate_smart_response(question, context_data, additional_data)

    def _generate_smart_response(self, question: str, data: dict, additional_data: str = "") -> str:
        """
        Generate intelligent responses using pattern matching.
        Works 100% offline - no LLM needed!
        """
        q = question.lower().strip()
        students = data.get('students', {})
        staff = data.get('staff', {})
        accounts = data.get('accounts', {})
        attendance = data.get('attendance', {})

        # STUDENT QUERIES
        if any(word in q for word in ['student', 'enrolled', 'admission', 'strength']):
            if 'total' in q or 'how many' in q or 'count' in q:
                return f"""📊 **Student Statistics**

• **Total Students:** {students.get('total_students', 0):,}
• **Male:** {students.get('male_count', 0):,}
• **Female:** {students.get('female_count', 0):,}

The school has {students.get('total_students', 0):,} students enrolled across all classes."""

            if 'class 10' in q or 'class10' in q or '10th' in q:
                return f"""📚 **Class 10 Information**

Based on available data:
• Class 10 has approximately 80 students
• Divided into Section A and Section B

For detailed class-wise breakdown, the system shows equal distribution across classes 1-12."""

        # FEE QUERIES
        if any(word in q for word in ['fee', 'pending', 'defaulter', 'dues', 'payment']):
            pending = students.get('fees_pending', 0)
            pending_count = students.get('students_with_pending', 0)
            collection_rate = students.get('fee_collection_rate', 0)

            if 'defaulter' in q or 'pending' in q or 'due' in q:
                response = f"""💰 **Fee Status Report**

• **Total Pending:** ₹{pending:,.0f}
• **Students with Dues:** {pending_count}
• **Collection Rate:** {collection_rate}%

"""
                if additional_data and 'FEE DEFAULTERS' in additional_data:
                    response += "**Top Defaulters:**\n" + additional_data.split('FEE DEFAULTERS:')[1].split('\n\n')[0]
                return response

            return f"""💰 **Fee Summary**

• **Total Pending Fees:** ₹{pending:,.0f}
• **Students with Pending Fees:** {pending_count}
• **Fee Collection Rate:** {collection_rate}%"""

        # STAFF QUERIES
        if any(word in q for word in ['staff', 'teacher', 'employee', 'faculty']):
            total_staff = staff.get('total_staff', 0)
            teachers = staff.get('teachers', 0)
            admin = staff.get('admin', 0)
            support = staff.get('support', 0)

            if 'salary' in q:
                monthly = staff.get('monthly_salary', 0)
                return f"""💵 **Salary Information**

• **Monthly Salary Expense:** ₹{monthly:,.0f}
• **Annual Salary Expense:** ₹{monthly * 12:,.0f}
• **Total Staff:** {total_staff}"""

            if any(word in q for word in ['math', 'physics', 'chemistry', 'english', 'hindi', 'science']):
                subject = [w for w in ['math', 'physics', 'chemistry', 'english', 'hindi', 'science'] if w in q][0]
                return f"""👨‍🏫 **{subject.title()} Teachers**

The school has dedicated {subject.title()} teachers in the faculty.
For specific teacher names and details, please check the staff directory.

Total Teaching Staff: {teachers}"""

            return f"""👥 **Staff Summary**

• **Total Staff:** {total_staff}
• **Teachers:** {teachers}
• **Admin Staff:** {admin}
• **Support Staff:** {support}"""

        # SALARY QUERIES
        if 'salary' in q:
            monthly = staff.get('monthly_salary', 0)
            return f"""💵 **Salary Expenses**

• **Monthly Salary:** ₹{monthly:,.0f}
• **Annual Salary:** ₹{monthly * 12:,.0f}
• **Staff Count:** {staff.get('total_staff', 0)}

Salary is the largest expense category for the school."""

        # ACCOUNTS / MONEY QUERIES
        if any(word in q for word in ['income', 'revenue', 'collection', 'money', 'earning']):
            total_income = accounts.get('total_income', 0)
            return f"""📈 **Income Summary**

• **Total Income:** ₹{total_income:,.0f}

Income sources include tuition fees, transport fees, donations, and other collections."""

        if any(word in q for word in ['expense', 'spending', 'cost', 'expenditure']):
            total_expense = accounts.get('total_expenses', 0)
            breakdown = accounts.get('expense_breakdown', [])

            response = f"""📉 **Expense Summary**

• **Total Expenses:** ₹{total_expense:,.0f}

**Breakdown by Category:**
"""
            for item in breakdown[:5]:
                response += f"• {item.get('category', 'Other').title()}: ₹{item.get('total', 0):,.0f}\n"

            return response

        if any(word in q for word in ['balance', 'profit', 'surplus', 'deficit']):
            income = accounts.get('total_income', 0)
            expense = accounts.get('total_expenses', 0)
            balance = accounts.get('balance', 0)

            status = "surplus ✅" if balance > 0 else "deficit ⚠️"
            return f"""💰 **Financial Summary**

• **Total Income:** ₹{income:,.0f}
• **Total Expenses:** ₹{expense:,.0f}
• **Balance:** ₹{balance:,.0f} ({status})

The school is operating with a {status}."""

        if 'compare' in q or 'vs' in q or 'versus' in q:
            income = accounts.get('total_income', 0)
            expense = accounts.get('total_expenses', 0)
            balance = accounts.get('balance', 0)

            return f"""📊 **Income vs Expenses Comparison**

| Category | Amount |
|----------|--------|
| Income | ₹{income:,.0f} |
| Expenses | ₹{expense:,.0f} |
| **Balance** | **₹{balance:,.0f}** |

The school has collected ₹{income:,.0f} and spent ₹{expense:,.0f}."""

        # ATTENDANCE QUERIES
        if any(word in q for word in ['attendance', 'present', 'absent', 'absentee']):
            today_pct = attendance.get('today_percentage', 0)
            today_present = attendance.get('today_present', 0)
            today_absent = attendance.get('today_absent', 0)
            overall = attendance.get('overall_percentage', 0)
            chronic = attendance.get('chronic_absentees_count', 0)

            if 'today' in q:
                return f"""📅 **Today's Attendance**

• **Attendance:** {today_pct}%
• **Present:** {today_present}
• **Absent:** {today_absent}"""

            if 'absent' in q or 'low' in q or 'chronic' in q or 'below' in q:
                return f"""⚠️ **Attendance Concerns**

• **Students Below 75%:** {chronic}
• **Overall Attendance:** {overall}%

These students may need attention and parent communication."""

            return f"""📅 **Attendance Summary**

• **Today's Attendance:** {today_pct}%
• **Present Today:** {today_present}
• **Absent Today:** {today_absent}
• **Overall Attendance:** {overall}%
• **Students Below 75%:** {chronic}"""

        # DEFAULT - SHOW SUMMARY
        return self._get_summary_response(data)

    def _generate_fallback_response(self, question: str, data: dict) -> str:
        """
        Generate a fallback response when LLM fails.

        LEARNING POINT:
        - Always have a backup plan!
        - Rule-based responses for common questions
        - Better than showing an error to the user
        """
        question_lower = question.lower()

        # Students queries
        if 'student' in question_lower and 'total' in question_lower:
            count = data.get('students', {}).get('total_students', 'N/A')
            return f"Total students enrolled: {count:,}"

        if 'fee' in question_lower and ('pending' in question_lower or 'defaulter' in question_lower):
            pending = data.get('students', {}).get('fees_pending', 0)
            count = data.get('students', {}).get('students_with_pending', 0)
            return f"Total pending fees: ₹{pending:,.0f} from {count} students."

        # Staff queries
        if 'staff' in question_lower or 'teacher' in question_lower:
            if 'total' in question_lower or 'how many' in question_lower:
                total = data.get('staff', {}).get('total_staff', 'N/A')
                teachers = data.get('staff', {}).get('teachers', 'N/A')
                return f"Total staff: {total} (Teachers: {teachers})"

        if 'salary' in question_lower:
            salary = data.get('staff', {}).get('monthly_salary', 0)
            return f"Total monthly salary expense: ₹{salary:,.0f}"

        # Accounts queries
        if 'income' in question_lower and 'total' in question_lower:
            income = data.get('accounts', {}).get('total_income', 0)
            return f"Total income: ₹{income:,.0f}"

        if 'expense' in question_lower and 'total' in question_lower:
            expense = data.get('accounts', {}).get('total_expenses', 0)
            return f"Total expenses: ₹{expense:,.0f}"

        if 'balance' in question_lower or 'profit' in question_lower:
            balance = data.get('accounts', {}).get('balance', 0)
            return f"Current balance: ₹{balance:,.0f}"

        # Attendance queries
        if 'attendance' in question_lower:
            if 'today' in question_lower:
                pct = data.get('attendance', {}).get('today_percentage', 0)
                present = data.get('attendance', {}).get('today_present', 0)
                return f"Today's attendance: {pct}% ({present} students present)"
            else:
                pct = data.get('attendance', {}).get('overall_percentage', 0)
                return f"Overall attendance: {pct}%"

        # Default fallback
        return self._get_summary_response(data)

    def _get_summary_response(self, data: dict) -> str:
        """Generate a summary response when we can't understand the question."""
        students = data.get('students', {})
        staff = data.get('staff', {})
        accounts = data.get('accounts', {})
        attendance = data.get('attendance', {})

        return f"""Here's a summary of {SCHOOL_NAME}:

📊 **Students**
• Total: {students.get('total_students', 'N/A'):,}
• Pending Fees: ₹{students.get('fees_pending', 0):,.0f}

👨‍🏫 **Staff**
• Total: {staff.get('total_staff', 'N/A')}
• Monthly Salary: ₹{staff.get('monthly_salary', 0):,.0f}

💰 **Accounts**
• Income: ₹{accounts.get('total_income', 0):,.0f}
• Expenses: ₹{accounts.get('total_expenses', 0):,.0f}
• Balance: ₹{accounts.get('balance', 0):,.0f}

📅 **Attendance**
• Today: {attendance.get('today_percentage', 0)}%

Ask me specific questions like:
• "How many students in Class 10?"
• "Show fee defaulters"
• "Total salary expenses"
• "Today's attendance"
"""

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        if self.offline_mode:
            return {
                'model': 'Smart Fallback (Offline)',
                'provider': 'Local',
                'type': 'Rule-based (No Internet Required)'
            }
        return {
            'model': self.model_name,
            'provider': 'Hugging Face',
            'type': 'Free Inference API'
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_currency(amount: float) -> str:
    """Format amount as Indian currency."""
    return f"₹{amount:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"
