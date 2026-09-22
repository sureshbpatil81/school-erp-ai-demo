"""
SETTINGS.PY - Configuration for School ERP
==========================================

This file contains all the settings for your app.
Change values here to customize for different schools.

LEARNING POINT:
- Keep all settings in one place
- Easy to change without touching other code
- Use environment variables for secrets in production
"""

import os

# =============================================================================
# SCHOOL INFORMATION
# =============================================================================
# Change these for different schools

SCHOOL_NAME = "ABC Public School"
SCHOOL_ADDRESS = "123 Education Street, Knowledge City"
SCHOOL_PHONE = "011-12345678"
SCHOOL_EMAIL = "info@abcschool.edu"

# =============================================================================
# DATABASE SETTINGS
# =============================================================================
# SQLite for demo (file-based, simple)
# Change to PostgreSQL/Supabase for production
#
# DEPLOYMENT NOTE (Render / any PaaS):
# The path must be ABSOLUTE. Render starts the process from the repo root but
# the working directory is not guaranteed, and a relative path would silently
# create an empty database somewhere else - the app would then boot with zero
# students. We anchor the file to this project folder, and allow an override
# via DATABASE_PATH so a mounted persistent disk can be used instead.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "school_data.db"),
)

# =============================================================================
# LLM SETTINGS
# =============================================================================
# We use free Mistral model from Hugging Face
# You can change to other models later

LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# Alternative models (uncomment to try):
# LLM_MODEL = "meta-llama/Llama-2-7b-chat-hf"
# LLM_MODEL = "google/flan-t5-large"

# Hugging Face API token (optional for public models)
# Get your free token at: https://huggingface.co/settings/tokens
HF_TOKEN = os.environ.get("HF_TOKEN", None)

# =============================================================================
# FEE STRUCTURE
# =============================================================================
# Monthly fees by class (in Rupees)

FEE_STRUCTURE = {
    1: 4000,   # Class 1
    2: 4000,   # Class 2
    3: 4000,   # Class 3
    4: 4000,   # Class 4
    5: 4000,   # Class 5
    6: 5000,   # Class 6
    7: 5000,   # Class 7
    8: 5000,   # Class 8
    9: 6000,   # Class 9
    10: 6000,  # Class 10
    11: 7000,  # Class 11
    12: 7000,  # Class 12
}

# Annual fee = monthly fee x number of billed months in the session
FEE_MONTHS_PER_SESSION = 10

# =============================================================================
# DEMO DATA SETTINGS
# =============================================================================
# How much fake data to generate

DEMO_SETTINGS = {
    "total_students": 1000,
    "total_teachers": 40,
    "total_admin_staff": 5,
    "total_support_staff": 5,
    "months_of_data": 6,  # Generate 6 months of transactions
    "attendance_days": 120,  # School days to generate
    "random_seed": 20240601,  # Fixed seed => the same demo every run
}

# =============================================================================
# STUDENT BEHAVIOUR PROFILES
# =============================================================================
# Each student is assigned a profile. This is what makes the demo interesting:
# without it every student looks identical and queries like
# "students below 75% attendance" return an empty list.
#
# weight          = share of students with this profile
# attendance_rate = probability the student shows up on a given day
# fee_status      = how this student is billed

STUDENT_PROFILES = [
    # name,         weight, attendance_rate, fee_status
    ("excellent",    0.45,   0.98,  "paid"),
    ("regular",      0.33,   0.93,  "paid"),
    ("irregular",    0.14,   0.82,  "partial"),
    ("at_risk",      0.06,   0.68,  "partial"),
    ("critical",     0.02,   0.52,  "pending"),
]

# =============================================================================
# TRANSPORT
# =============================================================================
# Route name -> monthly fare. Used for transport income and route-wise reports.

TRANSPORT_ROUTES = {
    "Route 1 - City Centre": 1500,
    "Route 2 - Lake View": 1800,
    "Route 3 - Industrial Area": 2000,
    "Route 4 - Airport Road": 2400,
    "Route 5 - Old Town": 1600,
}

# =============================================================================
# INCOME / EXPENSE CATEGORIES
# =============================================================================
# Richer categories give the dashboard charts something to show.

INCOME_CATEGORIES = [
    "fees", "transport", "donation", "hostel", "exam", "events", "library"
]

EXPENSE_CATEGORIES = [
    "salary", "utilities", "maintenance", "supplies",
    "transport", "events", "technology", "training"
]

# =============================================================================
# ACADEMIC SETTINGS
# =============================================================================

EXAM_TERMS = ["Unit Test 1", "Mid Term", "Unit Test 2", "Final Term"]

GRADE_BANDS = [
    (90, "A+"), (80, "A"), (70, "B+"), (60, "B"),
    (50, "C"), (40, "D"), (0, "F"),
]

ATTENDANCE_THRESHOLD = 75  # Below this % a student is flagged

# =============================================================================
# SALARY STRUCTURE
# =============================================================================
# Monthly salaries by role (in Rupees)

SALARY_STRUCTURE = {
    "principal": 75000,
    "vice_principal": 60000,
    "senior_teacher": 45000,
    "teacher": 35000,
    "junior_teacher": 28000,
    "admin_staff": 25000,
    "accountant": 30000,
    "peon": 18000,
    "guard": 20000,
    "cleaner": 16000,
}

# =============================================================================
# UI SETTINGS
# =============================================================================

UI_THEME = "soft"  # Options: "soft", "default", "glass", "monochrome"
APP_TITLE = f"🏫 {SCHOOL_NAME} - AI Assistant"
