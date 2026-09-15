import gradio as gr
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import SCHOOL_NAME, APP_TITLE
from database.schema import create_tables
from database.demo_data import generate_all_demo_data
from modules.students import StudentModule
from modules.staff import StaffModule
from modules.accounts import AccountsModule
from modules.attendance import AttendanceModule
from llm.client import LLMClient


def initialize_app():
    create_tables()
    generate_all_demo_data()


initialize_app()
llm_client = LLMClient()


def get_all_summaries():
    return {
        "students": StudentModule.get_summary(),
        "staff": StaffModule.get_summary(),
        "accounts": AccountsModule.get_summary(),
        "attendance": AttendanceModule.get_summary(),
    }


def get_detailed_data(question: str) -> str:
    q = question.lower()
    out = ""
    if "fee" in q and ("defaulter" in q or "pending" in q):
        rows = StudentModule.get_fee_defaulters()[:10]
        if rows:
            out += "\nTOP FEE DEFAULTERS:\n" + "\n".join(
                f"• {r['name']} (Class {r['class']}-{r['section']}): ₹{r['fees_pending']:,.0f} pending"
                for r in rows
            )
    for class_num in range(1, 13):
        if f"class {class_num}" in q or f"class{class_num}" in q:
            students = StudentModule.get_students_by_class(class_num)
            sections = StudentModule.get_section_wise_count(class_num)
            out += f"\nCLASS {class_num}: {len(students)} students\n"
            out += "\n".join(f"• Section {s['section']}: {s['count']} students" for s in sections)
            break
    if "teacher" in q or "teach" in q:
        for subject in ["math", "physics", "chemistry", "biology", "english", "hindi"]:
            if subject in q:
                rows = StaffModule.get_teachers_by_subject(subject)
                out += f"\n{subject.upper()} TEACHERS:\n" + "\n".join(
                    f"• {r['name']} ({r['designation']})" for r in rows
                )
                break
    if "salary" in q or "highest paid" in q:
        rows = StaffModule.get_highest_paid()[:5]
        out += "\nHIGHEST PAID STAFF:\n" + "\n".join(
            f"• {r['name']} ({r['designation']}): ₹{r['salary']:,.0f}" for r in rows
        )
    if "absent" in q:
        rows = AttendanceModule.get_absentees()[:10]
        out += "\nRECENT ABSENTEES:\n" + "\n".join(
            f"• {r['name']} (Class {r['class']}-{r['section']})" for r in rows
        )
    if "chronic" in q or "below 75" in q:
        rows = AttendanceModule.get_chronic_absentees()[:10]
        out += "\nSTUDENTS BELOW 75% ATTENDANCE:\n" + "\n".join(
            f"• {r['name']} (Class {r['class']}): {r['percentage']}%" for r in rows
        )
    if "month" in q and "compare" in q:
        rows = AccountsModule.get_monthly_comparison()
        out += "\nMONTHLY COMPARISON:\n" + "\n".join(
            f"• {r['month']}: Income ₹{r['income']:,.0f}, Expenses ₹{r['expenses']:,.0f}, Balance ₹{r['balance']:,.0f}"
            for r in rows
        )
    return out


def answer(message, history):
    if not message or not message.strip():
        return "Please ask a question about the school."
    return llm_client.generate_response(
        question=message,
        context_data=get_all_summaries(),
        additional_data=get_detailed_data(message),
        max_tokens=500,
        temperature=0.5,
    )


