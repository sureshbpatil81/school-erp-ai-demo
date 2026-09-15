"""
APP.PY - Main Application Entry Point
======================================

This is the main file that runs your School ERP AI Assistant.
Start here to understand how everything connects together.

LEARNING POINTS:
1. Gradio creates the web UI (no HTML/CSS needed!)
2. We connect UI events to Python functions
3. The app loads data, sends to LLM, displays results
4. Everything runs on Hugging Face Spaces for free

HOW TO RUN LOCALLY:
    python app.py

HOW TO DEPLOY:
    Upload all files to Hugging Face Spaces

ARCHITECTURE:
    User → Gradio UI → Python Functions → Database
                                       → LLM
                     ← Format Response ←
"""

import gradio as gr
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from config.settings import SCHOOL_NAME, APP_TITLE, UI_THEME
from database.schema import create_tables
from database.demo_data import generate_all_demo_data
from modules.students import StudentModule
from modules.staff import StaffModule
from modules.accounts import AccountsModule
from modules.attendance import AttendanceModule
from llm.client import LLMClient


# =============================================================================
# INITIALIZE APPLICATION
# =============================================================================

def initialize_app():
    """
    Initialize the application - create tables and generate demo data.

    LEARNING POINT:
    - This runs once when the app starts
    - Ensures database is ready before accepting queries
    """
    print("🚀 Initializing School ERP Assistant...")
    print(f"   School: {SCHOOL_NAME}")

    # Create database tables
    create_tables()

    # Generate demo data (only if empty)
    generate_all_demo_data()

    print("✅ Initialization complete!")


# Initialize on import
initialize_app()

# Create LLM client
llm_client = LLMClient()


# =============================================================================
# DATA GATHERING FUNCTIONS
# =============================================================================

def get_all_summaries() -> dict:
    """
    Gather summary data from all modules.

    LEARNING POINT:
    - We collect data BEFORE sending to LLM
    - This gives the LLM accurate, up-to-date information
    - Separates data layer from AI layer
    """
    return {
        'students': StudentModule.get_summary(),
        'staff': StaffModule.get_summary(),
        'accounts': AccountsModule.get_summary(),
        'attendance': AttendanceModule.get_summary()
    }


def get_detailed_data(question: str) -> str:
    """
    Get additional detailed data based on the question.

    LEARNING POINT:
    - We analyze the question to fetch relevant extra data
    - This makes responses more accurate
    - We only fetch what's needed (performance)
    """
    question_lower = question.lower()
    additional_data = ""

    # Fee related questions
    if 'fee' in question_lower and ('defaulter' in question_lower or 'pending' in question_lower):
        defaulters = StudentModule.get_fee_defaulters()[:10]  # Top 10
        if defaulters:
            additional_data += "\n\nTOP FEE DEFAULTERS:\n"
            for d in defaulters:
                additional_data += f"• {d['name']} (Class {d['class']}-{d['section']}): ₹{d['fees_pending']:,.0f} pending\n"

    # Class-specific questions
    for class_num in range(1, 13):
        if f'class {class_num}' in question_lower or f'class{class_num}' in question_lower:
            students = StudentModule.get_students_by_class(class_num)
            additional_data += f"\n\nCLASS {class_num} DETAILS:\n"
            additional_data += f"• Total students: {len(students)}\n"
            sections = StudentModule.get_section_wise_count(class_num)
            for sec in sections:
                additional_data += f"• Section {sec['section']}: {sec['count']} students\n"
            break

    # Teacher/subject questions
    if 'teacher' in question_lower or 'teach' in question_lower:
        for subject in ['math', 'physics', 'chemistry', 'biology', 'english', 'hindi']:
            if subject in question_lower:
                teachers = StaffModule.get_teachers_by_subject(subject)
                if teachers:
                    additional_data += f"\n\n{subject.upper()} TEACHERS:\n"
                    for t in teachers:
                        additional_data += f"• {t['name']} ({t['designation']})\n"
                break

    # Salary questions
    if 'salary' in question_lower or 'highest paid' in question_lower:
        highest = StaffModule.get_highest_paid()[:5]
        if highest:
            additional_data += "\n\nHIGHEST PAID STAFF:\n"
            for h in highest:
                additional_data += f"• {h['name']} ({h['designation']}): ₹{h['salary']:,.0f}\n"

    # Attendance questions
    if 'absent' in question_lower:
        absentees = AttendanceModule.get_absentees()[:10]
        if absentees:
            additional_data += "\n\nRECENT ABSENTEES:\n"
            for a in absentees:
                additional_data += f"• {a['name']} (Class {a['class']}-{a['section']})\n"

    if 'chronic' in question_lower or 'below 75' in question_lower:
        chronic = AttendanceModule.get_chronic_absentees()[:10]
        if chronic:
            additional_data += "\n\nSTUDENTS BELOW 75% ATTENDANCE:\n"
            for c in chronic:
                additional_data += f"• {c['name']} (Class {c['class']}): {c['percentage']}%\n"

    # Monthly comparison
    if 'month' in question_lower and 'compare' in question_lower:
        comparison = AccountsModule.get_monthly_comparison()
        if comparison:
            additional_data += "\n\nMONTHLY COMPARISON:\n"
            for m in comparison:
                additional_data += f"• {m['month']}: Income ₹{m['income']:,.0f}, Expenses ₹{m['expenses']:,.0f}, Balance ₹{m['balance']:,.0f}\n"

    return additional_data


