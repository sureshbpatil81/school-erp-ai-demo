"""
APP.PY - Main Application Entry Point
======================================

This is the main file that runs the School ERP AI Assistant.
Start here to understand how everything connects together.

LEARNING POINTS:
1. Gradio creates the web UI (no HTML/CSS/JS build step needed)
2. We connect UI events to Python functions
3. The app loads data, sends it to the LLM, and displays the result
4. Everything runs on Hugging Face Spaces for free

HOW TO RUN LOCALLY:
    python app.py

HOW TO REGENERATE DEMO DATA:
    python -m database.demo_data --force

ARCHITECTURE:
    config/    settings and tuning knobs
    database/  schema, connection, demo data generator
    modules/   one class per domain, returns plain dicts (the "tools")
    llm/       prompt building and model client
    ui/        theme, charts, cards, views  (all presentation)
    app.py     wiring only - this file stays thin on purpose

    User -> Gradio UI -> app.py -> modules -> SQLite
                                -> llm     -> response
"""

import sys
import os

import gradio as gr

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import SCHOOL_NAME, APP_TITLE, ATTENDANCE_THRESHOLD
from database.schema import create_tables
from database.demo_data import generate_all_demo_data
from modules.students import StudentModule
from modules.staff import StaffModule
from modules.accounts import AccountsModule
from modules.attendance import AttendanceModule
from modules.academics import AcademicsModule
from llm.client import LLMClient
from ui.theme import CUSTOM_CSS
from ui import views


# =============================================================================
# INITIALIZE APPLICATION
# =============================================================================

def initialize_app():
    """
    Initialize the application - create tables and generate demo data.

    LEARNING POINT:
    - This runs once when the app starts
    - Ensures the database is ready before accepting queries
    """
    print("🚀 Initializing School ERP Assistant...")
    print(f"   School: {SCHOOL_NAME}")

    create_tables()
    generate_all_demo_data()

    print("✅ Initialization complete!")


initialize_app()

llm_client = LLMClient()


# =============================================================================
# DATA GATHERING FUNCTIONS
# =============================================================================

def get_all_summaries() -> dict:
    """
    Gather summary data from all modules.

    LEARNING POINT:
    - We collect data BEFORE sending it to the LLM
    - This gives the LLM accurate, up-to-date information
    - It keeps the data layer separate from the AI layer
    """
    return {
        'students': StudentModule.get_summary(),
        'staff': StaffModule.get_summary(),
        'accounts': AccountsModule.get_summary(),
        'attendance': AttendanceModule.get_summary(),
        'academics': AcademicsModule.get_summary(),
    }