def money(v):
    v = float(v or 0)
    if abs(v) >= 10000000:
        return f"₹{v/10000000:.2f}Cr"
    if abs(v) >= 100000:
        return f"₹{v/100000:.1f}L"
    return f"₹{v:,.0f}"


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def dashboard_html():
    s = get_all_summaries()
    st, sf, ac, at = s["students"], s["staff"], s["accounts"], s["attendance"]
    pending = st["fees_pending"]
    collection = st["fee_collection_rate"]
    attendance = at["today_percentage"]
    balance = ac["balance"]
    greeting = get_greeting()
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
    <div class='hero'>
      <div>
        <div class='eyebrow'>EXECUTIVE OVERVIEW · {today.upper()}</div>
        <h1>{greeting}, Administrator.</h1>
        <p>One intelligent view of {SCHOOL_NAME}. Ask the AI Copilot anything about students, people, attendance or finances.</p>
      </div>
      <div class='hero-badge'><span class='pulse'></span> AI SYSTEM ONLINE</div>
    </div>
    <div class='kpis'>
      <div class='kpi'><div class='kpi-top'><span class='kpi-icon blue'>◉</span><span class='trend'>+4.2%</span></div><div class='kpi-value'>{st['total_students']:,}</div><div class='kpi-label'>Total students</div></div>
      <div class='kpi'><div class='kpi-top'><span class='kpi-icon violet'>◆</span><span class='trend'>Active</span></div><div class='kpi-value'>{sf['total_staff']}</div><div class='kpi-label'>Teaching & support staff</div></div>
      <div class='kpi'><div class='kpi-top'><span class='kpi-icon green'>₹</span><span class='trend'>Healthy</span></div><div class='kpi-value'>{money(balance)}</div><div class='kpi-label'>Current balance</div></div>
      <div class='kpi'><div class='kpi-top'><span class='kpi-icon amber'>↗</span><span class='trend'>Today</span></div><div class='kpi-value'>{attendance}%</div><div class='kpi-label'>Attendance</div></div>
    </div>
    <div class='grid2'>
      <div class='panel'>
        <div class='panel-head'><div><div class='panel-title'>Management snapshot</div><div class='panel-sub'>Key signals requiring attention</div></div><span class='chip'>TODAY</span></div>
        <div class='signal'><span class='dot green-dot'></span><div><b>Attendance is strong</b><small>{at['today_present']:,} present · {at['today_absent']:,} absent</small></div><strong>{attendance}%</strong></div>
        <div class='signal'><span class='dot amber-dot'></span><div><b>Fees need attention</b><small>{st['students_with_pending']} students have pending fees</small></div><strong>{money(pending)}</strong></div>
        <div class='signal'><span class='dot blue-dot'></span><div><b>Collection rate</b><small>Expected fee collection across students</small></div><strong>{collection}%</strong></div>
      </div>
      <div class='panel insight'>
        <div class='panel-head'><div><div class='panel-title'>AI insight</div><div class='panel-sub'>What the assistant can surface</div></div><span class='ai-chip'>✦ AI</span></div>
        <div class='insight-main'>Ask a question. Get an answer grounded in your school data.</div>
        <div class='suggestion-row'><span>“Which classes need attention?”</span><span>“Show fee defaulters”</span></div>
        <div class='suggestion-row'><span>“Compare income vs expenses”</span><span>“Who teaches Maths?”</span></div>
      </div>
    </div>
    """


def students_table():
    rows = StudentModule.get_fee_defaulters()[:12]
    return [[r["name"], f"Class {r['class']}-{r['section']}", r["fees_status"].title(), money(r["fees_pending"])] for r in rows]


def staff_table():
    rows = StaffModule.get_highest_paid()[:12]
    return [[r["name"], r["designation"], r["role"], money(r["salary"])] for r in rows]


def attendance_table():
    rows = AttendanceModule.get_absentees()[:12]
    return [[r["name"], f"Class {r['class']}-{r['section']}", r["roll_no"]] for r in rows]


def finance_table():
    rows = AccountsModule.get_expenses_by_category()
    return [[r["category"].title(), money(r["total"]), r["count"]] for r in rows]


CSS = """
* { box-sizing:border-box; }
html, body {
  margin:0!important; padding:0!important;
  background:#080c16!important; color:#eef2ff!important;
}
body { min-height:100vh!important; }
.gradio-container {
  max-width:1500px!important;
  min-height:100vh!important;
  margin:0 auto!important;
  padding:0 34px 44px!important;
  background:#080c16!important;
  color:#eef2ff!important;
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;
}
footer { display:none!important; }

