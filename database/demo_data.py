"""
DEMO_DATA.PY - Generate Realistic Demo Data
============================================

This file generates fake but realistic data for the demo.

LEARNING POINTS:
1. Demo data should look real but contain no actual personal info
2. Use random module for variety
3. Generate *related* data (student -> fees -> income -> attendance)
4. Make numbers realistic for the context

WHY THIS FILE WAS REWRITTEN
---------------------------
The original generator produced data that looked fine in aggregate but broke
the demo in three ways:

1. Every student had the same 94% chance of attending, so the *worst* student
   in school still had ~88% attendance. The question "show students below 75%
   attendance" returned an empty list.
2. A student could be marked 'pending' on fees while still having a full set of
   fee payments in the income table. The numbers contradicted each other.
3. Dates were hard-coded to mid-2024, so "today's attendance" showed a date
   that was years in the past.

The fix is to give every student a *profile* (see STUDENT_PROFILES in settings)
and to derive attendance, fees and income from that single source of truth.
Dates roll relative to today, so the demo is always current.
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    FEE_STRUCTURE,
    SALARY_STRUCTURE,
    DEMO_SETTINGS,
    STUDENT_PROFILES,
    TRANSPORT_ROUTES,
    EXAM_TERMS,
    GRADE_BANDS,
)
from .connection import execute_many, execute_query, get_connection
from .schema import create_tables

# =============================================================================
# NAME DATA (Indian names for realistic demo)
# =============================================================================

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav",
    "Advaith", "Aarush", "Kabir", "Ritvik", "Aaryan", "Karthik",
    "Rohan", "Rahul", "Amit", "Vikram", "Suresh", "Ramesh", "Ganesh",
    "Mahesh", "Raj", "Ajay", "Vijay", "Sanjay", "Deepak", "Rakesh"
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Ira", "Anika",
    "Priya", "Kavya", "Riya", "Saanvi", "Aanya", "Pari", "Kiara",
    "Avni", "Ishita", "Anvi", "Aradhya", "Nisha", "Pooja",
    "Sneha", "Neha", "Meera", "Lakshmi", "Radha", "Sita", "Gita",
    "Sunita", "Anita", "Rekha", "Shanti", "Durga", "Sarita"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Reddy", "Rao", "Gupta",
    "Verma", "Joshi", "Iyer", "Nair", "Menon", "Pillai", "Desai",
    "Shah", "Mehta", "Agarwal", "Bansal", "Kapoor", "Khanna",
    "Malhotra", "Bhatia", "Chopra", "Sethi", "Ahuja", "Saxena"
]

SUBJECTS = [
    "Mathematics", "Physics", "Chemistry", "Biology", "English",
    "Hindi", "Social Studies", "Computer Science", "Physical Education",
    "Art", "Music", "Sanskrit"
]

# Subjects that every student is examined in (keeps exam data a sane size)
CORE_SUBJECTS = ["Mathematics", "Science", "English", "Hindi", "Social Studies"]

DEPARTMENTS = ["Science", "Mathematics", "Languages", "Social Science", "Arts", "Sports"]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

# Map a subject to the department that owns it, so staff records are coherent
SUBJECT_DEPARTMENT = {
    "Mathematics": "Mathematics",
    "Physics": "Science",
    "Chemistry": "Science",
    "Biology": "Science",
    "Computer Science": "Science",
    "English": "Languages",
    "Hindi": "Languages",
    "Sanskrit": "Languages",
    "Social Studies": "Social Science",
    "Art": "Arts",
    "Music": "Arts",
    "Physical Education": "Sports",
}


# =============================================================================
# SMALL HELPERS
# =============================================================================

def random_date(start_year: int, end_year: int) -> str:
    """Generate a random date between two years."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')


def random_phone() -> str:
    """Generate a random Indian phone number."""
    prefixes = ['98', '97', '96', '95', '94', '93', '91', '90', '89', '88', '87', '86', '85']
    return random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(8)])


