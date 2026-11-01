"""CPV301 AutoDrive — presentation-style Streamlit app (navigation shell).

The project is told as an 8-slide talk (`presentation.SLIDES`), one page per slide under
`app_pages/`. Views shared by the slides live in `views.py`; project status lives in
`project_status.py`, which mirrors `docs/product_roadmap.md`.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from cpv301_autodrive.presentation import SLIDES, page_path, presenting

LOGO = Path(__file__).parent / "assets" / "logo.svg"


def render_app() -> None:
    st.set_page_config(
        page_title="CPV301 AutoDrive",
        page_icon=":material/traffic:",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.logo(str(LOGO), size="large")
    pages = [
        st.Page(page_path(slide), title=slide.title, icon=slide.icon, default=index == 0)
        for index, slide in enumerate(SLIDES)
    ]
    st.navigation(pages, position="hidden" if presenting() else "top").run()


if __name__ == "__main__":
    render_app()
