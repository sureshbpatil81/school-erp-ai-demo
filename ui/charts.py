"""
CHARTS.PY - Dependency-free SVG charts
=======================================

Every chart here is plain SVG built from Python strings.

WHY NOT PLOTLY / MATPLOTLIB?
- No extra dependency to install (important for a free Hugging Face Space)
- Renders instantly, no image encoding round-trip
- Scales crisply on any screen and respects the page's own CSS
- The whole file is readable: a bar chart really is just a <rect> per value

LEARNING POINT:
SVG uses a top-left origin, so a bar's y position is
(chart_height - bar_height), not the value itself. That single conversion is
the only tricky part of drawing charts by hand.
"""

from html import escape
from typing import List, Dict

from .theme import CHART_PALETTE, COLORS


# =============================================================================
# HELPERS
# =============================================================================

def _fmt_money(value: float) -> str:
    """Format a rupee amount in Indian short form (L = lakh, Cr = crore)."""
    value = float(value or 0)
    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f}Cr"
    if abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:.1f}L"
    if abs(value) >= 1_000:
        return f"₹{value / 1_000:.0f}K"
    return f"₹{value:.0f}"


def _empty(message: str = "No data available") -> str:
    """Placeholder shown when a query returns nothing."""
    return (
        f'<div style="padding:28px;text-align:center;opacity:.6;font-size:.9em">'
        f'{escape(message)}</div>'
    )


# =============================================================================
# BAR CHART
# =============================================================================

def bar_chart(
    data: List[Dict],
    label_key: str,
    value_key: str,
    height: int = 240,
    money: bool = False,
    suffix: str = "",
    color: str = None,
) -> str:
    """
    Vertical bar chart.

    Args:
        data: list of dicts
        label_key: dict key holding the x-axis label
        value_key: dict key holding the numeric value
        money: format values as rupees
        suffix: appended to the value label (e.g. "%")
        color: single colour; if None, cycles through the palette
    """
    if not data:
        return _empty()

    bar_w = 46
    gap = 18
    pad_left = 18
    pad_bottom = 42
    pad_top = 26
    width = pad_left * 2 + len(data) * (bar_w + gap)
    plot_h = height - pad_bottom - pad_top

    values = [float(row.get(value_key) or 0) for row in data]
    peak = max(values) if values else 0
    if peak <= 0:
        peak = 1

    parts = [
        f'<div class="chart-wrap"><svg viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">'
    ]

    # Horizontal grid lines give the eye a reference for the bar heights
    for i in range(1, 4):
        y = pad_top + plot_h * i / 4
        parts.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_left}" y2="{y:.1f}" '
            f'stroke="rgba(100,116,139,.18)" stroke-width="1"/>'
        )

    for idx, row in enumerate(data):
        value = float(row.get(value_key) or 0)
        bar_h = max((value / peak) * plot_h, 2)
        x = pad_left + idx * (bar_w + gap)
        y = pad_top + plot_h - bar_h
        fill = color or CHART_PALETTE[idx % len(CHART_PALETTE)]

        if money:
            value_text = _fmt_money(value)
        elif float(value).is_integer():
            value_text = f"{int(value):,}{suffix}"
        else:
            value_text = f"{value:,.1f}{suffix}"

        label = escape(str(row.get(label_key, '')))
        short = label if len(label) <= 9 else label[:8] + '…'

        parts.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" '
            f'rx="6" fill="{fill}" opacity=".9"><title>{label}: {value_text}</title></rect>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" '
            f'font-size="11" font-weight="600" fill="currentColor">{value_text}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - pad_bottom + 18}" '
            f'text-anchor="middle" font-size="11" fill="currentColor" opacity=".75">'
            f'{short}</text>'
        )

    parts.append('</svg></div>')
    return ''.join(parts)


# =============================================================================
# GROUPED BAR CHART (income vs expenses)
# =============================================================================

