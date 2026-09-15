"""
DEMO_DATA.PY - Generate Realistic Demo Data
============================================

This file generates fake but realistic data for the demo.

LEARNING POINTS:
1. Demo data should look real but contain no actual personal info
2. Use random module for variety
3. Generate related data (student → fees → attendance)
4. Make numbers realistic for the context

WHY DEMO DATA MATTERS:
- Shows the app working with realistic scenarios
- Tests edge cases (pending fees, absences, etc.)
- No privacy concerns (all fake)
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    FEE_STRUCTURE,
    SALARY_STRUCTURE,
    DEMO_SETTINGS
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

DEPARTMENTS = ["Science", "Mathematics", "Languages", "Social Science", "Arts", "Sports"]


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


def generate_students() -> List[Tuple]:
    """
    Generate student data.

    LEARNING POINT:
    - We create students distributed across classes 1-12
    - Each class has 2 sections (A and B)
    - ~80-90 students per class
    """
    students = []
    student_id = 1

    # Class distribution (roughly 1000 students total)
    class_sizes = {
        1: 80, 2: 80, 3: 85, 4: 85, 5: 90,
        6: 90, 7: 85, 8: 85, 9: 80, 10: 80,
        11: 80, 12: 80
    }

    for class_num, count in class_sizes.items():
        for i in range(count):
            # Randomly assign gender
            gender = random.choice(['M', 'F'])

            # Pick name based on gender
            if gender == 'M':
                first_name = random.choice(FIRST_NAMES_MALE)
            else:
                first_name = random.choice(FIRST_NAMES_FEMALE)

            last_name = random.choice(LAST_NAMES)
            name = f"{first_name} {last_name}"

            # Section A or B
            section = 'A' if i < count // 2 else 'B'

            # Roll number within section
            roll_no = (i % (count // 2)) + 1

            # Date of birth (based on class)
            birth_year = 2024 - class_num - 5  # Roughly 5-6 years old in Class 1
            dob = random_date(birth_year - 1, birth_year)

            # Admission date
            admission_date = random_date(2020, 2024)

            # Parent info
            parent_first = random.choice(FIRST_NAMES_MALE)
            parent_name = f"{parent_first} {last_name}"
            parent_phone = random_phone()
            parent_email = f"{first_name.lower()}.parent@email.com"

            # Address
            addresses = [
                "MG Road", "Station Road", "Gandhi Nagar", "Nehru Colony",
                "Civil Lines", "Model Town", "Green Park", "Vasant Vihar"
            ]
            address = f"{random.randint(1, 500)}, {random.choice(addresses)}"

            # Fees status (80% paid, 15% partial, 5% pending)
            fee_roll = random.random()
            monthly_fee = FEE_STRUCTURE[class_num]
            total_fees = monthly_fee * 4  # 4 months

            if fee_roll < 0.80:
                fees_status = 'paid'
                fees_pending = 0
            elif fee_roll < 0.95:
                fees_status = 'partial'
                fees_pending = random.randint(1, 3) * monthly_fee
            else:
                fees_status = 'pending'
                fees_pending = total_fees

            students.append((
                name, class_num, section, roll_no, gender, dob,
                admission_date, parent_name, parent_phone, parent_email,
                address, fees_status, fees_pending, total_fees
            ))

            student_id += 1

    return students


def generate_staff() -> List[Tuple]:
    """
    Generate staff data (teachers, admin, support).
    """
    staff = []

    # Principal
    staff.append((
        f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}",
        'admin', 'Principal', 'Administration', None,
        random_phone(), None, SALARY_STRUCTURE['principal'],
        random_date(2010, 2015), 15, 'active'
    ))

    # Vice Principal
    staff.append((
        f"{random.choice(FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}",
        'admin', 'Vice Principal', 'Administration', None,
        random_phone(), None, SALARY_STRUCTURE['vice_principal'],
        random_date(2012, 2018), 12, 'active'
    ))

    # Teachers (40)
    designations = ['Senior Teacher', 'Teacher', 'Junior Teacher']

    for i in range(40):
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            name = f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}"
        else:
            name = f"{random.choice(FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}"

        designation = random.choice(designations)
        if designation == 'Senior Teacher':
            salary = SALARY_STRUCTURE['senior_teacher']
        elif designation == 'Teacher':
            salary = SALARY_STRUCTURE['teacher']
        else:
            salary = SALARY_STRUCTURE['junior_teacher']

        # Add some variance to salary
        salary = salary + random.randint(-2000, 3000)

        subject = random.choice(SUBJECTS)
        department = random.choice(DEPARTMENTS)

        staff.append((
            name, 'teacher', designation, department, subject,
            random_phone(), f"{name.split()[0].lower()}@school.edu",
            salary, random_date(2015, 2023),
            random.randint(8, 15), 'active'
        ))

    # Admin staff (3 more)
    admin_roles = ['Office Manager', 'Accountant', 'Receptionist']
    for role in admin_roles:
        name = f"{random.choice(FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}"
        salary = SALARY_STRUCTURE['admin_staff']
        if role == 'Accountant':
            salary = SALARY_STRUCTURE['accountant']

        staff.append((
            name, 'admin', role, 'Administration', None,
            random_phone(), None, salary,
            random_date(2018, 2023), 12, 'active'
        ))

    # Support staff (5)
    support_roles = [
        ('Peon', 'peon'), ('Peon', 'peon'),
        ('Security Guard', 'guard'), ('Security Guard', 'guard'),
        ('Cleaner', 'cleaner')
    ]

    for role, salary_key in support_roles:
        name = f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}"
        staff.append((
            name, 'support', role, 'Maintenance', None,
            random_phone(), None, SALARY_STRUCTURE[salary_key],
            random_date(2019, 2023), 12, 'active'
        ))

    return staff


def generate_income(student_count: int) -> List[Tuple]:
    """
    Generate income records (fees, donations, etc.).
    """
    income = []

    # Get current date for reference
    base_date = datetime(2024, 6, 1)  # Start from June 2024

    # Generate 4 months of fee payments
    for month_offset in range(4):
        month_start = base_date + timedelta(days=30 * month_offset)
        month_name = month_start.strftime('%B %Y')

        # Fee payments (most students pay)
        for student_id in range(1, student_count + 1):
            # 85% of students pay each month
            if random.random() < 0.85:
                # Determine class (roughly) for fee amount
                class_num = ((student_id - 1) // 85) + 1
                if class_num > 12:
                    class_num = 12
                amount = FEE_STRUCTURE.get(class_num, 5000)

                pay_date = month_start + timedelta(days=random.randint(1, 25))
                payment_mode = random.choice(['cash', 'upi', 'cheque', 'bank'])
                receipt_no = f"RCP-{pay_date.strftime('%Y%m')}-{student_id:04d}"

                income.append((
                    pay_date.strftime('%Y-%m-%d'),
                    'fees',
                    amount,
                    student_id,
                    f"Tuition fee for {month_name}",
                    payment_mode,
                    receipt_no
                ))

        # Transport fees (30% of students)
        for student_id in range(1, student_count + 1):
            if random.random() < 0.30:
                pay_date = month_start + timedelta(days=random.randint(1, 25))
                income.append((
                    pay_date.strftime('%Y-%m-%d'),
                    'transport',
                    random.randint(1500, 2500),
                    student_id,
                    f"Transport fee for {month_name}",
                    random.choice(['cash', 'upi']),
                    f"TRP-{pay_date.strftime('%Y%m')}-{student_id:04d}"
                ))

        # Donations (2-5 per month)
        for _ in range(random.randint(2, 5)):
            pay_date = month_start + timedelta(days=random.randint(1, 28))
            donor = f"{random.choice(FIRST_NAMES_MALE)} {random.choice(LAST_NAMES)}"
            income.append((
                pay_date.strftime('%Y-%m-%d'),
                'donation',
                random.randint(5000, 50000),
                None,
                f"Donation from {donor}",
                random.choice(['cash', 'cheque', 'bank']),
                f"DON-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

    return income


def generate_expenses(staff_data: List[Tuple]) -> List[Tuple]:
    """
    Generate expense records (salaries, utilities, etc.).
    """
    expenses = []
    base_date = datetime(2024, 6, 1)

    for month_offset in range(4):
        month_start = base_date + timedelta(days=30 * month_offset)
        month_name = month_start.strftime('%B %Y')

        # Salary payments (1st-5th of each month)
        for idx, staff_member in enumerate(staff_data):
            name = staff_member[0]
            salary = staff_member[7]

            pay_date = month_start + timedelta(days=random.randint(1, 5))
            voucher_no = f"SAL-{pay_date.strftime('%Y%m')}-{idx + 1:03d}"

            expenses.append((
                pay_date.strftime('%Y-%m-%d'),
                'salary',
                salary,
                name,
                f"Salary for {month_name}",
                'bank',
                voucher_no
            ))

        # Utilities
        utilities = [
            ('Electricity Bill', random.randint(15000, 30000)),
            ('Water Bill', random.randint(3000, 6000)),
            ('Internet Bill', random.randint(5000, 8000)),
            ('Phone Bill', random.randint(2000, 4000)),
        ]

        for utility_name, amount in utilities:
            pay_date = month_start + timedelta(days=random.randint(10, 20))
            expenses.append((
                pay_date.strftime('%Y-%m-%d'),
                'utilities',
                amount,
                utility_name.split()[0] + " Company",
                utility_name,
                'bank',
                f"UTL-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # Maintenance (random, 1-3 per month)
        maintenance_items = [
            'Plumbing repair', 'Electrical work', 'AC maintenance',
            'Furniture repair', 'Building repair', 'Painting work',
            'Garden maintenance', 'Pest control'
        ]

        for _ in range(random.randint(1, 3)):
            item = random.choice(maintenance_items)
            pay_date = month_start + timedelta(days=random.randint(1, 28))
            expenses.append((
                pay_date.strftime('%Y-%m-%d'),
                'maintenance',
                random.randint(5000, 25000),
                'Contractor',
                item,
                random.choice(['cash', 'bank']),
                f"MNT-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

        # Supplies
        supplies = [
            ('Stationery', random.randint(8000, 15000)),
            ('Cleaning supplies', random.randint(3000, 6000)),
            ('Office supplies', random.randint(2000, 5000)),
        ]

        for supply_name, amount in supplies:
            pay_date = month_start + timedelta(days=random.randint(5, 25))
            expenses.append((
                pay_date.strftime('%Y-%m-%d'),
                'supplies',
                amount,
                'Vendor',
                supply_name,
                random.choice(['cash', 'upi']),
                f"SUP-{pay_date.strftime('%Y%m%d')}-{random.randint(1, 99):02d}"
            ))

    return expenses


def generate_attendance(student_count: int) -> List[Tuple]:
    """
    Generate attendance records.
    """
    attendance = []

    # Generate 80 days of attendance (roughly 4 months of school days)
    base_date = datetime(2024, 6, 1)
    school_days = []

    current = base_date
    while len(school_days) < 80:
        # Skip Sundays
        if current.weekday() != 6:
            school_days.append(current)
        current += timedelta(days=1)

    for day in school_days:
        date_str = day.strftime('%Y-%m-%d')

        for student_id in range(1, student_count + 1):
            # 94% present, 5% absent, 1% late
            roll = random.random()
            if roll < 0.94:
                status = 'present'
            elif roll < 0.99:
                status = 'absent'
            else:
                status = 'late'

            # Random teacher marks attendance
            marked_by = random.randint(3, 42)  # Teacher IDs

            attendance.append((
                date_str,
                student_id,
                status,
                marked_by,
                None  # remarks
            ))

    return attendance


def generate_all_demo_data():
    """
    Generate all demo data and insert into database.

    LEARNING POINT:
    - We generate data in order due to foreign key relationships
    - Students first, then income (which references students)
    - Staff first, then expenses (which references staff)
    """
    print("🚀 Starting demo data generation...")

    # Create tables first
    create_tables()

    # Check if data already exists
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] > 0:
        print("⚠️  Data already exists. Skipping generation.")
        print("   To regenerate, delete school_data.db file first.")
        conn.close()
        return
    conn.close()

    # Generate students
    print("👨‍🎓 Generating students...")
    students = generate_students()
    execute_many('''
        INSERT INTO students
        (name, class, section, roll_no, gender, dob, admission_date,
         parent_name, parent_phone, parent_email, address,
         fees_status, fees_pending, total_fees)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', students)
    print(f"   ✅ Created {len(students)} students")

    # Generate staff
    print("👨‍🏫 Generating staff...")
    staff = generate_staff()
    execute_many('''
        INSERT INTO staff
        (name, role, designation, department, subject, phone, email,
         salary, joining_date, leave_balance, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', staff)
    print(f"   ✅ Created {len(staff)} staff members")

    # Generate income
    print("💰 Generating income records...")
    income = generate_income(len(students))
    execute_many('''
        INSERT INTO income
        (date, category, amount, student_id, description, payment_mode, receipt_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', income)
    print(f"   ✅ Created {len(income)} income records")

    # Generate expenses
    print("💸 Generating expense records...")
    expenses = generate_expenses(staff)
    execute_many('''
        INSERT INTO expenses
        (date, category, amount, paid_to, description, payment_mode, voucher_no)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', expenses)
    print(f"   ✅ Created {len(expenses)} expense records")

    # Generate attendance
    print("📅 Generating attendance records...")
    attendance = generate_attendance(len(students))
    execute_many('''
        INSERT INTO attendance
        (date, student_id, status, marked_by, remarks)
        VALUES (?, ?, ?, ?, ?)
    ''', attendance)
    print(f"   ✅ Created {len(attendance)} attendance records")

    print("\n🎉 Demo data generation complete!")
    print(f"""
    Summary:
    --------
    Students:   {len(students)}
    Staff:      {len(staff)}
    Income:     {len(income)} records
    Expenses:   {len(expenses)} records
    Attendance: {len(attendance)} records
    """)


if __name__ == "__main__":
    generate_all_demo_data()
