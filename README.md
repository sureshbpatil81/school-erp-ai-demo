# 🏫 School ERP AI Assistant

An AI-powered school management system that lets you query school data using natural language.

**Built with:** Python + Gradio + Hugging Face + SQLite

---

## 🎯 What This Does

- **Chat Interface**: Ask questions in plain English
- **Visual Dashboard**: 7 tabs of KPI cards, charts and drill-down tables
- **5 Modules**: Students, Staff, Accounts, Attendance, Academics
- **LLM-Powered**: Uses Mistral 7B (free), with a rule-based offline fallback
- **Demo Data**: 1,000 students, 52 staff, 6 months of transactions,
  120,000 attendance records and 20,000 exam results
- **Zero chart dependencies**: every graph is hand-built SVG

---

## 📸 The Dashboard

| Tab | What it shows |
|-----|---------------|
| 💬 **Ask AI** | Natural-language chat over all school data |
| 📊 **Overview** | Headline KPIs + a "needs attention" alert panel |
| 👨‍🎓 **Students** | Class strength, pending fees by class, transport, defaulters |
| 👨‍🏫 **Staff** | Departments, subject coverage, payroll, leave approvals |
| 💰 **Accounts** | Income vs expenses by month, category donuts, payment modes |
| 📅 **Attendance** | Trend line, per-class bars, students below threshold |
| 📝 **Academics** | Subject averages, grade distribution, toppers, at-risk list |

---

## 🚀 Quick Start

### Option 1: Run Locally

```bash
# 1. Navigate to project folder
cd school-erp-demo

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py

# 4. Open in browser
# http://localhost:7860
```

### Option 2: Deploy to Hugging Face Spaces (Recommended)

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Create account if needed
3. Fill in:
   - **Space name**: `school-erp`
   - **SDK**: `Gradio`
   - **Hardware**: `CPU Basic (Free)`
4. Click "Create Space"
5. Upload all files from this folder
6. Wait 2-3 minutes for build
7. Share your URL!

---

## 📁 Project Structure

```
school-erp-demo/
│
├── app.py                 # ⭐ Main application - wiring only (START HERE)
├── requirements.txt       # Dependencies
├── README.md              # This file
│
├── config/
│   └── settings.py        # All configuration (school, fees, profiles)
│
├── database/
│   ├── connection.py      # Database connection utilities
│   ├── schema.py          # Table definitions + migrations
│   └── demo_data.py       # Generates realistic, self-consistent data
│
├── modules/               # One class per domain = the "tools"
│   ├── students.py        # Student queries
│   ├── staff.py           # Staff + leave queries
│   ├── accounts.py        # Income/expense queries
│   ├── attendance.py      # Attendance queries
│   └── academics.py       # Exam results and performance
│
├── ui/                    # All presentation code
│   ├── theme.py           # Colour palette + CSS
│   ├── charts.py          # SVG bar/line/donut/progress charts
│   ├── cards.py           # KPI cards, alerts, tables
│   └── views.py           # Composes one function per dashboard tab
│
└── llm/
    ├── client.py          # LLM connection + offline fallback
    └── prompts.py         # AI prompts
```

**Layering:** `modules/` answers *what the data is*, `ui/` decides *how it
looks*, and `app.py` only wires the two together. You can redesign the whole
dashboard without touching a single SQL query.

---

## 💬 Example Questions

### Students
- "How many students are enrolled?"
- "Show fee defaulters"
- "Students in Class 10"
- "Total pending fees"
- "Gender distribution"

### Staff
- "How many teachers?"
- "Who teaches Mathematics?"
- "Total salary expense"
- "Staff on leave"
- "Highest paid employees"

### Accounts
- "Total income this month"
- "Total expenses"
- "What is the balance?"
- "Compare income vs expenses"
- "Show expense breakdown"

### Attendance
- "Today's attendance"
- "Who is absent today?"
- "Students below 75% attendance"
- "Class 10 attendance"
- "Attendance trend"

---

## ⚙️ Customization

### Change School Name
Edit `config/settings.py`:
```python
SCHOOL_NAME = "Your School Name"
```

### Change Fee Structure
Edit `config/settings.py`:
```python
FEE_STRUCTURE = {
    1: 4000,   # Class 1 fee
    2: 4000,   # Class 2 fee
    # ... etc
}
```