/* Product header */
.brandbar {
  height:72px!important; display:flex!important; align-items:center!important;
  border-bottom:1px solid rgba(255,255,255,.07)!important;
  margin:0 -34px 26px!important; padding:0 34px!important;
  background:rgba(8,12,22,.94)!important;
  color:#fff!important;
}
.brand-logo {
  width:34px;height:34px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,#5d7cff,#8a63ff);
  color:white;font-weight:900;font-size:15px;
  box-shadow:0 8px 24px rgba(99,108,255,.25);
}
.brand-name { margin-left:11px;font-weight:850;font-size:16px;letter-spacing:-.02em;color:#fff!important; }
.brand-meta { margin-left:8px;color:#65718a!important;font-size:10px;font-weight:700;letter-spacing:.12em; }
.brand-spacer { flex:1; }
.top-status {
  display:flex;align-items:center;gap:8px;color:#91a0b8;font-size:11px;font-weight:700;
  padding:8px 12px;border:1px solid rgba(255,255,255,.07);border-radius:10px;
  background:#0e1422;
}
.status-dot {
  width:7px;height:7px;border-radius:50%;background:#4bd5a2;
  box-shadow:0 0 0 4px rgba(75,213,162,.09);
  animation: status-pulse 2.5s ease-in-out infinite;
}
@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Hero */
.hero {
  position:relative; overflow:hidden;
  min-height:190px!important;
  background:
    radial-gradient(circle at 85% 20%,rgba(101,116,255,.28),transparent 34%),
    radial-gradient(circle at 68% 100%,rgba(124,82,255,.18),transparent 32%),
    linear-gradient(135deg,#11182b,#10172a 58%,#141d35)!important;
  border:1px solid rgba(130,151,210,.13)!important;
  border-radius:26px!important; padding:32px 34px!important;
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:18px!important;
  box-shadow:0 25px 70px rgba(0,0,0,.32)!important;
}
.hero:after {
  content:""; position:absolute; right:-80px; bottom:-110px; width:300px;height:300px;
  border:1px solid rgba(130,150,255,.13);border-radius:50%;
  box-shadow:0 0 0 45px rgba(130,150,255,.025),0 0 0 90px rgba(130,150,255,.018);
}
.hero h1 {
  color:#fff!important;font-size:34px!important;line-height:1.12!important;
  letter-spacing:-.045em!important;margin:5px 0 10px!important;
}
.hero p { color:#8f9db5!important;max-width:650px!important;font-size:13px!important;line-height:1.65!important; }
.eyebrow { color:#8299ff!important;font-size:10px!important;font-weight:800!important;letter-spacing:.16em!important; }
.hero-badge {
  position:relative;z-index:2;display:flex;align-items:center;gap:9px;
  color:#a9b5ce!important;background:rgba(255,255,255,.045)!important;
  border:1px solid rgba(255,255,255,.09)!important;border-radius:12px!important;
  padding:10px 13px!important;font-size:10px!important;font-weight:800!important;
}
.pulse {
  width:7px;height:7px;border-radius:50%;background:#4bd5a2;
  box-shadow:0 0 0 5px rgba(75,213,162,.10);
  animation: pulse-glow 2s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 5px rgba(75,213,162,.10); }
  50% { box-shadow: 0 0 0 8px rgba(75,213,162,.25); }
}

/* KPI strip */
.kpis { display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px; }
.kpi {
  background:#0e1422!important;border:1px solid rgba(255,255,255,.065)!important;
  border-radius:18px!important;padding:17px 18px!important;
  box-shadow:0 10px 28px rgba(0,0,0,.15)!important;
  transition:.2s ease;
}
.kpi:hover {
  transform:translateY(-3px);
  border-color:rgba(120,143,220,.22)!important;
  box-shadow:0 16px 40px rgba(0,0,0,.22)!important;
}
.kpi { cursor:default; }
.kpi-top { display:flex;justify-content:space-between;align-items:center;margin-bottom:13px; }
.kpi-icon {
  width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:900;
}
.kpi-value { color:#f6f8ff!important;font-size:25px!important;font-weight:820!important;letter-spacing:-.04em!important; }
.kpi-label { color:#748199!important;font-size:11px!important;margin-top:4px!important; }
.kpi-icon.blue {background:rgba(93,124,255,.12)!important;color:#8da3ff!important;}
.kpi-icon.violet {background:rgba(145,104,255,.12)!important;color:#b194ff!important;}
.kpi-icon.green {background:rgba(75,213,162,.10)!important;color:#6fe1b8!important;}
.kpi-icon.amber {background:rgba(233,180,93,.10)!important;color:#f0c47c!important;}
.trend {
  background:rgba(75,213,162,.07)!important;color:#65d9ac!important;
  border:1px solid rgba(75,213,162,.10)!important;border-radius:7px!important;
  padding:4px 7px!important;font-size:9px!important;font-weight:800!important;
}

/* Snapshot */
.grid2 { display:grid;grid-template-columns:1.08fr .92fr;gap:14px; }
.panel {
  background:#0e1422!important;border:1px solid rgba(255,255,255,.065)!important;
  border-radius:20px!important;padding:20px!important;
  box-shadow:0 10px 30px rgba(0,0,0,.14)!important;
}
.panel-head { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px; }
.panel-title { color:#edf1fc!important;font-size:14px!important;font-weight:800!important;letter-spacing:-.01em!important; }
.panel-sub { color:#65728a!important;font-size:10px!important;margin-top:4px!important; }
.chip,.ai-chip {
  font-size:8px!important;font-weight:850!important;letter-spacing:.11em!important;
  padding:6px 8px!important;border-radius:7px!important;
}
.chip { background:#151d2d!important;color:#7d8ba5!important;border:1px solid rgba(255,255,255,.06)!important; }
.ai-chip { background:rgba(145,104,255,.10)!important;color:#ad94ff!important;border:1px solid rgba(145,104,255,.14)!important; }
.signal {
  display:grid!important;grid-template-columns:9px 1fr auto;gap:11px;align-items:center;
  padding:13px 0!important;border-top:1px solid rgba(255,255,255,.055)!important;
}
.signal:first-of-type { border-top:0!important; }
.dot { width:7px;height:7px;border-radius:50%; }
.green-dot{background:#4bd5a2}.amber-dot{background:#e9b45d}.blue-dot{background:#6c88ff}
.signal b { color:#dfe5f4!important;font-size:11px!important;font-weight:750!important;display:block!important; }
.signal small { color:#64728b!important;font-size:9px!important;display:block!important;margin-top:3px!important; }
.signal strong { color:#eef2ff!important;font-size:11px!important; }

/* AI insight */
.insight {
  background:
    radial-gradient(circle at 100% 0%,rgba(113,94,255,.13),transparent 42%),
    #10172a!important;
}
.insight-main { color:#eef2ff!important;font-size:18px!important;font-weight:700!important;line-height:1.35!important;letter-spacing:-.025em!important;margin:18px 0!important;max-width:420px; }
.suggestion-row { display:flex;gap:8px;margin-top:8px!important; }
.suggestion-row span {
  flex:1;background:#151e31!important;border:1px solid rgba(255,255,255,.055)!important;
  color:#8c9ab3!important;border-radius:9px!important;padding:9px 10px!important;
  font-size:9px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
  transition: all 0.2s ease;
  cursor:pointer;
}
.suggestion-row span:hover {
  background:#1a2540!important;
  border-color:rgba(130,150,255,.18)!important;
  color:#b8c4e0!important;
  transform:translateY(-1px);
}

/* Tabs as product navigation */
.tabs { margin-top:22px!important; }
.tabs > div:first-child {
  background:#0c121f!important;border:1px solid rgba(255,255,255,.06)!important;
  border-radius:13px!important;padding:4px!important;
}
.tabs button {
  background:transparent!important;color:#69768e!important;border:0!important;
  border-radius:9px!important;font-size:11px!important;font-weight:750!important;
  padding:9px 15px!important;
}
.tabs button.selected {
  color:#eef2ff!important;background:#17213a!important;
  box-shadow:0 4px 12px rgba(0,0,0,.2)!important;
}

/* Copilot — the star of the product */
.copilot {
  margin-top:18px!important;padding:0!important;overflow:hidden!important;
  background:#0a101c!important;border:1px solid rgba(111,136,255,.17)!important;
  border-radius:22px!important;box-shadow:0 28px 80px rgba(0,0,0,.34)!important;
}
.copilot-head {
  display:flex;justify-content:space-between;align-items:center;
  padding:20px 21px!important;
  background:linear-gradient(90deg,#0d1527,#101a31)!important;
  border-bottom:1px solid rgba(255,255,255,.065)!important;
}
.copilot-title { color:#f5f7ff!important;font-size:17px!important;font-weight:820!important;letter-spacing:-.02em!important; }
.copilot-sub { color:#697791!important;font-size:10px!important;margin-top:4px!important; }
.copilot-badge {
  color:#62dcae!important;background:rgba(75,213,162,.055)!important;
  border:1px solid rgba(75,213,162,.13)!important;border-radius:8px!important;
  padding:7px 9px!important;font-size:8px!important;font-weight:850!important;letter-spacing:.1em!important;
}
.copilot .gradio-chatbot {
  background:#090f1a!important;border:0!important;border-radius:0!important;
  min-height:330px!important;box-shadow:none!important;
}
.copilot .message-wrap,.copilot .wrap,.copilot .bubble-wrap { background:#090f1a!important; }
.copilot .message { color:#e9eefb!important; }
.copilot .bot {
  background:#111a2b!important;border:1px solid rgba(255,255,255,.06)!important;
  border-radius:14px!important;color:#e8edf9!important;
}
.copilot .user {
  background:linear-gradient(135deg,#536fff,#7458e9)!important;
  border-radius:14px!important;color:#fff!important;
}
.copilot .gr-row {
  background:#0a101c!important;padding:13px 15px 15px!important;
  border-top:1px solid rgba(255,255,255,.065)!important;
}
.copilot textarea,.copilot input,.copilot .gr-input {
  background:#111a2b!important;color:#f2f5ff!important;
  border:1px solid rgba(255,255,255,.09)!important;border-radius:12px!important;
  box-shadow:none!important;
}
.copilot textarea::placeholder,.copilot input::placeholder { color:#596983!important; }
.copilot .gr-button-primary {
  background:linear-gradient(135deg,#5a77ff,#7959e9)!important;color:white!important;
  border:0!important;border-radius:12px!important;font-weight:800!important;
  box-shadow:0 8px 20px rgba(89,103,255,.2)!important;
  transition: all 0.25s ease;
}
.copilot .gr-button-primary:hover {
  transform:translateY(-2px);
  box-shadow:0 12px 28px rgba(89,103,255,.35)!important;
  background:linear-gradient(135deg,#6a85ff,#8969f9)!important;
}
.copilot .examples-holder,.copilot .examples-container { background:#0a101c!important;border:0!important; }
.copilot .example {
  background:#111a2b!important;color:#7f8ca4!important;
  border:1px solid rgba(255,255,255,.055)!important;border-radius:8px!important;
}

/* Tables / content */
.section-title { color:#eef2ff!important; }
.section-sub { color:#697790!important; }
.gradio-container .prose,.gradio-container .markdown-text { color:#dce3f2!important; }
.gradio-container .dataframe,.gradio-container .table-wrap,
.gradio-container table { background:#0e1422!important;color:#e9eefb!important; }
.gradio-container th { background:#151e30!important;color:#8997af!important;border-color:rgba(255,255,255,.06)!important; }
.gradio-container td {
  background:#0e1422!important;color:#dfe6f5!important;border-color:rgba(255,255,255,.055)!important;
  transition: background 0.15s ease;
}
.gradio-container tr:hover td {
  background:#141d30!important;
}
.gradio-container .block { border-color:rgba(255,255,255,.055)!important; }

/* Mobile */
@media(max-width:900px){
  .gradio-container{padding:0 15px 30px!important}
  .brandbar{margin:0 -15px 18px!important;padding:0 15px!important}
  .brand-meta{display:none}
  .hero{padding:25px!important;display:block}
  .hero h1{font-size:28px!important}
  .hero-badge{display:inline-flex;margin-top:18px}
  .kpis{grid-template-columns:repeat(2,1fr)}
  .grid2{grid-template-columns:1fr}
  .tabs button{padding:8px 9px!important;font-size:10px!important}
}
"""


def create_ui():
    s = get_all_summaries()
    with gr.Blocks(title=f"{SCHOOL_NAME} · AI Management", theme=gr.themes.Base(), css=CSS) as demo:
        gr.HTML("""<div class="brandbar">
      <div class="brand-logo">A</div>
      <div class="brand-name">ATLAS</div>
      <div class="brand-meta">AI SCHOOL MANAGEMENT</div>
      <div class="brand-spacer"></div>
      <div class="top-status"><span class="status-dot"></span> System operational</div>
    </div>""")
        with gr.Tabs(elem_classes="tabs"):
            with gr.Tab("Overview"):
                gr.HTML(dashboard_html())
                with gr.Group(elem_classes="copilot"):
                    gr.HTML("""<div class='copilot-head'><div><div class='copilot-title'>✦ AI Copilot</div><div class='copilot-sub'>Ask anything about your school. AI answers are grounded in the live management database.</div></div><div class='copilot-badge'>● AI ONLINE</div></div>""")
                    chatbot = gr.Chatbot(height=380, show_label=False, layout="bubble", placeholder="<strong>What would you like to know?</strong><br>Try asking about students, fees, attendance or finance.")
                    with gr.Row():
                        msg = gr.Textbox(placeholder="Ask the school AI…", show_label=False, scale=8, lines=1)
                        send = gr.Button("Ask AI  →", variant="primary", scale=2)
                    gr.Examples(
                        examples=[
                            "How many students are enrolled?",
                            "Show me the top fee defaulters",
                            "What is today's attendance?",
                            "Compare income vs expenses",
                            "Who teaches Mathematics?",
                        ], inputs=msg
                    )

                    def submit_message(message, history):
                        if not message or not message.strip():
                            return history, ""
                        response = answer(message, history)
                        history = (history or []) + [[message, response]]
                        return history, ""
                    send.click(submit_message, [msg, chatbot], [chatbot, msg], api_name=False)
                    msg.submit(submit_message, [msg, chatbot], [chatbot, msg], api_name=False)

            with gr.Tab("Students & Fees"):
                gr.Markdown("### Student attention", elem_classes="section-title")
                gr.Markdown("Students with outstanding fee balances, ordered by amount.", elem_classes="section-sub")
                gr.Dataframe(headers=["Student","Class","Status","Pending"], value=students_table(), interactive=False, wrap=True)

            with gr.Tab("People"):
                gr.Markdown("### Teaching & support team", elem_classes="section-title")
                gr.Markdown("Highest-paid staff snapshot for management review.", elem_classes="section-sub")
                gr.Dataframe(headers=["Name","Designation","Role","Monthly salary"], value=staff_table(), interactive=False, wrap=True)

            with gr.Tab("Attendance"):
                gr.Markdown("### Attendance attention list", elem_classes="section-title")
                gr.Markdown("Recent absentees from the latest attendance date in the demo dataset.", elem_classes="section-sub")
                gr.Dataframe(headers=["Student","Class","Roll no."], value=attendance_table(), interactive=False, wrap=True)

            with gr.Tab("Finance"):
                gr.Markdown("### Expense intelligence", elem_classes="section-title")
                gr.Markdown("Category-level expense view for management oversight.", elem_classes="section-sub")
                gr.Dataframe(headers=["Category","Amount","Transactions"], value=finance_table(), interactive=False, wrap=True)

        gr.HTML("""
        <div style="text-align:center;padding:28px 0 10px;color:#4a5568;font-size:11px;border-top:1px solid rgba(255,255,255,.04);margin-top:30px;">
          <span style="color:#6b7280;">✦ ATLAS AI</span> · Demo Environment · All data is synthetic<br>
          <span style="opacity:0.6;font-size:10px;">Built with Gradio + Hugging Face · Powered by AI</span>
        </div>
        """)
    return demo


if __name__ == "__main__":
    print(f"Starting {SCHOOL_NAME} premium UI")
    demo = create_ui()
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        show_api=False,
    )