def get_detailed_data(question: str) -> str:
    """
    Get additional detailed data based on the question.

    LEARNING POINT:
    - We inspect the question to decide which extra query to run
    - Only fetching what is needed keeps responses fast
    - This is a simple, readable stand-in for full "tool calling"
    """
    q = question.lower()
    extra = ""

    # --- Fees ---------------------------------------------------------------
    if 'fee' in q and any(w in q for w in ['defaulter', 'pending', 'due', 'outstanding']):
        defaulters = StudentModule.get_fee_defaulters()[:10]
        if defaulters:
            extra += "\n\nTOP FEE DEFAULTERS:\n"
            for d in defaulters:
                extra += (f"• {d['name']} (Class {d['class']}-{d['section']}): "
                          f"₹{d['fees_pending']:,.0f} pending, parent {d['parent_phone']}\n")

    # --- Class specific -----------------------------------------------------
    for class_num in range(12, 0, -1):  # check 12 before 1 so "class 12" wins
        if f'class {class_num}' in q or f'class{class_num}' in q:
            students = StudentModule.get_students_by_class(class_num)
            extra += f"\n\nCLASS {class_num} DETAILS:\n"
            extra += f"• Total students: {len(students)}\n"
            for sec in StudentModule.get_section_wise_count(class_num):
                extra += f"• Section {sec['section']}: {sec['count']} students\n"
            att = AttendanceModule.get_class_attendance(class_num)
            extra += f"• Attendance: {att['percentage']}%\n"
            break

    # --- Teachers / subjects ------------------------------------------------
    if 'teacher' in q or 'teach' in q:
        for subject in ['math', 'physics', 'chemistry', 'biology', 'english',
                        'hindi', 'computer', 'sanskrit', 'art', 'music']:
            if subject in q:
                teachers = StaffModule.get_teachers_by_subject(subject)
                if teachers:
                    extra += f"\n\n{subject.upper()} TEACHERS:\n"
                    for t in teachers:
                        extra += f"• {t['name']} ({t['designation']}), {t['phone']}\n"
                break

    # --- Salary -------------------------------------------------------------
    if 'salary' in q or 'highest paid' in q:
        for h in StaffModule.get_highest_paid()[:5]:
            extra = extra or ""
            if 'HIGHEST PAID' not in extra:
                extra += "\n\nHIGHEST PAID STAFF:\n"
            extra += f"• {h['name']} ({h['designation']}): ₹{h['salary']:,.0f}\n"

    # --- Leave --------------------------------------------------------------
    if 'leave' in q:
        pending = StaffModule.get_pending_leave_requests()[:8]
        if pending:
            extra += "\n\nPENDING LEAVE REQUESTS:\n"
            for p in pending:
                extra += f"• {p['name']} - {p['leave_type']} on {p['date']} ({p['reason']})\n"

    # --- Attendance ---------------------------------------------------------
    if 'absent' in q:
        absentees = AttendanceModule.get_absentees()[:10]
        if absentees:
            extra += "\n\nABSENT TODAY:\n"
            for a in absentees:
                extra += f"• {a['name']} (Class {a['class']}-{a['section']}), {a['parent_phone']}\n"

    if 'chronic' in q or 'below 75' in q or 'low attendance' in q:
        chronic = AttendanceModule.get_chronic_absentees()[:10]
        if chronic:
            extra += f"\n\nSTUDENTS BELOW {ATTENDANCE_THRESHOLD}% ATTENDANCE:\n"
            for c in chronic:
                extra += (f"• {c['name']} (Class {c['class']}): {c['percentage']}% "
                          f"- parent {c['parent_phone']}\n")

    # --- Academics ----------------------------------------------------------
    if any(w in q for w in ['topper', 'top performer', 'best student', 'rank']):
        for t in AcademicsModule.get_toppers(10):
            if 'TOP PERFORMERS' not in extra:
                extra += "\n\nTOP PERFORMERS:\n"
            extra += f"• {t['name']} (Class {t['class']}-{t['section']}): {t['average']}%\n"

    if any(w in q for w in ['subject', 'marks', 'score', 'result', 'exam', 'grade',
                            'pass', 'fail', 'average']):
        subjects = AcademicsModule.get_subject_performance()
        if subjects:
            extra += "\n\nSUBJECT PERFORMANCE:\n"
            for s in subjects:
                extra += (f"• {s['subject']}: avg {s['average']}%, "
                          f"{s['fail_count']} fails\n")

    # If a specific subject is named ("how many pass in maths"), give the model
    # that subject's own pass/fail numbers - the averages above cannot answer it.
    named_subject = AcademicsModule.resolve_subject(q)
    if named_subject and not any(w in q for w in ['teach', 'teacher', 'faculty']):
        d = AcademicsModule.get_subject_detail(named_subject)
        if d:
            extra += (f"\n\n{d['subject'].upper()} DETAIL:\n"
                      f"• Passed: {d['passed']} of {d['total']} ({d['pass_rate']}%)\n"
                      f"• Failed: {d['failed']}\n"
                      f"• Average: {d['average']}%, range {d['lowest']}-{d['highest']}%\n")

    if 'struggling' in q or 'needs help' in q or 'at risk' in q or 'weak' in q:
        for s in AcademicsModule.get_students_needing_help(10):
            if 'STUDENTS NEEDING SUPPORT' not in extra:
                extra += "\n\nSTUDENTS NEEDING SUPPORT:\n"
            extra += (f"• {s['name']} (Class {s['class']}): avg {s['average']}%, "
                      f"attendance {s['attendance']}%\n")

    # --- Monthly comparison -------------------------------------------------
    if 'month' in q and ('compare' in q or 'trend' in q or 'vs' in q):
        for m in AccountsModule.get_monthly_comparison():
            if 'MONTHLY COMPARISON' not in extra:
                extra += "\n\nMONTHLY COMPARISON:\n"
            extra += (f"• {m['month']}: Income ₹{m['income']:,.0f}, "
                      f"Expenses ₹{m['expenses']:,.0f}, Balance ₹{m['balance']:,.0f}\n")

    return extra