def grouped_bar_chart(
    data: List[Dict],
    label_key: str,
    series: List[tuple],
    height: int = 260,
    money: bool = True,
) -> str:
    """
    Side-by-side bars for comparing two or more series per category.

    Args:
        series: list of (dict_key, display_name, colour) tuples
    """
    if not data:
        return _empty()

    group_w = 34 * len(series) + 22
    pad_left = 20
    pad_top = 34
    pad_bottom = 44
    width = pad_left * 2 + len(data) * group_w
    plot_h = height - pad_top - pad_bottom

    peak = 0
    for row in data:
        for key, _name, _colour in series:
            peak = max(peak, float(row.get(key) or 0))
    if peak <= 0:
        peak = 1

    parts = [
        f'<div class="chart-wrap"><svg viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">'
    ]

    for i in range(1, 4):
        y = pad_top + plot_h * i / 4
        parts.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_left}" y2="{y:.1f}" '
            f'stroke="rgba(100,116,139,.18)" stroke-width="1"/>'
        )

    bar_w = 26
    for idx, row in enumerate(data):
        base_x = pad_left + idx * group_w + 8
        for s_idx, (key, name, colour) in enumerate(series):
            value = float(row.get(key) or 0)
            bar_h = max((value / peak) * plot_h, 2)
            x = base_x + s_idx * (bar_w + 6)
            y = pad_top + plot_h - bar_h
            text = _fmt_money(value) if money else f"{value:,.0f}"
            parts.append(
                f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" '
                f'rx="5" fill="{colour}" opacity=".9">'
                f'<title>{escape(name)}: {text}</title></rect>'
            )

        label = escape(str(row.get(label_key, '')))
        parts.append(
            f'<text x="{base_x + (len(series) * (bar_w + 6)) / 2 - 3:.1f}" '
            f'y="{height - pad_bottom + 18}" text-anchor="middle" font-size="11" '
            f'fill="currentColor" opacity=".75">{label}</text>'
        )

    # Legend across the top
    legend_x = pad_left
    for key, name, colour in series:
        parts.append(
            f'<rect x="{legend_x}" y="10" width="11" height="11" rx="3" fill="{colour}"/>'
        )
        parts.append(
            f'<text x="{legend_x + 16}" y="20" font-size="11" fill="currentColor">'
            f'{escape(name)}</text>'
        )
        legend_x += 26 + len(name) * 7

    parts.append('</svg></div>')
    return ''.join(parts)


# =============================================================================
# LINE CHART
# =============================================================================