# =============================================================================
# CHAT FUNCTION
# =============================================================================

def chat(message: str, history: list) -> str:
    """
    Main chat function - processes user messages and returns AI responses.

    LEARNING POINT:
    - This is the "brain" of the application
    - It connects user input → data → LLM → response
    - History parameter allows for conversation context

    Args:
        message: User's question
        history: Previous conversation messages

    Returns:
        AI-generated response
    """
    if not message.strip():
        return "Please ask a question about the school."

    # Step 1: Gather current data from all modules
    context_data = get_all_summaries()

    # Step 2: Get additional detailed data based on question
    additional_data = get_detailed_data(message)

    # Step 3: Generate response using LLM
    response = llm_client.generate_response(
        question=message,
        context_data=context_data,
        additional_data=additional_data,
        max_tokens=500,
        temperature=0.5  # Lower for more focused responses
    )

    return response


# =============================================================================
# DASHBOARD DATA
# =============================================================================

def get_dashboard_stats():
    """Get statistics for the dashboard display."""
    students = StudentModule.get_summary()
    staff = StaffModule.get_summary()
    accounts = AccountsModule.get_summary()
    attendance = AttendanceModule.get_summary()

    return {
        'students': students['total_students'],
        'staff': staff['total_staff'],
        'balance': accounts['balance'],
        'attendance': attendance['today_percentage']
    }


# =============================================================================
# GRADIO UI
# =============================================================================

def create_ui():
    """
    Create the Gradio user interface.

    LEARNING POINT:
    - Gradio makes it easy to create web UIs in Python
    - No HTML/CSS/JavaScript needed!
    - Components are arranged in Blocks and Rows
    """

    # Get initial stats
    stats = get_dashboard_stats()

    with gr.Blocks(
        title=APP_TITLE,
        theme=gr.themes.Soft(),  # Nice, clean theme
        css="""
            .stat-card {
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
        """
    ) as demo:

        # Header
        gr.Markdown(f"""
        # 🏫 {SCHOOL_NAME}
        ### AI-Powered School Management Assistant

        Ask questions in plain English about students, staff, accounts, and attendance.
        """)

        # Dashboard Stats Row
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown(f"""
                <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius:10px; color:white;">
                    <div style="font-size:2em; font-weight:bold;">👨‍🎓 {stats['students']:,}</div>
                    <div>Students</div>
                </div>
                """)

            with gr.Column(scale=1):
                gr.Markdown(f"""
                <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:10px; color:white;">
                    <div style="font-size:2em; font-weight:bold;">👨‍🏫 {stats['staff']}</div>
                    <div>Staff</div>
                </div>
                """)

            with gr.Column(scale=1):
                gr.Markdown(f"""
                <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius:10px; color:white;">
                    <div style="font-size:2em; font-weight:bold;">💰 ₹{stats['balance']/100000:.1f}L</div>
                    <div>Balance</div>
                </div>
                """)

            with gr.Column(scale=1):
                gr.Markdown(f"""
                <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius:10px; color:white;">
                    <div style="font-size:2em; font-weight:bold;">📅 {stats['attendance']}%</div>
                    <div>Attendance</div>
                </div>
                """)

        gr.Markdown("---")

        # Chat Interface
        chatbot = gr.ChatInterface(
            fn=chat,
            title="💬 Ask Me Anything",
            description="Type your question below. I can help with student info, staff details, accounts, and attendance.",
            examples=[
                "How many students are enrolled?",
                "Show fee defaulters",
                "What is the total monthly salary expense?",
                "Today's attendance percentage",
                "Compare income vs expenses",
                "Who teaches Mathematics?",
                "Students with less than 75% attendance",
                "How much fees collected this month?",
                "Class 10 student count",
                "Show me the expense breakdown",
            ],
            retry_btn=None,
            undo_btn=None,
        )

        # Footer
        gr.Markdown("""
        ---
        ### 📚 Quick Guide

        **Student Queries:**
        - "Total students" / "Class-wise count"
        - "Fee defaulters" / "Pending fees"
        - "Students in Class 10"

        **Staff Queries:**
        - "How many teachers?"
        - "Who teaches [subject]?"
        - "Total salary expense"

        **Account Queries:**
        - "Total income/expenses"
        - "Monthly comparison"
        - "Fee collection this month"

        **Attendance Queries:**
        - "Today's attendance"
        - "Absent students"
        - "Students below 75%"

        ---
        *Built with ❤️ using Gradio + Hugging Face | Demo Data - Not Real Students*
        """)

    return demo


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    LEARNING POINT:
    - This block runs only when you execute: python app.py
    - It doesn't run when this file is imported elsewhere
    - create_ui().launch() starts the web server
    """
    print("\n" + "="*50)
    print(f"🏫 {SCHOOL_NAME} - AI Assistant")
    print("="*50)
    print(f"\n📊 Model: {llm_client.get_model_info()['model']}")
    print("🌐 Starting web server...")
    print("\n" + "="*50 + "\n")

    # Create and launch the UI
    demo = create_ui()
    demo.launch(
        share=False,  # Set to True to get a public URL
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,  # Default Gradio port
    )
