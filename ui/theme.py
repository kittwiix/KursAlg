"""Палитры и шрифты интерфейса.

Светлая тема сделана на мягком зелёном фоне с бирюзовым акцентом, тёмная —
на глубоком графитовом. Все цвета собраны в одном месте, чтобы переключение
темы не приходилось искать по всему коду.
"""

from __future__ import annotations

from dataclasses import dataclass

FONT_UI = "Segoe UI"
FONT_MONO = "Consolas"


@dataclass(frozen=True)
class Palette:
    """Набор цветов одной темы.

    Поля названы по роли, а не по конкретному оттенку: surface — фон карточек,
    accent — активные элементы, muted — второстепенный текст. Благодаря этому
    одну и ту же разметку можно рисовать в двух темах.
    """

    name: str
    bg: str
    surface: str
    surface_alt: str
    text: str
    muted: str
    border: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    danger: str
    danger_soft: str
    warning: str
    warning_soft: str
    success: str
    success_soft: str
    tape_bg: str
    cell: str
    cell_alt: str
    head: str
    head_text: str
    shadow: str
    code_bg: str
    code_text: str
    code_comment: str
    code_state: str
    code_move: str
    code_symbol: str
    selection: str
    log_bg: str
    log_alt: str
    titlebar: str
    titlebar_text: str


LIGHT = Palette(
    name="light",
    bg="#EEF4F1",
    surface="#FFFFFF",
    surface_alt="#E4F0EB",
    text="#162420",
    muted="#5F746D",
    border="#CBDDD7",
    accent="#0E9F86",
    accent_hover="#0B8571",
    accent_pressed="#086B5B",
    accent_soft="#D6F3EA",
    danger="#C94C47",
    danger_soft="#FBE4E2",
    warning="#A96B12",
    warning_soft="#FCEFD5",
    success="#1F8F61",
    success_soft="#DDF3E8",
    tape_bg="#F3F9F7",
    cell="#FFFFFF",
    cell_alt="#F8FCFA",
    head="#0E9F86",
    head_text="#0A6A5A",
    shadow="#B7CCC5",
    code_bg="#FBFDFC",
    code_text="#22322D",
    code_comment="#7C8F89",
    code_state="#0A7B68",
    code_move="#A65A0B",
    code_symbol="#334155",
    selection="#BEEBE0",
    log_bg="#FFFFFF",
    log_alt="#F4FAF8",
    titlebar="#FFFFFF",
    titlebar_text="#162420",
)

DARK = Palette(
    name="dark",
    bg="#0D1513",
    surface="#141F1C",
    surface_alt="#1B2A26",
    text="#E7F2EE",
    muted="#93AAA2",
    border="#2A3D37",
    accent="#2DD4B5",
    accent_hover="#57E2C9",
    accent_pressed="#1FB79C",
    accent_soft="#153B33",
    danger="#FF7B72",
    danger_soft="#3B1F1E",
    warning="#E3B341",
    warning_soft="#3A2E16",
    success="#4ADE9B",
    success_soft="#163528",
    tape_bg="#101B18",
    cell="#182722",
    cell_alt="#1C2D27",
    head="#2DD4B5",
    head_text="#8FF0DD",
    shadow="#08110E",
    code_bg="#101A17",
    code_text="#D9E8E3",
    code_comment="#78908A",
    code_state="#5BE3C8",
    code_move="#F2B766",
    code_symbol="#C7D7D2",
    selection="#1E4D43",
    log_bg="#141F1C",
    log_alt="#192722",
    titlebar="#111B18",
    titlebar_text="#E7F2EE",
)

THEMES = {"light": LIGHT, "dark": DARK}


def font(size: int, weight: str = "normal", family: str = FONT_UI):
    """Возвращает кортеж шрифта для Tkinter."""
    return (family, size, weight)


def mono(size: int, weight: str = "normal"):
    """Возвращает моноширинный шрифт для редактора и листингов."""
    return (FONT_MONO, size, weight)