def line_chart(
    data: List[Dict],
    label_key: str,
    value_key: str,
    height: int = 240,
    color: str = None,
    suffix: str = "%",
    y_min: float = None,
    y_max: float = None,
) -> str:
    """
    Line chart with a soft gradient fill underneath.

    LEARNING POINT:
    - For percentage data we deliberately do NOT start the y-axis at zero.
      Attendance moving between 88% and 96% looks completely flat on a 0-100
      axis; zooming the axis makes the real variation visible.
    """
    if not data:
        return _empty()
    if len(data) == 1:
        return bar_chart(data, label_key, value_key, height=height, suffix=suffix)

    colour = color or COLORS['primary']
    pad_left = 44
    pad_right = 16
    pad_top = 20
    pad_bottom = 40
    width = max(420, 52 * len(data))
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    values = [float(row.get(value_key) or 0) for row in data]
    lo = y_min if y_min is not None else min(values)
    hi = y_max if y_max is not None else max(values)
    if hi == lo:
        hi, lo = hi + 1, lo - 1
    span = hi - lo
    lo -= span * 0.15
    hi += span * 0.15
    span = hi - lo

    def point(idx: int, value: float):
        x = pad_left + (plot_w * idx / (len(data) - 1))
        y = pad_top + plot_h - ((value - lo) / span) * plot_h
        return x, y

    coords = [point(i, v) for i, v in enumerate(values)]
    line_pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in coords)
    area_pts = (
        f'{pad_left},{pad_top + plot_h} {line_pts} '
        f'{pad_left + plot_w},{pad_top + plot_h}'
    )

    uid = f"grad{abs(hash(str(values))) % 100000}"
    parts = [
        f'<div class="chart-wrap"><svg viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">',
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{colour}" stop-opacity=".35"/>'
        f'<stop offset="100%" stop-color="{colour}" stop-opacity="0"/>'
        f'</linearGradient></defs>',
    ]

    # Y-axis reference lines and labels
    for i in range(5):
        y = pad_top + plot_h * i / 4
        val = hi - span * i / 4
        parts.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
            f'stroke="rgba(100,116,139,.15)" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{pad_left - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="10" '
            f'fill="currentColor" opacity=".6">{val:.0f}{suffix}</text>'
        )

    parts.append(f'<polygon points="{area_pts}" fill="url(#{uid})"/>')
    parts.append(
        f'<polyline points="{line_pts}" fill="none" stroke="{colour}" '
        f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # Data points - label every Nth to avoid overlap on long series
    step = max(1, len(data) // 8)
    for idx, (x, y) in enumerate(coords):
        label = escape(str(data[idx].get(label_key, '')))
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#fff" stroke="{colour}" '
            f'stroke-width="2"><title>{label}: {values[idx]:.1f}{suffix}</title></circle>'
        )
        if idx % step == 0 or idx == len(data) - 1:
            short = label[-5:] if len(label) > 6 else label
            parts.append(
                f'<text x="{x:.1f}" y="{height - pad_bottom + 18}" text-anchor="middle" '
                f'font-size="10" fill="currentColor" opacity=".7">{short}</text>'
            )

    parts.append('</svg></div>')
    return ''.join(parts)


# =============================================================================
# DONUT CHART
# =============================================================================

def donut_chart(
    data: List[Dict],
    label_key: str,
    value_key: str,
    size: int = 210,
    money: bool = False,
) -> str:
    """
    Donut chart with a legend.

    LEARNING POINT:
    - Rather than computing arc paths with trigonometry, we draw one circle per
      slice and animate `stroke-dasharray`. The circumference is 2*pi*r, so a
      slice covering 25% simply uses a dash of 0.25 * circumference.
    """
    if not data:
        return _empty()

    total = sum(float(row.get(value_key) or 0) for row in data)
    if total <= 0:
        return _empty()

    radius = size / 2 - 22
    circumference = 2 * 3.14159265 * radius
    centre = size / 2

    parts = [
        '<div style="display:flex;align-items:center;gap:22px;flex-wrap:wrap">',
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img">',
        f'<circle cx="{centre}" cy="{centre}" r="{radius:.1f}" fill="none" '
        f'stroke="rgba(100,116,139,.13)" stroke-width="26"/>',
    ]

    offset = 0.0
    legend = ['<div style="font-size:.86em;line-height:1.9">']

    for idx, row in enumerate(data):
        value = float(row.get(value_key) or 0)
        share = value / total
        colour = CHART_PALETTE[idx % len(CHART_PALETTE)]
        dash = share * circumference
        label = escape(str(row.get(label_key, '')).title())
        text = _fmt_money(value) if money else f"{value:,.0f}"

        parts.append(
            f'<circle cx="{centre}" cy="{centre}" r="{radius:.1f}" fill="none" '
            f'stroke="{colour}" stroke-width="26" '
            f'stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {centre} {centre})">'
            f'<title>{label}: {text} ({share * 100:.1f}%)</title></circle>'
        )

        legend.append(
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="width:11px;height:11px;border-radius:3px;background:{colour};'
            f'display:inline-block;flex:none"></span>'
            f'<span style="flex:1"><b>{label}</b> &nbsp;{text} '
            f'<span style="opacity:.6">({share * 100:.1f}%)</span></span></div>'
        )
        offset += dash

    centre_text = _fmt_money(total) if money else f"{total:,.0f}"
    parts.append(
        f'<text x="{centre}" y="{centre - 2}" text-anchor="middle" font-size="17" '
        f'font-weight="700" fill="currentColor">{centre_text}</text>'
    )
    parts.append(
        f'<text x="{centre}" y="{centre + 16}" text-anchor="middle" font-size="10" '
        f'fill="currentColor" opacity=".6">TOTAL</text>'
    )
    parts.append('</svg>')
    legend.append('</div>')
    parts.append(''.join(legend))
    parts.append('</div>')
    return ''.join(parts)


# =============================================================================
# HORIZONTAL PROGRESS BARS
# =============================================================================

def progress_rows(
    data: List[Dict],
    label_key: str,
    value_key: str,
    max_value: float = 100,
    suffix: str = "%",
    danger_below: float = None,
) -> str:
    """
    A list of labelled horizontal bars.

    Ideal for "attendance by class" where a vertical bar chart with 12 columns
    would be cramped. Bars below `danger_below` turn red automatically.
    """
    if not data:
        return _empty()

    peak = max_value or max(float(r.get(value_key) or 0) for r in data) or 1
    rows = ['<div style="display:flex;flex-direction:column;gap:9px">']

    for row in data:
        value = float(row.get(value_key) or 0)
        pct = min(value / peak * 100, 100)

        if danger_below is not None and value < danger_below:
            colour = COLORS['danger']
        elif danger_below is not None and value < danger_below * 1.1:
            colour = COLORS['warning']
        else:
            colour = COLORS['success']

        label = escape(str(row.get(label_key, '')))
        rows.append(
            f'<div style="display:flex;align-items:center;gap:10px;font-size:.86em">'
            f'<span style="width:84px;flex:none;opacity:.8">{label}</span>'
            f'<span style="flex:1;background:rgba(100,116,139,.14);border-radius:999px;'
            f'height:9px;overflow:hidden">'
            f'<span style="display:block;width:{pct:.1f}%;height:100%;background:{colour};'
            f'border-radius:999px"></span></span>'
            f'<span style="width:58px;text-align:right;font-weight:600">'
            f'{value:,.1f}{suffix}</span></div>'
        )

    rows.append('</div>')
    return ''.join(rows)