### Regenerate Demo Data

```bash
python -m database.demo_data --force
```

The generator uses a **fixed random seed**, so the numbers are identical every
time you run the demo. All dates are generated **relative to today**, so
"today's attendance" is always genuinely today.

### Tune the story the data tells

`config/settings.py` → `STUDENT_PROFILES` controls the mix of students:

```python
STUDENT_PROFILES = [
    # name,       weight, attendance_rate, fee_status
    ("excellent",  0.45,   0.98,  "paid"),
    ("regular",    0.33,   0.93,  "paid"),
    ("irregular",  0.14,   0.82,  "partial"),
    ("at_risk",    0.06,   0.68,  "partial"),
    ("critical",   0.02,   0.52,  "pending"),
]
```

Each student's profile drives their attendance, their fees **and** their exam
marks. Raise the `at_risk` weight and the "students needing support" list grows
accordingly — everything stays consistent.

---

## 🎬 Suggested Demo Flow

1. **Overview tab** — lead with the KPI cards and the "needs attention" panel.
2. **Ask AI** — *"Which students are below 75% attendance?"*
3. **Attendance tab** — show the same students in the dashboard, with parent
   phone numbers ready to call.
4. **Ask AI** — *"Which students are struggling?"* — this joins low marks with
   low attendance to explain *why*.
5. **Accounts tab** — month-on-month income vs expenses.
6. **Ask AI** — *"Compare income vs expenses by month"* — same answer, in words.

The point to land: **the chat and the dashboard read from the same data**, so
the AI can never contradict the numbers on screen.

---

## ✅ Data Integrity

The demo data is intentionally self-consistent:

- `SUM(total_fees) - SUM(fees_pending)` exactly equals total fee income
- A student marked `pending` genuinely has missing payment rows
- Exam marks correlate with attendance, so "at risk" students are believable
- ~60 students fall below the 75% attendance threshold, so that query is never
  an empty list

---

## 🧠 Learning Guide

### How This App Works

```
User Question
     ↓
┌─────────────┐
│   Gradio    │  ← UI Framework (creates web interface)
└──────┬──────┘
       ↓
┌─────────────┐
│   app.py    │  ← Main logic (connects everything)
└──────┬──────┘
       ↓
   ┌───┴───┐
   ↓       ↓
┌─────┐ ┌─────┐
│ DB  │ │ LLM │  ← Database (data) + AI (understanding)
└─────┘ └─────┘
       ↓
┌─────────────┐
│  Response   │  ← AI-generated answer
└─────────────┘
```

### Key Concepts

1. **Agent = LLM + Tools**
   - LLM understands questions
   - Tools (database queries) get data
   - Together = intelligent assistant

2. **Prompt Engineering**
   - See `llm/prompts.py`
   - We tell the AI what it is and how to behave
   - We provide data context

3. **Modular Architecture**
   - Each module handles one domain
   - Easy to add new modules
   - Easy to modify existing ones

---

## 🔧 Troubleshooting

### "No module named..."
```bash
pip install -r requirements.txt
```

### "Database is empty"
Delete `school_data.db` and restart.

### "LLM not responding"
- Check internet connection
- Hugging Face might be busy, wait and retry
- The app has fallback responses

### "Port already in use"
```bash
# Kill process on port 7860
lsof -ti:7860 | xargs kill -9
```

---

## 🎓 What You'll Learn

By studying this code, you'll understand:

- ✅ How LLMs work in real applications
- ✅ How to build AI-powered chat interfaces
- ✅ Database design and queries
- ✅ Modular code architecture
- ✅ Prompt engineering basics
- ✅ Deploying AI apps to the cloud

---

## 📝 Next Steps (Ideas)

1. **Add more modules**: Library, Transport, Exams
2. **Add authentication**: Login for different users
3. **Real database**: Supabase/PostgreSQL
4. **Better LLM**: Claude API for smarter responses
5. **PDF reports**: Generate downloadable reports
6. **WhatsApp bot**: Connect via Twilio
7. **Hindi support**: Multi-language queries

---

## 📄 License

MIT License - Feel free to use, modify, and share!

---

## 🤝 Contributing

This is a learning project. Feel free to:
- Ask questions
- Suggest improvements
- Add features
- Fix bugs

---

**Built for learning AI, Agents, and LLMs** 🚀
