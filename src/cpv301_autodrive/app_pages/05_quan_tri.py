"""Slide 5 — data governance as a Gate 0 timeline."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.views import render_governance_timeline, render_project_status

slide_header(__file__)
render_governance_timeline()
with st.expander("Chi tiết: bảng Gate 0, quyết định và milestone", icon=":material/table_chart:"):
    render_project_status()
slide_footer(__file__)
