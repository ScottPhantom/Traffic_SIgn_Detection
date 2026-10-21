"""Slide 4 — DATASET01 at a glance, then the interactive explorer."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.views import render_data_overview, render_dataset01

slide_header(__file__)
render_data_overview()
st.space("small")
render_dataset01()
slide_footer(__file__)
