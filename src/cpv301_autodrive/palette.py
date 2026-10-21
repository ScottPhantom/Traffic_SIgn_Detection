"""One colour palette for the presentation app (theme, Altair charts and the Graphviz pipeline).

`.streamlit/config.toml` carries the same values as `[theme.light]`/`[theme.dark]` tokens; keep both
in sync. Charts and the diagram are drawn by Python, so they read the active mode through
`current()` instead of inheriting the theme.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Palette:
    ink: str  # body text, chart labels
    muted: str  # secondary text, axes, edges
    data: str  # main data colour (primary)
    accent: str  # highlights and thresholds
    reference: str  # information/reference
    border: str
    stage_fills: dict[str, str]  # pipeline-stage states READY, NEXT, REFERENCE, PLANNED
    stage_ink: str  # text on stage fills


LIGHT = Palette(
    ink="#0f172a",
    muted="#64748b",
    data="#2563eb",
    accent="#c2410c",  # white-on-accent and accent-on-white contrast ≥ 4.5:1
    reference="#047857",
    border="#cbd5e1",
    stage_fills={
        "READY": "#d1fae5",
        "NEXT": "#ffedd5",
        "REFERENCE": "#dbeafe",
        "PLANNED": "#f1f5f9",
    },
    stage_ink="#0f172a",
)
DARK = Palette(
    ink="#e2e8f0",
    muted="#94a3b8",
    data="#60a5fa",
    accent="#fb923c",
    reference="#34d399",
    border="#334155",
    stage_fills={
        "READY": "#064e3b",
        "NEXT": "#7c2d12",
        "REFERENCE": "#1e3a8a",
        "PLANNED": "#1e293b",
    },
    stage_ink="#f1f5f9",
)

def current() -> Palette:
    """Palette of the viewer's active light/dark mode (light outside a browser session)."""
    try:
        return DARK if st.context.theme.type == "dark" else LIGHT
    except (AttributeError, RuntimeError):
        return LIGHT
