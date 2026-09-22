"""
VIEWS.PY - Dashboard view builders
===================================

Each function here returns a finished HTML string for one tab of the app.
app.py only has to decide *when* to call them, not *what* they contain.

LEARNING POINT:
Keeping data access (modules/), presentation (ui/) and wiring (app.py) in
separate layers is what lets you redesign the dashboard without touching a
single SQL query.
"""

from datetime import datetime

from modules.students import StudentModule
from modules.staff import StaffModule
from modules.accounts import AccountsModule
from modules.attendance import AttendanceModule
from modules.academics import AcademicsModule
from config.settings import ATTENDANCE_THRESHOLD

from .theme import COLORS
from . import charts, cards


def _lakhs(value: float) -> str:
    """Compact rupee display for KPI tiles."""
    value = float(value or 0)
    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f}Cr"
    if abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:.1f}L"
    return f"₹{value:,.0f}"


# =============================================================================
# OVERVIEW TAB
# =============================================================================

def build_overview() -> str:
    """Top-level KPIs, alerts and the two headline charts."""
    students = StudentModule.get_summary()
    staff = StaffModule.get_summary()
    accounts = AccountsModule.get_summary()
    attendance = AttendanceModule.get_summary()
    academics = AcademicsModule.get_summary()

    # ---- KPI row -----------------------------------------------------------
    kpis = cards.kpi_grid([
        cards.kpi_card(
            '👨‍🎓', f"{students['total_students']:,}", 'Students', 'green',
            f"{students['male_count']} boys · {students['female_count']} girls"
        ),
        cards.kpi_card(
            '👨‍🏫', f"{staff['total_staff']}", 'Staff', 'indigo',
            f"{staff['teachers']} teachers · {staff['on_leave']} on leave"
        ),
        cards.kpi_card(
            '💰', _lakhs(accounts['balance']), 'Net Balance', 'pink',
            f"Income {_lakhs(accounts['total_income'])}"
        ),
        cards.kpi_card(
            '📅', f"{attendance['today_percentage']}%", 'Attendance Today', 'blue',
            f"{attendance['today_present']} present · {attendance['today_absent']} absent"
        ),
        cards.kpi_card(
            '📝', f"{academics['overall_average']}%", 'Average Score', 'violet',
            f"Pass rate {academics['pass_rate']}%"
        ),
        cards.kpi_card(
            '⚠️', f"{students['students_with_pending']}", 'Fee Defaulters', 'orange',
            f"{_lakhs(students['fees_pending'])} outstanding"
        ),
    ])

    # ---- Alerts: the "what needs my attention today" panel ------------------
    alerts = []
    if attendance['chronic_absentees_count'] > 0:
        alerts.append(cards.alert(
            'danger', '🚨 Chronic absenteeism',
            f"{attendance['chronic_absentees_count']} students are below "
            f"{ATTENDANCE_THRESHOLD}% attendance and need parent follow-up."
        ))
    if students['fees_pending'] > 0:
        alerts.append(cards.alert(
            'warning', '💳 Outstanding fees',
            f"{_lakhs(students['fees_pending'])} is pending from "
            f"{students['students_with_pending']} students "
            f"(collection rate {students['fee_collection_rate']}%)."
        ))
    if staff.get('pending_leaves'):
        alerts.append(cards.alert(
            'info', '🏖️ Leave approvals waiting',
            f"{staff['pending_leaves']} staff leave requests are pending approval."
        ))
    if accounts['balance'] > 0:
        alerts.append(cards.alert(
            'success', '✅ Healthy cash position',
            f"Net surplus of {_lakhs(accounts['balance'])} across the period."
        ))

    # ---- Charts ------------------------------------------------------------
    comparison = AccountsModule.get_monthly_comparison()
    trend = AttendanceModule.get_attendance_trend(21)

    money_chart = cards.panel(
        '💹 Monthly income vs expenses',
        charts.grouped_bar_chart(
            comparison, 'month',
            [('income', 'Income', COLORS['success']),
             ('expenses', 'Expenses', COLORS['danger'])]
        )
    )

    attendance_chart = cards.panel(
        '📈 Attendance trend (last 21 school days)',
        charts.line_chart(trend, 'date', 'percentage', color=COLORS['secondary'])
    )

    return (
        kpis
        + cards.panel('🔔 Needs attention', ''.join(alerts))
        + money_chart
        + attendance_chart
    )


# =============================================================================
# STUDENTS TAB
# =============================================================================