def grade_for(percentage: float) -> str:
    """Convert a percentage into a letter grade using the configured bands."""
    for cutoff, letter in GRADE_BANDS:
        if percentage >= cutoff:
            return letter
    return "F"


def pick_profile() -> tuple:
    """
    Pick a student profile using the configured weights.

    Returns a (name, attendance_rate, fee_status) tuple.
    """
    names = [p[0] for p in STUDENT_PROFILES]
    weights = [p[1] for p in STUDENT_PROFILES]
    chosen = random.choices(names, weights=weights, k=1)[0]
    for name, _weight, attendance_rate, fee_status in STUDENT_PROFILES:
        if name == chosen:
            return name, attendance_rate, fee_status
    return "regular", 0.93, "paid"


def school_days(count: int, end_date: datetime) -> List[datetime]:
    """
    Return `count` school days ending on (or just before) `end_date`.

    LEARNING POINT:
    - We walk *backwards* from today so the newest record is always "today".
    - Sundays are skipped; so are the 2nd and 4th Saturdays, which is the
      usual pattern for Indian schools.
    """
    days: List[datetime] = []
    current = end_date
    while len(days) < count:
        is_sunday = current.weekday() == 6
        is_saturday = current.weekday() == 5
        week_of_month = (current.day - 1) // 7 + 1
        is_off_saturday = is_saturday and week_of_month in (2, 4)

        if not is_sunday and not is_off_saturday:
            days.append(current)
        current -= timedelta(days=1)

    return sorted(days)


