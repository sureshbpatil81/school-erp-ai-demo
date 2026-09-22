"""
THEME.PY - Colours and CSS
===========================

All visual styling lives here.

LEARNING POINT:
- Defining the palette once, in Python, means the charts and the cards can
  never drift out of sync with the stylesheet.
- Everything uses CSS variables so switching to a dark theme later is a
  one-line change.
"""

# =============================================================================
# COLOUR PALETTE
# =============================================================================

COLORS = {
    'primary':   '#4f46e5',
    'secondary': '#0ea5e9',
    'success':   '#10b981',
    'warning':   '#f59e0b',
    'danger':    '#ef4444',
    'purple':    '#8b5cf6',
    'pink':      '#ec4899',
    'teal':      '#14b8a6',
    'slate':     '#64748b',
}

# Ordered list used when a chart needs N distinct colours
CHART_PALETTE = [
    '#4f46e5', '#0ea5e9', '#10b981', '#f59e0b',
    '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6',
]

# Gradients for the KPI cards
GRADIENTS = {
    'indigo': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'green':  'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'pink':   'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'blue':   'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'orange': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'teal':   'linear-gradient(135deg, #0093E9 0%, #80D0C7 100%)',
    'dark':   'linear-gradient(135deg, #434343 0%, #262626 100%)',
    'violet': 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
}


# =============================================================================
# STYLESHEET
# =============================================================================

CUSTOM_CSS = """
/* ---------- Layout ---------------------------------------------------- */
.gradio-container {
    max-width: 1400px !important;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* ---------- App header ------------------------------------------------ */
.app-header {
    background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 50%, #0ea5e9 100%);
    border-radius: 16px;
    padding: 26px 32px;
    color: #fff;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(79, 70, 229, .25);
}
.app-header h1 {
    margin: 0;
    font-size: 1.9em;
    font-weight: 700;
    letter-spacing: -.5px;
    color: #fff;
}
.app-header p {
    margin: 6px 0 0;
    opacity: .9;
    font-size: .95em;
}
.header-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
}
.header-chip {
    background: rgba(255, 255, 255, .18);
    border: 1px solid rgba(255, 255, 255, .25);
    padding: 5px 12px;
    border-radius: 999px;
    font-size: .8em;
    backdrop-filter: blur(6px);
}

/* ---------- KPI cards ------------------------------------------------- */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin: 4px 0 18px;
}
.kpi-card {
    border-radius: 14px;
    padding: 18px 20px;
    color: #fff;
    position: relative;
    overflow: hidden;
    box-shadow: 0 6px 18px rgba(15, 23, 42, .14);
    transition: transform .18s ease, box-shadow .18s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 26px rgba(15, 23, 42, .22);
}
.kpi-icon   { font-size: 1.5em; opacity: .95; }
.kpi-value  { font-size: 1.9em; font-weight: 700; line-height: 1.15; margin-top: 4px; }
.kpi-label  { font-size: .82em; opacity: .92; text-transform: uppercase; letter-spacing: .6px; }
.kpi-sub    { font-size: .78em; opacity: .85; margin-top: 6px; }

/* ---------- Panels ---------------------------------------------------- */
/* NOTE: never hardcode a white background here. Gradio's dark theme keeps
   --body-text-color light, so a forced #fff panel renders white-on-white and
   the content becomes invisible. Follow the theme's own block colour instead. */
.panel {
    background: var(--block-background-fill, var(--background-fill-primary, #fff));
    color: var(--body-text-color, #0f172a);
    border: 1px solid rgba(100, 116, 139, .18);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.panel-title {
    font-weight: 650;
    font-size: 1em;
    margin: 0 0 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--body-text-color, #0f172a);
}

/* ---------- Alerts ---------------------------------------------------- */
/* Each alert pins BOTH its background and its text colour. A translucent
   rgba() tint alone is not enough: the text would inherit the theme's colour,
   which is near-white in dark mode and unreadable on a light tint. Pairing an
   opaque light background with a dark accent text keeps these legible in
   light and dark themes alike (all pairs clear WCAG AA). */
.alert {
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    border-left: 4px solid;
    font-size: .9em;
}
.alert-danger  { background: #fef2f2; border-color: #ef4444; color: #991b1b; }
.alert-warning { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
.alert-success { background: #ecfdf5; border-color: #10b981; color: #065f46; }
.alert-info    { background: #eff6ff; border-color: #0ea5e9; color: #075985; }

/* Inherit the parent alert's colour so the heading never falls back to the
   theme text colour. */
.alert-title   { font-weight: 650; margin-bottom: 2px; color: inherit; }
.alert div     { color: inherit; }

/* ---------- Badges ---------------------------------------------------- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: .76em;
    font-weight: 600;
}
/* Opaque backgrounds: a translucent tint over a dark theme surface would
   darken the chip and kill the contrast with the dark accent text. */
.badge-green { background: #d1fae5; color: #065f46; }
.badge-red   { background: #fee2e2; color: #991b1b; }
.badge-amber { background: #fef3c7; color: #92400e; }

/* ---------- Charts ---------------------------------------------------- */
.chart-wrap { width: 100%; overflow-x: auto; }
.chart-wrap svg { max-width: 100%; height: auto; display: block; }

/* ---------- Data tables ----------------------------------------------- */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: .88em;
    color: var(--body-text-color, #0f172a);
}
.data-table th {
    text-align: left;
    padding: 9px 12px;
    background: rgba(100, 116, 139, .10);
    font-weight: 650;
    color: var(--body-text-color, #0f172a);
    border-bottom: 2px solid rgba(100, 116, 139, .18);
}
.data-table td {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(100, 116, 139, .12);
}
.data-table tr:hover td { background: rgba(79, 70, 229, .05); }
.text-right { text-align: right; }

/* ---------- Footer ---------------------------------------------------- */
.app-footer {
    text-align: center;
    font-size: .82em;
    opacity: .7;
    padding: 14px 0 4px;
}

/* ---------- Mobile ---------------------------------------------------- */
@media (max-width: 640px) {
    .app-header { padding: 18px; }
    .app-header h1 { font-size: 1.4em; }
    .kpi-value { font-size: 1.5em; }
}
"""