# =============================================================================
# CHAT FUNCTION
# =============================================================================

def chat(message: str, history: list) -> str:
    """
    Main chat function - processes user messages and returns AI responses.

    LEARNING POINT:
    - This is the "brain" of the application
    - It connects user input -> data -> LLM -> response

    Args:
        message: User's question
        history: Previous conversation messages (unused, kept for Gradio's API)

    Returns:
        AI-generated response
    """
    if not message or not message.strip():
        return "Please ask a question about the school."

    try:
        context_data = get_all_summaries()
        additional_data = get_detailed_data(message)

        return llm_client.generate_response(
            question=message,
            context_data=context_data,
            additional_data=additional_data,
            max_tokens=500,
            temperature=0.5,
        )
    except Exception as exc:
        # A demo should never show a raw traceback to the audience
        print(f"Chat error: {exc}")
        return (
            "⚠️ Something went wrong while looking that up. "
            "Please try rephrasing your question."
        )


# =============================================================================
# GRADIO UI
# =============================================================================

EXAMPLE_QUESTIONS = [
    "How many students are enrolled?",
    "Show me the fee defaulters",
    "Which students are below 75% attendance?",
    "Who are the top performers?",
    "Compare income vs expenses by month",
    "What is the total monthly salary expense?",
    "Who teaches Mathematics?",
    "Which subject needs the most attention?",
    "Show pending leave requests",
    "Which students are struggling?",
]


def build_chat_interface() -> gr.ChatInterface:
    """
    Build the chat tab.

    LEARNING POINT:
    - Gradio 4 accepted retry_btn/undo_btn; Gradio 5 removed them and raises
      a TypeError. Passing them unconditionally means the app crashes on
      startup for anyone on the current release.
    - Building kwargs dynamically keeps this working on both versions.
    """
    kwargs = dict(
        fn=chat,
        examples=EXAMPLE_QUESTIONS,
        cache_examples=False,
    )

    major = int(gr.__version__.split('.')[0])
    if major < 5:
        kwargs['retry_btn'] = None
        kwargs['undo_btn'] = None

    return gr.ChatInterface(**kwargs)


