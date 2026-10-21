"""Slide 3 — interactive system pipeline."""

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.views import render_pipeline_explorer

slide_header(__file__)
render_pipeline_explorer()
slide_footer(__file__)