def build_students() -> str:
    summary = StudentModule.get_summary()
    class_counts = StudentModule.get_class_wise_count()
    pending = StudentModule.get_class_wise_pending()
    defaulters = StudentModule.get_fee_defaulters()[:12]
    transport = StudentModule.get_transport_usage()

    kpis = cards.kpi_grid([
        cards.kpi_card('👥', f"{summary['total_students']:,}", 'Total Students', 'green'),
        cards.kpi_card('📊', f"{summary['fee_collection_rate']}%", 'Fee Collection', 'indigo'),
        cards.kpi_card('⚠️', f"{summary['students_with_pending']}", 'With Dues', 'orange'),
        cards.kpi_card('🚌', f"{sum(r['students'] for r in transport)}", 'Use Transport', 'teal'),
    ])

    return (
        kpis
        + cards.panel(
            '🏫 Students per class',
            charts.bar_chart(class_counts, 'class', 'count', color=COLORS['primary'])
        )
        + cards.panel(
            '💳 Pending fees by class',
            charts.bar_chart(pending, 'class', 'pending', money=True, color=COLORS['warning'])
        )
        + cards.panel(
            '🚌 Transport route usage',
            charts.donut_chart(transport, 'route', 'students')
        )
        + cards.panel(
            '📋 Top fee defaulters',
            cards.data_table(defaulters, [
                ('name', 'Student'),
                ('class', 'Class'),
                ('section', 'Sec'),
                ('fees_status', 'Status'),
                ('fees_pending', 'Pending', 'money'),
                ('parent_name', 'Parent'),
                ('parent_phone', 'Contact'),
            ])
        )
    )


# =============================================================================
# STAFF TAB
# =============================================================================

def build_staff() -> str:
    summary = StaffModule.get_summary()
    departments = StaffModule.get_department_distribution()
    coverage = StaffModule.get_subject_coverage()
    on_leave = StaffModule.get_staff_on_leave()[:10]
    pending_leaves = StaffModule.get_pending_leave_requests()[:10]
    highest = StaffModule.get_highest_paid()[:8]

    kpis = cards.kpi_grid([
        cards.kpi_card('👨‍🏫', f"{summary['total_staff']}", 'Total Staff', 'indigo'),
        cards.kpi_card('📚', f"{summary['teachers']}", 'Teachers', 'green'),
        cards.kpi_card('💵', _lakhs(summary['monthly_salary']), 'Monthly Payroll', 'pink'),
        cards.kpi_card('🏖️', f"{summary['on_leave']}", 'Upcoming Leave', 'orange',
                       f"{summary['pending_leaves']} awaiting approval"),
    ])

    return (
        kpis
        + cards.panel(
            '🏢 Staff by department',
            charts.donut_chart(departments, 'department', 'count')
        )
        + cards.panel(
            '📖 Teachers per subject (lowest first)',
            charts.bar_chart(coverage, 'subject', 'teachers', color=COLORS['purple'])
        )
        + cards.panel(
            '💰 Highest paid staff',
            cards.data_table(highest, [
                ('name', 'Name'),
                ('designation', 'Designation'),
                ('role', 'Role'),
                ('salary', 'Salary', 'money'),
            ])
        )
        + cards.panel(
            '⏳ Leave requests pending approval',
            cards.data_table(pending_leaves, [
                ('name', 'Staff'),
                ('designation', 'Designation'),
                ('date', 'Date'),
                ('leave_type', 'Type'),
                ('reason', 'Reason'),
            ], empty_msg='No pending leave requests')
        )
        + cards.panel(
            '🗓️ Approved upcoming leave',
            cards.data_table(on_leave, [
                ('name', 'Staff'),
                ('date', 'Date'),
                ('leave_type', 'Type'),
                ('reason', 'Reason'),
            ], empty_msg='Nobody on leave')
        )
    )


# =============================================================================
# ACCOUNTS TAB
# =============================================================================

def build_accounts() -> str:
    summary = AccountsModule.get_summary()
    this_month = summary['this_month']
    comparison = AccountsModule.get_monthly_comparison()
    modes = AccountsModule.get_payment_mode_split()

    kpis = cards.kpi_grid([
        cards.kpi_card('📈', _lakhs(summary['total_income']), 'Total Income', 'green'),
        cards.kpi_card('📉', _lakhs(summary['total_expenses']), 'Total Expenses', 'pink'),
        cards.kpi_card('🏦', _lakhs(summary['balance']), 'Net Balance', 'indigo'),
        cards.kpi_card('🗓️', _lakhs(this_month['balance']), 'This Month', 'blue',
                       f"In {_lakhs(this_month['income'])} · Out {_lakhs(this_month['expenses'])}"),
    ])

    return (
        kpis
        + cards.panel(
            '💹 Income vs expenses by month',
            charts.grouped_bar_chart(
                comparison, 'month',
                [('income', 'Income', COLORS['success']),
                 ('expenses', 'Expenses', COLORS['danger'])]
            )
        )
        + cards.panel(
            '💰 Income sources',
            charts.donut_chart(summary['income_breakdown'], 'category', 'total', money=True)
        )
        + cards.panel(
            '💸 Expense breakdown',
            charts.donut_chart(summary['expense_breakdown'], 'category', 'total', money=True)
        )
        + cards.panel(
            '💳 How parents pay',
            cards.data_table(modes, [
                ('payment_mode', 'Mode'),
                ('count', 'Transactions', 'num'),
                ('total', 'Amount', 'money'),
            ])
        )
    )


# =============================================================================
# ATTENDANCE TAB
# =============================================================================

