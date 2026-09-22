"""
CARDS.PY - KPI cards, panels, alerts and tables
================================================

Small HTML builders used to assemble the dashboard.

LEARNING POINT:
Every value that originates from the database is passed through html.escape().
Even in a demo with generated names this is worth doing: it is the habit that
prevents an HTML-injection bug the day the app is pointed at real data.
"""

from html import escape
from typing import List, Dict

from .theme import GRADIENTS


def kpi_card(icon: str, value: str, label: str, gradient: str = 'indigo',
             sub: str = "") -> str:
    """A single gradient KPI tile."""
    background = GRADIENTS.get(gradient, GRADIENTS['indigo'])
    sub_html = f'<div class="kpi-sub">{escape(sub)}</div>' if sub else ''
    return (
        f'<div class="kpi-card" style="background:{background}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-value">{escape(str(value))}</div>'
        f'<div class="kpi-label">{escape(label)}</div>'
        f'{sub_html}</div>'
    )


def kpi_grid(cards: List[str]) -> str:
    """Arrange KPI cards in a responsive grid."""
    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def panel(title: str, body: str) -> str:
    """A titled content panel."""
    return (
        f'<div class="panel"><div class="panel-title">{title}</div>{body}</div>'
    )


def alert(kind: str, title: str, message: str) -> str:
    """
    A coloured alert strip.

    kind: 'danger' | 'warning' | 'success' | 'info'
    """
    return (
        f'<div class="alert alert-{kind}">'
        f'<div class="alert-title">{escape(title)}</div>'
        f'<div>{escape(message)}</div></div>'
    )


def data_table(rows: List[Dict], columns: List[tuple], empty_msg: str = "No records found") -> str:
    """
    Render a list of dicts as an HTML table.

    Args:
        rows: query results
        columns: list of (dict_key, "Header") or (dict_key, "Header", "money"|"num"|"pct")
    """
    if not rows:
        return (
            f'<div style="padding:20px;text-align:center;opacity:.6;font-size:.9em">'
            f'{escape(empty_msg)}</div>'
        )

    head = ''.join(
        f'<th class="{"text-right" if len(c) > 2 else ""}">{escape(c[1])}</th>'
        for c in columns
    )

    body_rows = []
    for row in rows:
        cells = []
        for col in columns:
            key, _header = col[0], col[1]
            fmt = col[2] if len(col) > 2 else None
            raw = row.get(key)

            if raw is None:
                text = '—'
            elif fmt == 'money':
                text = f"₹{float(raw):,.0f}"
            elif fmt == 'num':
                text = f"{float(raw):,.0f}"
            elif fmt == 'pct':
                text = f"{float(raw):,.1f}%"
            else:
                text = str(raw)

            css = ' class="text-right"' if fmt else ''
            cells.append(f'<td{css}>{escape(text)}</td>')
        body_rows.append(f'<tr>{"".join(cells)}</tr>')

    return (
        f'<div style="overflow-x:auto"><table class="data-table">'
        f'<thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table></div>'
    )


def header(school_name: str, chips: List[str]) -> str:
    """The gradient app header with status chips."""
    chip_html = ''.join(f'<span class="header-chip">{escape(c)}</span>' for c in chips)
    return (
        f'<div class="app-header">'
        f'<h1>🏫 {escape(school_name)}</h1>'
        f'<p>AI-powered management assistant — ask anything in plain English</p>'
        f'<div class="header-meta">{chip_html}</div>'
        f'</div>'
    )
