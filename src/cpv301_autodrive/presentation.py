"""Slide registry and shared slide chrome for the presentation-style Streamlit app.

The app tells the project as an ordered 8-slide talk. `web_app.py` builds `st.navigation` from
`SLIDES`; every page script calls `slide_header()` first and `slide_footer()` last, which give the
"Trang k/8" label, the presentation-mode toggle and the previous/next buttons.

Presentation mode (`?present=true`) hides the top navigation and the slide progress becomes a bar;
PageUp/PageDown (what presentation clickers send) move between slides.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

PAGES_DIR = "app_pages"
PRESENT_KEY = "present"


@dataclass(frozen=True)
class Slide:
    file: str
    title: str
    icon: str
    subtitle: str


SLIDES: tuple[Slide, ...] = (
    Slide(
        "01_tong_quan.py",
        "Tổng quan",
        ":material/home:",
        "Nhận diện biển báo giao thông Việt Nam cho mô phỏng hỗ trợ lái",
    ),
    Slide(
        "02_bai_toan.py",
        "Bài toán",
        ":material/flag:",
        "Vì sao cần một model riêng cho biển báo Việt Nam",
    ),
    Slide(
        "03_pipeline.py",
        "Pipeline",
        ":material/account_tree:",
        "Từ khung hình camera đến hành vi xe mô phỏng",
    ),
    Slide(
        "04_du_lieu.py", "Dữ liệu", ":material/hub:", "DATASET01: 3.216 khung hình, 54 lớp biển báo"
    ),
    Slide(
        "05_quan_tri.py",
        "Quản trị dữ liệu",
        ":material/verified:",
        "Gate 0: chín tiêu chí trước khi được train",
    ),
    Slide(
        "06_mo_hinh.py",
        "Mô hình",
        ":material/model_training:",
        "Detector YOLO, ngưỡng nghiệm thu D-05 và tốc độ đo được",
    ),
    Slide("07_demo.py", "Demo", ":material/directions_car:", "Mô phỏng với baseline E0 (GTSRB)"),
    Slide(
        "08_buoc_tiep.py",
        "Bước tiếp theo",
        ":material/rocket_launch:",
        "Rủi ro đã biết và lộ trình M1 → M6",
    ),
)


def page_path(slide: Slide) -> str:
    return f"{PAGES_DIR}/{slide.file}"


def _index(page_file: str) -> int:
    name = Path(page_file).name
    return next(i for i, slide in enumerate(SLIDES) if slide.file == name)


def presenting() -> bool:
    """Presentation mode from the toggle state, or from the URL on first load."""
    if PRESENT_KEY in st.session_state:
        return bool(st.session_state[PRESENT_KEY])
    return str(st.query_params.get(PRESENT_KEY, "")).lower() in {"true", "1"}


def slide_header(page_file: str) -> Slide:
    index = _index(page_file)
    slide = SLIDES[index]
    with st.container(
        horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"
    ):
        st.caption(f"{slide.icon} Trang {index + 1}/{len(SLIDES)} · CPV301 AutoDrive")
        st.toggle(
            "Trình chiếu",
            key=PRESENT_KEY,
            # The default must stay False: a bound param equal to the default is dropped from the
            # URL, so value=True would erase ?present=true. The binding itself reads the URL.
            value=False,
            bind="query-params",
            help="Ẩn thanh điều hướng; dùng PageUp/PageDown hoặc nút cuối trang để chuyển slide.",
        )
    if presenting():
        st.progress((index + 1) / len(SLIDES))
    st.title(slide.title, anchor=False)
    st.subheader(f":gray[{slide.subtitle}]", anchor=False)
    st.space("small")
    return slide


def go_to(slide: Slide) -> None:
    """Switch slide and drop the previous slide's URL params.

    `st.switch_page` without `query_params` calls `QueryParams.clear()`, which raises
    `StreamlitAPIException` while a widget is bound to a URL param (`?pipeline_stage=...`,
    `?present=...`); an explicit mapping replaces them without that check. Bound params can't be
    set here either; the `present` toggle keeps its session state and re-syncs the URL.
    """
    st.switch_page(page_path(slide), query_params={})


def slide_footer(page_file: str) -> None:
    index = _index(page_file)
    st.space("medium")
    if 0 < index < len(SLIDES) - 1:
        alignment = "distribute"
    else:
        alignment = "right" if index == 0 else "left"
    with st.container(horizontal=True, horizontal_alignment=alignment):
        if index > 0:
            previous = SLIDES[index - 1]
            if st.button(
                f"Trang trước: {previous.title}",
                icon=":material/arrow_back:",
                shortcut="PageUp",
                key="slide_previous",
            ):
                go_to(previous)
        if index < len(SLIDES) - 1:
            following = SLIDES[index + 1]
            if st.button(
                f"Trang sau: {following.title}",
                icon=":material/arrow_forward:",
                icon_position="right",
                type="primary",
                shortcut="PageDown",
                key="slide_next",
            ):
                go_to(following)
