"""One colour palette for the presentation app (theme, Altair charts and the Graphviz pipeline).

`.streamlit/config.toml` carries the same values as theme tokens; keep both in sync.
"""

INK = "#172724"  # body text
MUTED = "#5b6b66"  # secondary text, axes
GREEN = "#176153"  # main data/brand colour
ORANGE = "#b4541c"  # primary/accent, thresholds (white text contrast ≥ 4.5:1)
BLUE = "#2f6690"  # reference/information
GRAY = "#7a8a84"  # planned/neutral
BORDER = "#d9e4df"

# Light fills for pipeline-stage states (READY, NEXT, REFERENCE, PLANNED).
STAGE_FILLS = {"READY": "#d8ece2", "NEXT": "#f6dcc8", "REFERENCE": "#dbe7f2", "PLANNED": "#eceeee"}
