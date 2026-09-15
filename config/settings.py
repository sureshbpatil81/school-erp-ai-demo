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

DATABASE_PATH = "school_data.db"

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

# =============================================================================
# DEMO DATA SETTINGS
# =============================================================================
# How much fake data to generate

DEMO_SETTINGS = {
    "total_students": 1000,
    "total_teachers": 40,
    "total_admin_staff": 5,
    "total_support_staff": 5,
    "months_of_data": 4,  # Generate 4 months of transactions
    "attendance_days": 80,  # School days to generate
}

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
