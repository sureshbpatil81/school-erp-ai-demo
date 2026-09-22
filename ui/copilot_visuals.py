from modules.accounts import AccountsModule
from modules.students import StudentModule
from modules.attendance import AttendanceModule
from ui import charts
from ui.theme import COLORS


def _clean(text):
    return " ".join(str(text or "").lower().strip().split())


def is_visual_followup(message):
    q = _clean(message)

    if not q:
        return False

    # Explicit natural-language visualization requests
    if "pie chart" in q:
        return True

    if "show expenses as pie" in q:
        return True

    exact = {
        "pie",
        "pie chart",
        "show pie",
        "show pie chart",
        "show as pie",
        "show as pie chart",
        "show as a pie",
        "show as a pie chart",
        "show as graph",
        "show as a graph",
        "show as chart",
        "show as a chart",
        "show graph",
        "show chart",
        "graph it",
        "graph this",
        "chart it",
        "chart this",
    }

    if q in exact:
        return True

    visual = any(word in q for word in ("pie", "chart", "graph", "plot"))
    context = any(
        phrase in q
        for phrase in (
            "show as",
            "show this",
            "show that",
            "show me",
            "chart this",
            "graph this",
        )
    )

    return visual and context


def _history_text(history):
    if not history:
        return ""

    parts = []

    for turn in reversed(history):
        if isinstance(turn, (list, tuple)):
            for item in turn[:2]:
                if isinstance(item, str) and item.strip():
                    parts.append(item)

        elif isinstance(turn, dict):
            content = turn.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content)

        if len(parts) >= 6:
            break

    return " ".join(reversed(parts))


def _render(title, visual):
    return f"""
<div style="
    margin-top:12px;
    padding:22px;
    border-radius:16px;
    background:#111827;
    border:1px solid rgba(255,255,255,.10);
    color:#f8fafc;
">
    <div style="
        font-size:18px;
        font-weight:700;
        margin-bottom:14px;
    ">{title}</div>
    {visual}
</div>
"""


def build_followup_visual(message, history):
    if not is_visual_followup(message):
        return "", ""

    current = _clean(message)
    previous = _clean(_history_text(history))
    q = previous + " " + current

    wants_pie = "pie" in current

    # ---------------------------------------------------------
    # EXPENSES
    # ---------------------------------------------------------
    if any(word in q for word in (
        "expense",
        "expenses",
        "expense breakdown",
        "expense category",
    )):
        data = AccountsModule.get_expenses_by_category()

        if wants_pie:
            visual = charts.donut_chart(
                data,
                "category",
                "total",
                size=300,
                money=True,
            )

            return (
                "Here is the expense breakdown as a pie chart.",
                _render("💸 Expenses by Category", visual),
            )

        visual = charts.bar_chart(
            data,
            "category",
            "total",
            money=True,
            color=COLORS["danger"],
        )

        return (
            "Here is the expense breakdown.",
            _render("💸 Expenses by Category", visual),
        )

    # ---------------------------------------------------------
    # INCOME VS EXPENSES
    # ---------------------------------------------------------
    if any(word in q for word in (
        "income vs",
        "income versus",
        "compare income",
        "monthly comparison",
    )):
        data = AccountsModule.get_monthly_comparison()

        visual = charts.grouped_bar_chart(
            data,
            "month",
            [
                ("income", "Income", COLORS["success"]),
                ("expenses", "Expenses", COLORS["danger"]),
            ],
        )

        return (
            "Here is the income vs expenses comparison.",
            _render("📊 Income vs Expenses", visual),
        )

    # ---------------------------------------------------------
    # INCOME BREAKDOWN
    # ---------------------------------------------------------
    if any(word in q for word in (
        "income breakdown",
        "income category",
        "income source",
        "revenue breakdown",
    )):
        data = AccountsModule.get_income_by_category()

        visual = charts.donut_chart(
            data,
            "category",
            "total",
            size=300,
            money=True,
        )

        return (
            "Here is the income breakdown as a pie chart.",
            _render("📈 Income by Category", visual),
        )

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------
    if any(word in q for word in (
        "attendance",
        "absent",
        "attendance trend",
    )):
        data = AttendanceModule.get_attendance_trend(21)

        visual = charts.line_chart(
            data,
            "date",
            "percentage",
            color=COLORS["secondary"],
        )

        return (
            "Here is the attendance trend.",
            _render("📅 Attendance Trend", visual),
        )

    # ---------------------------------------------------------
    # STUDENTS BY CLASS
    # ---------------------------------------------------------
    if any(word in q for word in (
        "students by class",
        "class-wise",
        "class wise",
        "student distribution",
    )):
        data = StudentModule.get_class_wise_count()

        visual = charts.bar_chart(
            data,
            "class",
            "count",
            color=COLORS["primary"],
        )

        return (
            "Here is the student distribution by class.",
            _render("👨‍🎓 Students by Class", visual),
        )

    return "", ""