def month_starts(count: int, end_date: datetime) -> List[datetime]:
    """Return the first day of the last `count` months, oldest first."""
    months = []
    year, month = end_date.year, end_date.month
    for _ in range(count):
        months.append(datetime(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return sorted(months)


# =============================================================================
# STUDENTS
# =============================================================================

def build_students() -> List[Dict]:
    """
    Build student records as dictionaries.

    LEARNING POINT:
    - We return dicts (not tuples) because income, attendance and exam
      generation all need to read a student's class and profile.
    - The `id` we assign here matches the AUTOINCREMENT id SQLite will give,
      because we insert them in this exact order.
    """
    students: List[Dict] = []
    student_id = 1

    class_sizes = {
        1: 80, 2: 80, 3: 85, 4: 85, 5: 90,
        6: 90, 7: 85, 8: 85, 9: 80, 10: 80,
        11: 80, 12: 80
    }

    billed_months = DEMO_SETTINGS["months_of_data"]
    today = datetime.now()

    for class_num, count in class_sizes.items():
        half = count // 2
        for i in range(count):
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                first_name = random.choice(FIRST_NAMES_MALE)
            else:
                first_name = random.choice(FIRST_NAMES_FEMALE)

            last_name = random.choice(LAST_NAMES)
            name = f"{first_name} {last_name}"

            section = 'A' if i < half else 'B'
            roll_no = (i % half) + 1

            # Date of birth: a Class 1 student is about 6 years old
            birth_year = today.year - class_num - 5
            dob = random_date(birth_year - 1, birth_year)

            # Admission date: at most `class_num` years ago, never in the future
            earliest_admission = max(today.year - class_num, today.year - 12)
            admission_date = random_date(earliest_admission, today.year)

            parent_name = f"{random.choice(FIRST_NAMES_MALE)} {last_name}"
            parent_phone = random_phone()
            parent_email = f"{first_name.lower()}.{last_name.lower()}@email.com"

            addresses = [
                "MG Road", "Station Road", "Gandhi Nagar", "Nehru Colony",
                "Civil Lines", "Model Town", "Green Park", "Vasant Vihar"
            ]
            address = f"{random.randint(1, 500)}, {random.choice(addresses)}"

            # --- The important bit: profile drives fees AND attendance -------
            profile, attendance_rate, fee_status = pick_profile()

            monthly_fee = FEE_STRUCTURE[class_num]
            total_fees = monthly_fee * billed_months

            if fee_status == 'paid':
                months_paid = billed_months
            elif fee_status == 'partial':
                # Paid most, but not all, of the billed months
                months_paid = random.randint(billed_months // 2, billed_months - 1)
            else:  # pending
                months_paid = random.randint(0, max(billed_months // 3, 1))

            fees_pending = monthly_fee * (billed_months - months_paid)
            if fees_pending == 0:
                fee_status = 'paid'

            # ~30% of students use school transport
            route = random.choice(list(TRANSPORT_ROUTES)) if random.random() < 0.30 else None

            students.append({
                'id': student_id,
                'name': name,
                'class': class_num,
                'section': section,
                'roll_no': roll_no,
                'gender': gender,
                'dob': dob,
                'admission_date': admission_date,
                'parent_name': parent_name,
                'parent_phone': parent_phone,
                'parent_email': parent_email,
                'address': address,
                'fees_status': fee_status,
                'fees_pending': fees_pending,
                'total_fees': total_fees,
                'profile': profile,
                'transport_route': route,
                'blood_group': random.choice(BLOOD_GROUPS),
                # Not stored in the DB - used to drive related data
                '_attendance_rate': attendance_rate,
                '_monthly_fee': monthly_fee,
                '_months_paid': months_paid,
            })

            student_id += 1

    return students


def student_rows(students: List[Dict]) -> List[Tuple]:
    """Convert student dicts into tuples ready for INSERT."""
    return [
        (
            s['name'], s['class'], s['section'], s['roll_no'], s['gender'],
            s['dob'], s['admission_date'], s['parent_name'], s['parent_phone'],
            s['parent_email'], s['address'], s['fees_status'], s['fees_pending'],
            s['total_fees'], s['profile'], s['transport_route'], s['blood_group'],
        )
        for s in students
    ]


# =============================================================================
# STAFF
# =============================================================================

def generate_staff() -> List[Tuple]:
    """Generate staff data (teachers, admin, support)."""
    staff = []
    today = datetime.now()

    # Principal
    staff.append((
        f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}",
        'admin', 'Principal', 'Administration', None,
        random_phone(), 'principal@school.edu', SALARY_STRUCTURE['principal'],
        random_date(today.year - 14, today.year - 9), 15, 'active'
    ))

    # Vice Principal
    staff.append((
        f"{random.choice(FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}",
        'admin', 'Vice Principal', 'Administration', None,
        random_phone(), 'viceprincipal@school.edu', SALARY_STRUCTURE['vice_principal'],
        random_date(today.year - 12, today.year - 6), 12, 'active'
    ))

    # Teachers - at least two per subject so "who teaches X?" always answers
    designations = ['Senior Teacher', 'Teacher', 'Junior Teacher']
    teacher_count = DEMO_SETTINGS['total_teachers']

    subject_plan: List[str] = []
    while len(subject_plan) < teacher_count:
        subject_plan.extend(SUBJECTS)
    subject_plan = subject_plan[:teacher_count]

    used_emails = set()

    for i in range(teacher_count):
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            first = random.choice(FIRST_NAMES_MALE)
        else:
            first = random.choice(FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"

        designation = random.choice(designations)
        if designation == 'Senior Teacher':
            salary = SALARY_STRUCTURE['senior_teacher']
        elif designation == 'Teacher':
            salary = SALARY_STRUCTURE['teacher']
        else:
            salary = SALARY_STRUCTURE['junior_teacher']
        salary = salary + random.randint(-2000, 3000)

        subject = subject_plan[i]
        department = SUBJECT_DEPARTMENT.get(subject, 'General')

        # Unique email per teacher
        email = f"{first.lower()}.{last.lower()}@school.edu"
        suffix = 2
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{suffix}@school.edu"
            suffix += 1
        used_emails.add(email)

        staff.append((
            name, 'teacher', designation, department, subject,
            random_phone(), email, salary,
            random_date(today.year - 9, today.year - 1),
            random.randint(4, 15), 'active'
        ))

    # Admin staff
    admin_roles = ['Office Manager', 'Accountant', 'Receptionist', 'Librarian', 'Counsellor']
    for role in admin_roles[:DEMO_SETTINGS['total_admin_staff']]:
        name = f"{random.choice(FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}"
        salary = SALARY_STRUCTURE['accountant'] if role == 'Accountant' else SALARY_STRUCTURE['admin_staff']
        staff.append((
            name, 'admin', role, 'Administration', None,
            random_phone(), f"{role.split()[0].lower()}@school.edu", salary,
            random_date(today.year - 6, today.year - 1), 12, 'active'
        ))

    # Support staff
    support_roles = [
        ('Peon', 'peon'), ('Peon', 'peon'),
        ('Security Guard', 'guard'), ('Security Guard', 'guard'),
        ('Cleaner', 'cleaner')
    ]
    for role, salary_key in support_roles[:DEMO_SETTINGS['total_support_staff']]:
        name = f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}"
        staff.append((
            name, 'support', role, 'Maintenance', None,
            random_phone(), None, SALARY_STRUCTURE[salary_key],
            random_date(today.year - 5, today.year - 1), 12, 'active'
        ))

    return staff


# =============================================================================
# INCOME
# =============================================================================

def generate_income(students: List[Dict]) -> List[Tuple]:
    """
    Generate income records that RECONCILE with each student's fee status.

    LEARNING POINT:
    - A student who owes two months of fees has exactly two missing payments.
    - That means "total pending" from the students table and "total collected"
      from the income table tell the same story. Demos fall apart when they
      don't.
    """
    income: List[Tuple] = []
    today = datetime.now()
    months = month_starts(DEMO_SETTINGS["months_of_data"], today)

    for student in students:
        # The student paid for the FIRST `_months_paid` months; the unpaid
        # months are the most recent ones (which is how arrears build up).
        paid_months = months[:student['_months_paid']]

        for month_start in paid_months:
            month_name = month_start.strftime('%B %Y')
            pay_day = min(month_start + timedelta(days=random.randint(1, 25)), today)

            income.append((
                pay_day.strftime('%Y-%m-%d'),
                'fees',
                student['_monthly_fee'],
                student['id'],
                f"Tuition fee for {month_name}",
                random.choice(['cash', 'upi', 'cheque', 'bank']),
                f"RCP-{pay_day.strftime('%Y%m')}-{student['id']:04d}"
            ))

        # Transport fees follow the assigned route
        if student['transport_route']:
            fare = TRANSPORT_ROUTES[student['transport_route']]
            for month_start in paid_months:
                pay_day = min(month_start + timedelta(days=random.randint(1, 25)), today)
                income.append((
                    pay_day.strftime('%Y-%m-%d'),
                    'transport',
                    fare,
                    student['id'],
                    f"Transport - {student['transport_route']}",
                    random.choice(['cash', 'upi']),
                    f"TRP-{pay_day.strftime('%Y%m')}-{student['id']:04d}"
                ))

    # Non-fee income streams - these make the income chart interesting
    for month_start in months:
        month_end = min(month_start + timedelta(days=27), today)
        if month_end < month_start:
            continue

        def day_in_month() -> datetime:
            span = (month_end - month_start).days
            return month_start + timedelta(days=random.randint(0, max(span, 0)))

        # Donations
        for _ in range(random.randint(3, 6)):
            pay_date = day_in_month()
            donor = f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}"
            income.append((
                pay_date.strftime('%Y-%m-%d'), 'donation',
                random.randint(5000, 50000), None,
                f"Donation from {donor}",
                random.choice(['cash', 'cheque', 'bank']),
                f"DON-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # Hostel fees
        for _ in range(random.randint(8, 14)):
            pay_date = day_in_month()
            income.append((
                pay_date.strftime('%Y-%m-%d'), 'hostel',
                random.randint(6000, 12000), None,
                f"Hostel fee for {month_start.strftime('%B %Y')}",
                random.choice(['upi', 'bank']),
                f"HST-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # Exam fees
        for _ in range(random.randint(4, 8)):
            pay_date = day_in_month()
            income.append((
                pay_date.strftime('%Y-%m-%d'), 'exam',
                random.randint(15000, 40000), None,
                "Examination fee collection",
                'bank',
                f"EXM-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # Events and library
        for category, low, high, label in [
            ('events', 8000, 35000, 'Annual day / sports ticket sales'),
            ('library', 2000, 9000, 'Library fees and fines'),
        ]:
            for _ in range(random.randint(2, 4)):
                pay_date = day_in_month()
                income.append((
                    pay_date.strftime('%Y-%m-%d'), category,
                    random.randint(low, high), None, label,
                    random.choice(['cash', 'upi']),
                    f"{category[:3].upper()}-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
                ))

    return income


# =============================================================================
# EXPENSES
# =============================================================================

def generate_expenses(staff_data: List[Tuple]) -> List[Tuple]:
    """Generate expense records (salaries, utilities, etc.)."""
    expenses: List[Tuple] = []
    today = datetime.now()
    months = month_starts(DEMO_SETTINGS["months_of_data"], today)

    for month_start in months:
        month_name = month_start.strftime('%B %Y')

        # --- Salaries (paid in the first week of each month) ----------------
        for idx, staff_member in enumerate(staff_data):
            name = staff_member[0]
            salary = staff_member[7]
            pay_date = month_start + timedelta(days=random.randint(1, 5))
            if pay_date > today:
                continue
            expenses.append((
                pay_date.strftime('%Y-%m-%d'), 'salary', salary, name,
                f"Salary for {month_name}", 'bank',
                f"SAL-{pay_date.strftime('%Y%m')}-{idx + 1:03d}"
            ))

        def day_in_month(low: int, high: int):
            candidate = month_start + timedelta(days=random.randint(low, high))
            return candidate if candidate <= today else None

        # --- Utilities ------------------------------------------------------
        utilities = [
            ('Electricity Bill', random.randint(15000, 30000)),
            ('Water Bill', random.randint(3000, 6000)),
            ('Internet Bill', random.randint(5000, 8000)),
            ('Phone Bill', random.randint(2000, 4000)),
        ]
        for utility_name, amount in utilities:
            pay_date = day_in_month(10, 20)
            if not pay_date:
                continue
            expenses.append((
                pay_date.strftime('%Y-%m-%d'), 'utilities', amount,
                utility_name.split()[0] + " Company", utility_name, 'bank',
                f"UTL-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # --- Maintenance ----------------------------------------------------
        maintenance_items = [
            'Plumbing repair', 'Electrical work', 'AC maintenance',
            'Furniture repair', 'Building repair', 'Painting work',
            'Garden maintenance', 'Pest control'
        ]
        for _ in range(random.randint(3, 6)):
            pay_date = day_in_month(1, 27)
            if not pay_date:
                continue
            expenses.append((
                pay_date.strftime('%Y-%m-%d'), 'maintenance',
                random.randint(5000, 25000), 'Contractor',
                random.choice(maintenance_items), random.choice(['cash', 'bank']),
                f"MNT-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # --- Supplies -------------------------------------------------------
        supplies = [
            ('Stationery', random.randint(8000, 15000)),
            ('Cleaning supplies', random.randint(3000, 6000)),
            ('Office supplies', random.randint(2000, 5000)),
            ('Laboratory consumables', random.randint(6000, 14000)),
            ('Sports equipment', random.randint(5000, 20000)),
        ]
        for supply_name, amount in supplies:
            pay_date = day_in_month(5, 25)
            if not pay_date:
                continue
            expenses.append((
                pay_date.strftime('%Y-%m-%d'), 'supplies', amount,
                'Vendor', supply_name, random.choice(['cash', 'upi']),
                f"SUP-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # --- Transport, technology, events, training ------------------------
        other_costs = [
            ('transport', 'Bus diesel and servicing', 45000, 80000),
            ('technology', 'Smart board / lab computers AMC', 12000, 45000),
            ('events', 'Annual day and sports meet', 10000, 60000),
            ('training', 'Teacher training workshop', 8000, 25000),
        ]
        for category, label, low, high in other_costs:
            pay_date = day_in_month(3, 26)
            if not pay_date:
                continue
            expenses.append((
                pay_date.strftime('%Y-%m-%d'), category,
                random.randint(low, high), 'Vendor', label, 'bank',
                f"{category[:3].upper()}-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

    return expenses


# =============================================================================
# ATTENDANCE
# =============================================================================

def generate_attendance(students: List[Dict], teacher_ids: List[int]) -> List[Tuple]:
    """
    Generate attendance records driven by each student's profile.

    LEARNING POINT:
    - Because every student has their own attendance_rate, the school ends up
      with a realistic spread: most students above 90%, a handful below 75%.
    - That spread is what makes "who needs attention?" a meaningful question.
    """
    attendance: List[Tuple] = []
    days = school_days(DEMO_SETTINGS["attendance_days"], datetime.now())

    absence_reasons = [
        'Fever', 'Family function', 'Medical appointment',
        'Travel', 'Unwell', None, None
    ]

    for day in days:
        date_str = day.strftime('%Y-%m-%d')
        for student in students:
            rate = student['_attendance_rate']
            roll = random.random()

            if roll < rate:
                status = 'present'
                remark = None
            elif roll < rate + 0.03:
                status = 'late'
                remark = None
            else:
                status = 'absent'
                remark = random.choice(absence_reasons)

            attendance.append((
                date_str, student['id'], status,
                random.choice(teacher_ids), remark
            ))

    return attendance


# =============================================================================
# EXAM RESULTS
# =============================================================================

def generate_exam_results(students: List[Dict]) -> List[Tuple]:
    """
    Generate term-wise exam marks.

    LEARNING POINT:
    - Marks correlate with the attendance profile. A student who misses half
      the classes should not be topping the class - that correlation is what
      makes the "at risk students" story credible in a demo.
    """
    results: List[Tuple] = []

    for student in students:
        # Base ability, nudged by how often the student actually attends
        base = 45 + (student['_attendance_rate'] - 0.5) * 70
        ability = max(25.0, min(95.0, random.gauss(base, 8)))

        for term in EXAM_TERMS:
            for subject in CORE_SUBJECTS:
                marks = max(8.0, min(100.0, random.gauss(ability, 9)))
                marks = round(marks, 1)
                results.append((
                    student['id'], term, subject, marks, 100, grade_for(marks)
                ))

    return results


# =============================================================================
# LEAVE REQUESTS
# =============================================================================

def generate_leave_requests(staff_count: int) -> List[Tuple]:
    """
    Generate staff leave requests - past, current and pending approval.

    The original demo never populated this table, so "who is on leave?"
    always answered "nobody".
    """
    requests: List[Tuple] = []
    today = datetime.now()
    leave_types = ['casual', 'sick', 'earned', 'maternity', 'duty']
    reasons = [
        'Family function', 'Medical treatment', 'Personal work',
        'Child care', 'Official training', 'Out of station',
    ]

    for _ in range(45):
        staff_id = random.randint(1, staff_count)
        # Spread from 60 days ago to 20 days ahead
        offset = random.randint(-60, 20)
        date = today + timedelta(days=offset)

        if offset > 0:
            status = random.choice(['pending', 'approved', 'approved'])
        else:
            status = random.choice(['approved', 'approved', 'rejected'])

        requests.append((
            staff_id, date.strftime('%Y-%m-%d'),
            random.choice(leave_types), random.choice(reasons), status
        ))

    return requests


# =============================================================================
# ORCHESTRATION
# =============================================================================

def generate_all_demo_data(force: bool = False):
    """
    Generate all demo data and insert into database.

    Args:
        force: if True, wipe existing rows and regenerate.

    LEARNING POINT:
    - We generate data in order due to foreign key relationships
    - Students first, then income/attendance/results (which reference students)
    - Staff first, then expenses and leave requests
    """
    print("🚀 Starting demo data generation...")

    # A fixed seed means the demo shows the same numbers every time you run it
    random.seed(DEMO_SETTINGS.get("random_seed", 20240601))

    create_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    existing = cursor.fetchone()[0]
    conn.close()

    if existing > 0 and not force:
        print("⚠️  Data already exists. Skipping generation.")
        print("   To regenerate, run: python -m database.demo_data --force")
        return

    if existing > 0 and force:
        print("🧹 Clearing existing data...")
        conn = get_connection()
        cursor = conn.cursor()
        for table in ['attendance', 'exam_results', 'leave_requests',
                      'income', 'expenses', 'students', 'staff']:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        conn.commit()
        conn.close()

    # ---- Students ----------------------------------------------------------
    print("👨‍🎓 Generating students...")
    students = build_students()
    execute_many('''
        INSERT INTO students
        (name, class, section, roll_no, gender, dob, admission_date,
         parent_name, parent_phone, parent_email, address,
         fees_status, fees_pending, total_fees, profile, transport_route, blood_group)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', student_rows(students))
    print(f"   ✅ Created {len(students)} students")

    # ---- Staff -------------------------------------------------------------
    print("👨‍🏫 Generating staff...")
    staff = generate_staff()
    execute_many('''
        INSERT INTO staff
        (name, role, designation, department, subject, phone, email,
         salary, joining_date, leave_balance, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', staff)
    print(f"   ✅ Created {len(staff)} staff members")

    # Teacher ids are the rows where role == 'teacher' (1-based insert order)
    teacher_ids = [i + 1 for i, row in enumerate(staff) if row[1] == 'teacher']

    # ---- Income ------------------------------------------------------------
    print("💰 Generating income records...")
    income = generate_income(students)
    execute_many('''
        INSERT INTO income
        (date, category, amount, student_id, description, payment_mode, receipt_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', income)
    print(f"   ✅ Created {len(income)} income records")

    # ---- Expenses ----------------------------------------------------------
    print("💸 Generating expense records...")
    expenses = generate_expenses(staff)
    execute_many('''
        INSERT INTO expenses
        (date, category, amount, paid_to, description, payment_mode, voucher_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', expenses)
    print(f"   ✅ Created {len(expenses)} expense records")

    # ---- Attendance --------------------------------------------------------
    print("📅 Generating attendance records...")
    attendance = generate_attendance(students, teacher_ids)
    execute_many('''
        INSERT INTO attendance
        (date, student_id, status, marked_by, remarks)
        VALUES (?, ?, ?, ?, ?)
    ''', attendance)
    print(f"   ✅ Created {len(attendance)} attendance records")

    # ---- Exam results ------------------------------------------------------
    print("📝 Generating exam results...")
    results = generate_exam_results(students)
    execute_many('''
        INSERT INTO exam_results
        (student_id, term, subject, marks, max_marks, grade)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', results)
    print(f"   ✅ Created {len(results)} exam results")

    # ---- Leave requests ----------------------------------------------------
    print("🏖️  Generating leave requests...")
    leaves = generate_leave_requests(len(staff))
    execute_many('''
        INSERT INTO leave_requests
        (staff_id, date, leave_type, reason, status)
        VALUES (?, ?, ?, ?, ?)
    ''', leaves)
    print(f"   ✅ Created {len(leaves)} leave requests")

    print("\n🎉 Demo data generation complete!")
    print(f"""
    Summary:
    --------
    Students:   {len(students)}
    Staff:      {len(staff)}
    Income:     {len(income)} records
    Expenses:   {len(expenses)} records
    Attendance: {len(attendance)} records
    Results:    {len(results)} records
    Leaves:     {len(leaves)} records
    """)


if __name__ == "__main__":
    generate_all_demo_data(force='--force' in sys.argv)
