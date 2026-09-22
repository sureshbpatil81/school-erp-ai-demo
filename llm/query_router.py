"""
Deterministic ERP query router.

Factual school/ERP questions are answered directly from the database.
The LLM is not used to invent, summarize, or guess ERP facts.
"""

import re

from modules.students import StudentModule
from modules.staff import StaffModule
from modules.accounts import AccountsModule
from modules.attendance import AttendanceModule
from modules.academics import AcademicsModule


def _q(text):
    return " ".join((text or "").lower().strip().split())


def _money(value):
    return f"₹{float(value or 0):,.0f}"


def _table(headers, rows):
    if not rows:
        return "_No records found._"

    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")

    return "\n".join(out)


def _class_number(q):
    m = re.search(r"\bclass\s*(\d{1,2})\b", q)
    if m:
        return int(m.group(1))

    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\b", q)
    if m:
        return int(m.group(1))

    return None


def answer_factual_question(question: str):
    """
    Return a deterministic answer for supported ERP questions.

    Returns:
        str: database-backed answer
        None: not an ERP factual question; caller may use the LLM
    """
    q = _q(question)

    if not q:
        return None

    # ---------------------------------------------------------
    # FEE / PAYMENT QUESTIONS
    # ---------------------------------------------------------
    fee_words = (
        "fee", "fees", "payment", "payments",
        "pending", "defaulter", "defaulters", "dues", "due"
    )

    if any(w in q for w in fee_words):

        # Detailed student list
        if any(w in q for w in (
            "name", "names", "who", "students", "student list",
            "list", "defaulter", "defaulters"
        )):
            class_num = _class_number(q)
            rows = StudentModule.get_fee_defaulters(class_num)

            table_rows = []
            for i, r in enumerate(rows, 1):
                table_rows.append([
                    i,
                    r.get("name", ""),
                    f"Class {r.get('class', '')}-{r.get('section', '')}",
                    _money(r.get("fees_pending", 0)),
                ])

            total = sum(float(r.get("fees_pending") or 0) for r in rows)

            title = "💰 **Students with Pending Fees**"
            scope = f" in Class {class_num}" if class_num else ""

            return (
                f"{title}{scope}\n\n"
                f"**Students with dues:** {len(rows)}  \n"
                f"**Total pending:** {_money(total)}\n\n"
                + _table(
                    ["#", "Student", "Class", "Pending"],
                    table_rows,
                )
            )

        # Summary only
        summary = StudentModule.get_summary()

        return (
            "💰 **Fee Status Report**\n\n"
            f"• **Total Pending:** {_money(summary['fees_pending'])}\n"
            f"• **Students with Dues:** {summary['students_with_pending']}\n"
            f"• **Collection Rate:** {summary['fee_collection_rate']}%"
        )

    # ---------------------------------------------------------
    # STUDENT COUNTS / CLASS
    # ---------------------------------------------------------
    if any(w in q for w in (
        "student count", "number of students",
        "how many students", "total students",
        "school strength", "student strength"
    )):
        total = StudentModule.get_total_count()

        return (
            "📊 **Student Count**\n\n"
            f"**Total Students:** {total:,}"
        )

    if (
        "students by class" in q
        or "class wise students" in q
        or "class-wise students" in q
        or "student distribution" in q
    ):
        rows = StudentModule.get_class_wise_count()

        return (
            "👨‍🎓 **Students by Class**\n\n"
            + _table(
                ["Class", "Students"],
                [
                    [r.get("class", ""), f"{r.get('count', 0):,}"]
                    for r in rows
                ],
            )
        )

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------
    if any(w in q for w in (
        "absent", "absentee", "absentees"
    )):
        rows = AttendanceModule.get_absentees()

        return (
            "📅 **Absent Students**\n\n"
            f"**Absent:** {len(rows)}\n\n"
            + _table(
                ["#", "Student", "Class", "Roll No."],
                [
                    [
                        i,
                        r.get("name", ""),
                        f"{r.get('class', '')}-{r.get('section', '')}",
                        r.get("roll_no", ""),
                    ]
                    for i, r in enumerate(rows, 1)
                ],
            )
        )

    if any(w in q for w in (
        "below 75", "below 75%", "chronic absentee",
        "chronic absentees", "low attendance"
    )):
        rows = AttendanceModule.get_chronic_absentees(75)

        return (
            "⚠️ **Students Below 75% Attendance**\n\n"
            f"**Students:** {len(rows)}\n\n"
            + _table(
                ["#", "Student", "Class", "Attendance"],
                [
                    [
                        i,
                        r.get("name", ""),
                        f"{r.get('class', '')}-{r.get('section', '')}",
                        f"{r.get('percentage', 0)}%",
                    ]
                    for i, r in enumerate(rows, 1)
                ],
            )
        )

    if "attendance" in q:
        today = AttendanceModule.get_today_attendance()

        return (
            "📅 **Attendance**\n\n"
            f"| Metric | Value |\n"
            f"|---|---:|\n"
            f"| Date | {today.get('date', '')} |\n"
            f"| Attendance | {today.get('percentage', 0)}% |\n"
            f"| Present | {today.get('present', 0):,} |\n"
            f"| Absent | {today.get('absent', 0):,} |\n"
            f"| Late | {today.get('late', 0):,} |"
        )

    # ---------------------------------------------------------
    # ACADEMICS
    # ---------------------------------------------------------
    if any(w in q for w in (
        "topper", "toppers", "top performer",
        "top performers", "best students"
    )):
        class_num = _class_number(q)
        rows = AcademicsModule.get_toppers(
            limit=10,
            class_num=class_num,
        )

        return (
            "🏆 **Top Performers**\n\n"
            + _table(
                ["#", "Student", "Class", "Average"],
                [
                    [
                        i,
                        r.get("name", ""),
                        f"{r.get('class', '')}-{r.get('section', '')}",
                        f"{r.get('average', 0)}%",
                    ]
                    for i, r in enumerate(rows, 1)
                ],
            )
        )

    subject = AcademicsModule.resolve_subject(q)

    # Specific subject topper / highest score.
    # This MUST run before the generic subject-performance query.
    if subject and any(w in q for w in (
        "highest", "highest score", "topper", "top",
        "best student", "best", "maximum", "max"
    )):
        rows = AcademicsModule.get_subject_toppers(subject, limit=10)

        return (
            f"🏆 **Top {subject} Students**\\n\\n"
            + _table(
                ["#", "Student", "Class", "Marks", "Grade"],
                [
                    [
                        i,
                        r.get("name", ""),
                        f"{r.get('class', '')}-{r.get('section', '')}",
                        f"{r.get('marks', 0)}%",
                        r.get("grade", ""),
                    ]
                    for i, r in enumerate(rows, 1)
                ],
            )
        )

    if subject and any(w in q for w in (
        "subject", "marks", "score", "result",
        "pass", "fail", "average"
    )):
        detail = AcademicsModule.get_subject_detail(subject)

        if detail:
            return (
                f"📝 **{detail['subject']} Performance**\n\n"
                "| Metric | Value |\n"
                "|---|---:|\n"
                f"| Average | {detail['average']}% |\n"
                f"| Pass Rate | {detail['pass_rate']}% |\n"
                f"| Passed | {detail['passed']:,} |\n"
                f"| Failed | {detail['failed']:,} |\n"
                f"| Lowest | {detail['lowest']}% |\n"
                f"| Highest | {detail['highest']}% |"
            )

    if any(w in q for w in (
        "academic performance", "subject performance",
        "performance by subject", "subjects"
    )):
        rows = AcademicsModule.get_subject_performance()

        return (
            "📝 **Subject Performance**\n\n"
            + _table(
                ["Subject", "Average", "Lowest", "Highest", "Fails"],
                [
                    [
                        r.get("subject", ""),
                        f"{r.get('average', 0)}%",
                        f"{r.get('lowest', 0)}%",
                        f"{r.get('highest', 0)}%",
                        r.get("fail_count", 0),
                    ]
                    for r in rows
                ],
            )
        )

    # ---------------------------------------------------------
    # STAFF / TEACHERS
    # ---------------------------------------------------------
    if any(w in q for w in (
        "teacher", "teachers", "staff", "faculty"
    )):
        # Subject teacher lookup
        subject_words = {
            "math": "math",
            "maths": "math",
            "mathematics": "math",
            "science": "science",
            "physics": "physics",
            "chemistry": "chemistry",
            "biology": "biology",
            "english": "english",
            "hindi": "hindi",
        }

        subject_key = next(
            (key for key in subject_words if key in q),
            None,
        )

        if subject_key:
            rows = StaffModule.get_teachers_by_subject(
                subject_words[subject_key]
            )

            return (
                f"👨‍🏫 **{subject_key.title()} Teachers**\n\n"
                + _table(
                    ["Teacher", "Designation", "Department", "Phone"],
                    [
                        [
                            r.get("name", ""),
                            r.get("designation", ""),
                            r.get("department", ""),
                            r.get("phone", ""),
                        ]
                        for r in rows
                    ],
                )
            )

        summary = StaffModule.get_summary()

        return (
            "👥 **Staff Summary**\n\n"
            "| Metric | Value |\n"
            "|---|---:|\n"
            f"| Total Staff | {summary['total_staff']} |\n"
            f"| Teachers | {summary['teachers']} |\n"
            f"| Admin | {summary['admin']} |\n"
            f"| Support | {summary['support']} |"
        )

    # ---------------------------------------------------------
    # SALARY
    # ---------------------------------------------------------
    if "salary" in q or "salaries" in q:
        monthly = StaffModule.get_total_monthly_salary()

        return (
            "💵 **Salary Expense**\n\n"
            "| Metric | Amount |\n"
            "|---|---:|\n"
            f"| Monthly | {_money(monthly)} |\n"
            f"| Annual | {_money(monthly * 12)} |"
        )

    # ---------------------------------------------------------
    # EXPENSES
    # ---------------------------------------------------------
    if any(w in q for w in (
        "expense", "expenses", "expenditure",
        "spending", "cost"
    )):
        total = AccountsModule.get_total_expenses()
        rows = AccountsModule.get_expenses_by_category()

        return (
            "📉 **Expense Summary**\n\n"
            f"**Total Expenses:** {_money(total)}\n\n"
            + _table(
                ["Category", "Amount"],
                [
                    [
                        str(r.get("category", "")).title(),
                        _money(r.get("total", 0)),
                    ]
                    for r in rows
                ],
            )
        )

    # ---------------------------------------------------------
    # INCOME VS EXPENSES
    # ---------------------------------------------------------
    if (
        "income vs" in q
        or "income versus" in q
        or "compare income" in q
        or "compare expenses" in q
    ):
        data = AccountsModule.get_balance()

        return (
            "📊 **Income vs Expenses**\n\n"
            "| Category | Amount |\n"
            "|---|---:|\n"
            f"| Income | {_money(data['total_income'])} |\n"
            f"| Expenses | {_money(data['total_expenses'])} |\n"
            f"| **Balance** | **{_money(data['balance'])}** |"
        )

    # ---------------------------------------------------------
    # INCOME
    # ---------------------------------------------------------
    if any(w in q for w in (
        "income", "revenue", "earnings", "collection"
    )):
        total = AccountsModule.get_total_income()
        rows = AccountsModule.get_income_by_category()

        return (
            "📈 **Income Summary**\n\n"
            f"**Total Income:** {_money(total)}\n\n"
            + _table(
                ["Category", "Amount"],
                [
                    [
                        str(r.get("category", "")).title(),
                        _money(r.get("total", 0)),
                    ]
                    for r in rows
                ],
            )
        )

    # ---------------------------------------------------------
    # Nothing deterministic matched.
    # Let the LLM handle genuinely open-ended questions.
    # ---------------------------------------------------------
    return None
