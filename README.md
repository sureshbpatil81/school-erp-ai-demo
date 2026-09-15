# 🏫 School ERP AI Assistant

An AI-powered school management system that lets you query school data using natural language.

**Built with:** Python + Gradio + Hugging Face + SQLite

---

## 🎯 What This Does

- **Chat Interface**: Ask questions in plain English
- **4 Modules**: Students, Staff, Accounts, Attendance
- **LLM-Powered**: Uses Mistral 7B (free) for understanding
- **Demo Data**: 1000 students, 50 staff, 4 months of data

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
├── app.py                 # ⭐ Main application (START HERE)
├── requirements.txt       # Dependencies
├── README.md             # This file
│
├── config/
│   └── settings.py       # All configuration (school name, fees, etc.)
│
├── database/
│   ├── connection.py     # Database connection utilities
│   ├── schema.py         # Table definitions
│   └── demo_data.py      # Generates fake data
│
├── modules/
│   ├── students.py       # Student queries
│   ├── staff.py          # Staff queries
│   ├── accounts.py       # Income/expense queries
│   └── attendance.py     # Attendance queries
│
└── llm/
    ├── client.py         # LLM connection
    └── prompts.py        # AI prompts
```

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
Delete `school_data.db` and restart the app.

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