def build_attendance() -> str:
    summary = AttendanceModule.get_summary()
    class_wise = AttendanceModule.get_class_wise_attendance()
    monthly = AttendanceModule.get_monthly_trend()
    breakdown = AttendanceModule.get_status_breakdown()
    chronic = AttendanceModule.get_chronic_absentees()[:12]
    absentees = AttendanceModule.get_absentees()[:12]

    for row in class_wise:
        row['label'] = f"Class {row['class']}"

    kpis = cards.kpi_grid([
        cards.kpi_card('✅', f"{summary['today_percentage']}%", 'Today', 'green',
                       summary['today_date']),
        cards.kpi_card('📊', f"{summary['overall_percentage']}%", 'Overall Average', 'indigo'),
        cards.kpi_card('🚨', f"{summary['chronic_absentees_count']}",
                       f'Below {ATTENDANCE_THRESHOLD}%', 'pink'),
        cards.kpi_card('❌', f"{summary['today_absent']}", 'Absent Today', 'orange'),
    ])

    return (
        kpis
        + cards.panel(
            '📈 Monthly attendance trend',
            charts.line_chart(monthly, 'month', 'percentage', color=COLORS['success'])
        )
        + cards.panel(
            '🏫 Attendance by class',
            charts.progress_rows(class_wise, 'label', 'percentage',
                                 danger_below=ATTENDANCE_THRESHOLD)
        )
        + cards.panel(
            '🥧 Present / absent / late split',
            charts.donut_chart(breakdown, 'status', 'count')
        )
        + cards.panel(
            f'🚨 Students below {ATTENDANCE_THRESHOLD}% — call the parents',
            cards.data_table(chronic, [
                ('name', 'Student'),
                ('class', 'Class'),
                ('section', 'Sec'),
                ('present_days', 'Present', 'num'),
                ('total_days', 'Total', 'num'),
                ('percentage', 'Attendance', 'pct'),
                ('parent_phone', 'Contact'),
            ], empty_msg='No students below threshold 🎉')
        )
        + cards.panel(
            '📋 Absent today',
            cards.data_table(absentees, [
                ('name', 'Student'),
                ('class', 'Class'),
                ('section', 'Sec'),
                ('parent_phone', 'Contact'),
            ], empty_msg='Full attendance today 🎉')
        )
    )


# =============================================================================
# ACADEMICS TAB
# =============================================================================

def build_academics() -> str:
    summary = AcademicsModule.get_summary()
    subjects = AcademicsModule.get_subject_performance()
    terms = AcademicsModule.get_term_performance()
    grades = AcademicsModule.get_grade_distribution()
    class_perf = AcademicsModule.get_class_performance()
    toppers = AcademicsModule.get_toppers(10)
    needs_help = AcademicsModule.get_students_needing_help(12)

    for row in class_perf:
        row['label'] = f"Class {row['class']}"

    kpis = cards.kpi_grid([
        cards.kpi_card('📝', f"{summary['overall_average']}%", 'School Average', 'violet'),
        cards.kpi_card('✅', f"{summary['pass_rate']}%", 'Pass Rate', 'green'),
        cards.kpi_card('🏆', summary['best_subject'], 'Strongest Subject', 'indigo'),
        cards.kpi_card('📉', summary['weakest_subject'], 'Needs Focus', 'pink'),
    ])

    return (
        kpis
        + cards.panel(
            '📚 Average score by subject',
            charts.bar_chart(subjects, 'subject', 'average', suffix='%',
                             color=COLORS['purple'])
        )
        + cards.panel(
            '📈 Performance across terms',
            charts.line_chart(terms, 'term', 'average', color=COLORS['primary'])
        )
        + cards.panel(
            '🎓 Grade distribution',
            charts.bar_chart(grades, 'grade', 'count', color=COLORS['teal'])
        )
        + cards.panel(
            '🏫 Average by class',
            charts.progress_rows(class_perf, 'label', 'average', danger_below=50)
        )
        + cards.panel(
            '🏆 Top performers',
            cards.data_table(toppers, [
                ('name', 'Student'),
                ('class', 'Class'),
                ('section', 'Sec'),
                ('average', 'Average', 'pct'),
            ])
        )
        + cards.panel(
            '🆘 Students needing support (low marks or low attendance)',
            cards.data_table(needs_help, [
                ('name', 'Student'),
                ('class', 'Class'),
                ('average', 'Avg Score', 'pct'),
                ('attendance', 'Attendance', 'pct'),
                ('parent_phone', 'Contact'),
            ], empty_msg='Everyone is on track 🎉')
        )
    )


# =============================================================================
# HEADER
# =============================================================================

def build_header(school_name: str, model_label: str) -> str:
    """App header with live status chips."""
    students = StudentModule.get_total_count()
    staff = StaffModule.get_total_count()
    attendance = AttendanceModule.get_summary()

    return cards.header(school_name, [
        f"👨‍🎓 {students:,} students",
        f"👨‍🏫 {staff} staff",
        f"📅 Attendance {attendance['today_percentage']}%",
        f"🤖 {model_label}",
        f"🕒 Updated {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
    ])