def create_ui():
    """
    Create the Gradio user interface.

    LEARNING POINT:
    - gr.HTML holds our custom dashboard markup
    - Each tab has a Refresh button wired to the matching ui.views builder,
      so the numbers can be re-read from the database without a restart
    """
    model_label = llm_client.get_model_info()['model']

    with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft(
        primary_hue="indigo", secondary_hue="blue",
    ), css=CUSTOM_CSS) as demo:

        header = gr.HTML(views.build_header(SCHOOL_NAME, model_label))

        with gr.Tabs():
            # ---------------- Overview --------------------------------------
            # NOTE: the dashboard is deliberately the FIRST tab. Gradio renders
            # whichever tab comes first on load, so putting the chat here meant
            # visitors landed on a text box and never saw the charts.
            with gr.Tab("📊 Overview"):
                overview_btn = gr.Button("🔄 Refresh", size="sm")
                overview_html = gr.HTML(views.build_overview())
                overview_btn.click(views.build_overview, outputs=overview_html)

            # ---------------- Chat ------------------------------------------
            with gr.Tab("💬 Ask AI"):
                gr.Markdown(
                    "Ask anything about students, staff, accounts, attendance "
                    "or exam results — in plain English."
                )
                build_chat_interface()

            # ---------------- Students --------------------------------------
            with gr.Tab("👨‍🎓 Students"):
                students_btn = gr.Button("🔄 Refresh", size="sm")
                students_html = gr.HTML(views.build_students())
                students_btn.click(views.build_students, outputs=students_html)

            # ---------------- Staff -----------------------------------------
            with gr.Tab("👨‍🏫 Staff"):
                staff_btn = gr.Button("🔄 Refresh", size="sm")
                staff_html = gr.HTML(views.build_staff())
                staff_btn.click(views.build_staff, outputs=staff_html)

            # ---------------- Accounts --------------------------------------
            with gr.Tab("💰 Accounts"):
                accounts_btn = gr.Button("🔄 Refresh", size="sm")
                accounts_html = gr.HTML(views.build_accounts())
                accounts_btn.click(views.build_accounts, outputs=accounts_html)

            # ---------------- Attendance ------------------------------------
            with gr.Tab("📅 Attendance"):
                attendance_btn = gr.Button("🔄 Refresh", size="sm")
                attendance_html = gr.HTML(views.build_attendance())
                attendance_btn.click(views.build_attendance, outputs=attendance_html)

            # ---------------- Academics -------------------------------------
            with gr.Tab("📝 Academics"):
                academics_btn = gr.Button("🔄 Refresh", size="sm")
                academics_html = gr.HTML(views.build_academics())
                academics_btn.click(views.build_academics, outputs=academics_html)

            # ---------------- Guide -----------------------------------------
            with gr.Tab("📚 Guide"):
                gr.Markdown(f"""
### What you can ask

| Area | Example questions |
|------|-------------------|
| **Students** | "Total students", "Fee defaulters", "Students in Class 10", "Transport routes" |
| **Staff** | "How many teachers?", "Who teaches Physics?", "Total salary expense", "Pending leave requests" |
| **Accounts** | "Total income", "Expense breakdown", "Compare income vs expenses", "This month's balance" |
| **Attendance** | "Today's attendance", "Who is absent?", "Students below {ATTENDANCE_THRESHOLD}%" |
| **Academics** | "Top performers", "Which subject is weakest?", "Grade distribution", "Students struggling" |

### Suggested demo flow

1. **Overview** — headline KPIs and the "needs attention" panel
2. **Ask AI** — *"Which students are below {ATTENDANCE_THRESHOLD}% attendance?"*
3. **Attendance** — show the same students in the dashboard table
4. **Academics** — *"Which students are struggling?"* ties low marks to low attendance
5. **Accounts** — month-on-month income vs expenses

### Regenerating the demo data

```bash
python -m database.demo_data --force
```

Data is generated from a fixed random seed, so the numbers are identical
every time you run the demo — but all dates roll forward relative to today.

*All data is randomly generated. No real student information is used.*
                """)

        gr.HTML(
            '<div class="app-footer">Built with Gradio + SQLite · '
            'Demo data only — not real students</div>'
        )

        # Refresh the header chips whenever the app is loaded
        demo.load(lambda: views.build_header(SCHOOL_NAME, model_label), outputs=header)

    return demo


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    LEARNING POINT:
    - This block runs only when you execute: python app.py
    - It does not run when this file is imported elsewhere

    DEPLOYMENT NOTE (Render):
    - Render assigns a random port and exposes it as the PORT env var.
      Binding to a hardcoded 7860 makes the health check fail and Render
      kills the service with "no open ports detected".
    - We must also bind 0.0.0.0 (not 127.0.0.1) so the platform's proxy
      can reach the container.
    - Locally, PORT is usually unset, so we fall back to 7860.
    """
    port = int(os.environ.get("PORT", 7860))

    print("\n" + "=" * 50)
    print(f"🏫 {SCHOOL_NAME} - AI Assistant")
    print("=" * 50)
    print(f"\n📊 Model: {llm_client.get_model_info()['model']}")
    print(f"🎨 Gradio: {gr.__version__}")
    print(f"🌐 Starting web server on 0.0.0.0:{port} ...")
    print("\n" + "=" * 50 + "\n")

    create_ui().queue().launch(
        share=False,
        server_name="0.0.0.0",
        server_port=port,
        show_api=False,
    )
