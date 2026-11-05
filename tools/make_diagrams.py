"""Рисует диаграммы для пояснительной записки.

Скрипт создаёт три PNG-картинки и рядом — исходники .drawio, которые можно
открыть и поправить в draw.io. Запуск:

    python tools/make_diagrams.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "diagrams"

ACCENT = "#0E9F86"
ACCENT_SOFT = "#D6F3EA"
TEXT = "#162420"
MUTED = "#5F746D"
BORDER = "#C7DAD3"
CELL = "#FFFFFF"
CELL_ALT = "#F2F8F5"
WARNING = "#A96B12"
WARNING_SOFT = "#FCEFD5"
DANGER = "#C94C47"
DANGER_SOFT = "#FBE4E2"
BACKGROUND = "#FFFFFF"

FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"


def get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Загружает шрифт Windows, а при отсутствии — встроенный."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    """Возвращает ширину и высоту многострочного текста."""
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=8, align="center")
    return box[2] - box[0], box[3] - box[1]


def draw_center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str = TEXT,
) -> None:
    """Пишет текст по центру прямоугольника."""
    x1, y1, x2, y2 = box
    width, height = text_size(draw, text, font)
    draw.multiline_text(
        ((x1 + x2 - width) / 2, (y1 + y2 - height) / 2),
        text,
        font=font,
        fill=fill,
        spacing=8,
        align="center",
    )


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = BORDER,
    radius: int = 22,
    width: int = 3,
) -> None:
    """Рисует прямоугольник со скруглёнными углами."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = MUTED,
    width: int = 3,
    head: int = 14,
) -> None:
    """Рисует линию со стрелкой на конце."""
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        points = [
            (x2, y2),
            (x2 - direction * head, y2 - head // 2),
            (x2 - direction * head, y2 + head // 2),
        ]
    else:
        direction = 1 if y2 > y1 else -1
        points = [
            (x2, y2),
            (x2 - head // 2, y2 - direction * head),
            (x2 + head // 2, y2 - direction * head),
        ]
    draw.polygon(points, fill=color)


def diamond(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str = WARNING_SOFT,
    outline: str = WARNING,
) -> None:
    """Рисует ромб для блока условия."""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    draw.polygon([(cx, y1), (x2, cy), (cx, y2), (x1, cy)], fill=fill, outline=outline, width=4)


def wrap_for_width(text: str, font: ImageFont.FreeTypeFont, width: int) -> str:
    """Переносит текст по словам под заданную ширину в пикселях."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def make_tape_scheme() -> Image.Image:
    """Создаёт схему ленты с головкой и номерами позиций."""
    width, height = 2200, 900
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font_title = get_font(FONT_BOLD, 56)
    font_symbol = get_font(FONT_MONO, 66)
    font_small = get_font(FONT_REGULAR, 36)
    font_index = get_font(FONT_REGULAR, 30)
    font_note = get_font(FONT_BOLD, 32)

    draw.text((110, 70), "Лента и головка", font=font_title, fill=TEXT)
    draw.text(
        (110, 132),
        "Лента бесконечна в обе стороны, поэтому хранятся только непустые ячейки",
        font=font_small,
        fill=MUTED,
    )

    cell_w = 190
    cell_h = 150
    gap = 10
    count = 9
    start_x = (width - count * cell_w - (count - 1) * gap) // 2
    y1 = 300
    y2 = y1 + cell_h
    positions = list(range(-4, 5))
    symbols = ["_", "1", "1", "0", "1", "1", "1", "_", "_"]
    centers = []
    for index, (position, symbol) in enumerate(zip(positions, symbols)):
        x1 = start_x + index * (cell_w + gap)
        x2 = x1 + cell_w
        fill = CELL if index % 2 == 0 else CELL_ALT
        outline = ACCENT if position == 0 else BORDER
        thickness = 6 if position == 0 else 3
        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=16,
            fill=ACCENT_SOFT if position == 0 else fill,
            outline=outline,
            width=thickness,
        )
        color = MUTED if symbol == "_" else TEXT
        draw.text(
            ((x1 + x2) / 2, (y1 + y2) / 2),
            symbol,
            font=font_symbol,
            fill=color,
            anchor="mm",
        )
        draw.text(
            ((x1 + x2) / 2, y2 + 30),
            str(position),
            font=font_index,
            fill=MUTED,
            anchor="ma",
        )
        centers.append((x1 + x2) / 2)

    head_x = centers[4]
    draw.polygon(
        [(head_x - 18, 252), (head_x + 18, 252), (head_x, 280)],
        fill=ACCENT,
    )
    draw.text((head_x, 218), "ГОЛОВКА", font=font_note, fill=ACCENT, anchor="ms")

    arrow(draw, (180, 520), (60, 520), color=MUTED, width=3)
    arrow(draw, (width - 180, 520), (width - 60, 520), color=MUTED, width=3)
    draw.text((100, 540), "лента продолжается влево", font=font_small, fill=MUTED)
    draw.text(
        (width - 100, 540),
        "лента продолжается вправо",
        font=font_small,
        fill=MUTED,
        anchor="ra",
    )

    blank_x = centers[-1]
    arrow(draw, (blank_x, 245), (blank_x, 296), color=WARNING, width=3)
    draw.text(
        (blank_x, 220),
        "пустая ячейка обозначается _",
        font=font_small,
        fill=WARNING,
        anchor="ms",
    )
    draw.text(
        (110, 780),
        "Позиции ячеек нумеруются относительно начального положения головки",
        font=font_small,
        fill=MUTED,
    )
    return image


def make_flowchart() -> Image.Image:
    """Создаёт блок-схему работы интерпретатора."""
    width, height = 2000, 1400
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font_title = get_font(FONT_BOLD, 52)
    font_block = get_font(FONT_REGULAR, 32)
    font_small = get_font(FONT_REGULAR, 28)
    font_label = get_font(FONT_BOLD, 28)
    font_oval = get_font(FONT_BOLD, 34)

    draw.text((100, 55), "Работа интерпретатора", font=font_title, fill=TEXT)

    start = (820, 140, 1180, 220)
    rounded_box(draw, start, ACCENT_SOFT, ACCENT, radius=40, width=4)
    draw_center_text(draw, start, "Старт", font_oval, ACCENT)

    read_box = (760, 290, 1240, 400)
    rounded_box(draw, read_box, CELL, BORDER)
    draw_center_text(draw, read_box, "Прочитать пару\n(состояние q, символ a)", font_block)

    rule_diamond = (760, 470, 1240, 650)
    diamond(draw, rule_diamond)
    draw_center_text(draw, rule_diamond, "Правило для\nпары есть?", font_block, TEXT)

    apply_box = (740, 720, 1260, 860)
    rounded_box(draw, apply_box, CELL, BORDER)
    draw_center_text(
        draw,
        apply_box,
        "Записать b, сдвинуть D,\nперейти в состояние q′",
        font_block,
    )

    halt_diamond = (760, 930, 1240, 1090)
    diamond(draw, halt_diamond)
    draw_center_text(draw, halt_diamond, "q′ — состояние\nостанова?", font_block, TEXT)

    limit_diamond = (760, 1160, 1240, 1310)
    diamond(draw, limit_diamond, fill=ACCENT_SOFT, outline=ACCENT)
    draw_center_text(draw, limit_diamond, "Шагов меньше\nлимита?", font_block, TEXT)

    stop_stuck = (180, 500, 600, 620)
    rounded_box(draw, stop_stuck, DANGER_SOFT, DANGER, radius=40, width=4)
    draw_center_text(draw, stop_stuck, "Стоп:\nнет правила", font_oval, DANGER)

    stop_halt = (1450, 950, 1900, 1070)
    rounded_box(draw, stop_halt, ACCENT_SOFT, ACCENT, radius=40, width=4)
    draw_center_text(draw, stop_halt, "Стоп:\nдостигнут qz", font_oval, ACCENT)

    stop_limit = (1450, 1190, 1900, 1310)
    rounded_box(draw, stop_limit, WARNING_SOFT, WARNING, radius=40, width=4)
    draw_center_text(draw, stop_limit, "Стоп:\nлимит шагов", font_oval, WARNING)

    arrow(draw, (1000, 220), (1000, 290))
    arrow(draw, (1000, 400), (1000, 470))
    arrow(draw, (760, 560), (600, 560), color=DANGER)
    arrow(draw, (1000, 650), (1000, 720))
    arrow(draw, (1000, 860), (1000, 930))
    arrow(draw, (1240, 1010), (1450, 1010), color=ACCENT)
    arrow(draw, (1000, 1090), (1000, 1160))
    arrow(draw, (1240, 1235), (1450, 1235), color=WARNING)

    draw.line([(1000, 1310), (1000, 1350), (70, 1350), (70, 345), (760, 345)], fill=MUTED, width=3)
    draw.polygon([(760, 345), (744, 333), (744, 357)], fill=MUTED)

    draw.text((1015, 675), "да", font=font_label, fill=ACCENT)
    draw.text((620, 525), "нет", font=font_label, fill=DANGER)
    draw.text((1015, 1110), "нет", font=font_label, fill=MUTED)
    draw.text((1260, 970), "да", font=font_label, fill=ACCENT)
    draw.text((1260, 1200), "да", font=font_label, fill=WARNING)
    draw.text((620, 1320), "нет", font=font_label, fill=MUTED)

    # Подзаголовок убран: подпись рисунка в отчёте и так поясняет схему.
    return image


def class_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    lines: list[str],
    font_title: ImageFont.FreeTypeFont,
    font_line: ImageFont.FreeTypeFont,
    accent: bool = False,
) -> None:
    """Рисует прямоугольник класса с заголовком и списком полей."""
    x1, y1, x2, y2 = box
    rounded_box(draw, box, CELL, ACCENT if accent else BORDER, radius=18, width=4)
    header_height = 74
    draw.rounded_rectangle(
        (x1, y1, x2, y1 + header_height),
        radius=18,
        fill=ACCENT_SOFT if accent else "#EAF4F0",
        outline=ACCENT if accent else BORDER,
        width=3,
    )
    draw.text(
        ((x1 + x2) / 2, y1 + header_height / 2),
        title,
        font=font_title,
        fill=ACCENT if accent else TEXT,
        anchor="mm",
    )
    draw.line([(x1, y1 + header_height), (x2, y1 + header_height)], fill=BORDER, width=2)
    text_y = y1 + header_height + 20
    for line in lines:
        color = TEXT if not line.startswith("+") else MUTED
        draw.text((x1 + 24, text_y), line, font=font_line, fill=color)
        text_y += 38


def make_class_diagram() -> Image.Image:
    """Создаёт диаграмму классов ядра."""
    width, height = 2400, 1700
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font_title = get_font(FONT_BOLD, 48)
    font_block = get_font(FONT_BOLD, 40)
    font_line = get_font(FONT_MONO, 28)
    font_label = get_font(FONT_REGULAR, 28)

    draw.text((100, 55), "Классы ядра интерпретатора", font=font_title, fill=TEXT)
    draw.text(
        (100, 110),
        "Ядро не зависит от Tkinter: лента, программа и исполнитель тестируются отдельно",
        font=font_label,
        fill=MUTED,
    )

    program_box = (90, 210, 720, 620)
    class_box(
        draw,
        program_box,
        "Program",
        [
            "rules: list[Rule]",
            "initial_state: str",
            "halt_state: str",
            "+ parse(text) -> Program",
            "+ find(q, a) -> Rule | None",
            "+ is_halt_state(q) -> bool",
        ],
        font_block,
        font_line,
        accent=True,
    )
    rule_box = (830, 210, 1480, 590)
    class_box(
        draw,
        rule_box,
        "Rule",
        [
            "state: str",
            "read: str",
            "write: str",
            "move: str",
            "next_state: str",
            "line_number: int",
        ],
        font_block,
        font_line,
    )
    tape_box = (1590, 210, 2290, 620)
    class_box(
        draw,
        tape_box,
        "Tape",
        [
            "cells: dict[int, str]",
            "head: int",
            "blank: str",
            "+ read(position=None) -> str",
            "+ write(symbol, position=None)",
            "+ move(direction) -> int",
            "+ copy() -> Tape",
        ],
        font_block,
        font_line,
        accent=True,
    )

    machine_box = (300, 760, 1120, 1240)
    class_box(
        draw,
        machine_box,
        "Machine",
        [
            "program: Program",
            "tape: Tape",
            "state: str",
            "steps: int",
            "max_steps: int",
            "status: str",
            "+ step() -> TraceEntry | None",
            "+ run() -> list[TraceEntry]",
            "+ reset()",
        ],
        font_block,
        font_line,
        accent=True,
    )
    trace_box = (1260, 760, 2200, 1220)
    class_box(
        draw,
        trace_box,
        "TraceEntry",
        [
            "step: int",
            "state_before: str",
            "read_symbol: str",
            "write_symbol: str | None",
            "move: str | None",
            "state_after: str",
            "head_before / head_after: int",
            "note: str",
        ],
        font_block,
        font_line,
    )

    error_box = (760, 1350, 1300, 1490)
    class_box(
        draw,
        error_box,
        "TuringError",
        ["общая ошибка ядра"],
        font_block,
        font_line,
        accent=False,
    )
    sub1 = (220, 1540, 720, 1650)
    sub2 = (790, 1540, 1250, 1650)
    sub3 = (1320, 1540, 1880, 1650)
    for box, title in (
        (sub1, "ProgramSyntaxError"),
        (sub2, "TapeParseError"),
        (sub3, "StepLimitExceeded"),
    ):
        rounded_box(draw, box, DANGER_SOFT, DANGER, radius=18, width=3)
        draw_center_text(draw, box, title, get_font(FONT_BOLD, 30), DANGER)

    arrow(draw, (720, 400), (830, 400), color=MUTED)
    draw.text((745, 365), "1..*", font=font_label, fill=MUTED)
    arrow(draw, (1120, 900), (1260, 900), color=MUTED)
    draw.text((1160, 865), "пишет", font=font_label, fill=MUTED)
    arrow(draw, (410, 760), (410, 620), color=MUTED)
    draw.text((430, 670), "использует", font=font_label, fill=MUTED)
    draw.line([(1050, 760), (1050, 700), (1950, 700)], fill=MUTED, width=3)
    arrow(draw, (1950, 700), (1950, 620), color=MUTED)
    draw.text((1560, 665), "использует", font=font_label, fill=MUTED)
    bus_y = 1515
    draw.line([(1030, 1490), (1030, bus_y)], fill=DANGER, width=3)
    draw.line([(470, bus_y), (1600, bus_y)], fill=DANGER, width=3)
    for box in (sub1, sub2, sub3):
        cx = (box[0] + box[2]) // 2
        draw.line([(cx, bus_y), (cx, box[1])], fill=DANGER, width=3)
    return image


def save_drawio_tape(path: Path) -> None:
    """Сохраняет упрощённый исходник схемы ленты для draw.io."""
    cells = []
    for index, position in enumerate(range(-4, 5)):
        x = 120 + index * 130
        symbol = "1" if position in (-3, -2, 0, 1, 2) else ("0" if position == -1 else "_")
        style = (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#F2F8F5;"
            "strokeColor=#C7DAD3;fontSize=22;fontFamily=Consolas;"
        )
        if position == 0:
            style = (
                "rounded=1;whiteSpace=wrap;html=1;fillColor=#D6F3EA;"
                "strokeColor=#0E9F86;strokeWidth=3;fontSize=22;"
                "fontFamily=Consolas;"
            )
        cells.append(
            f'<mxCell id="cell{index}" value="{escape(symbol)}" '
            f'style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="180" width="110" height="80" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="app.diagrams.net"><diagram name="Лента">'
        '<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="700">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
        + "".join(cells)
        + '<mxCell id="head" value="Головка" '
        'style="text;html=1;fontSize=14;fontColor=#0E9F86;fontStyle=1;" '
        'vertex="1" parent="1">'
        '<mxGeometry x="615" y="110" width="100" height="30" as="geometry"/></mxCell>'
        '<mxCell id="note" value="Лента бесконечна в обе стороны. Пустая ячейка обозначается _" '
        'style="text;html=1;fontSize=14;fontColor=#5F746D;" vertex="1" parent="1">'
        '<mxGeometry x="120" y="330" width="700" height="30" as="geometry"/></mxCell>'
        "</root></mxGraphModel></diagram></mxfile>"
    )
    path.write_text(xml, encoding="utf-8")


def save_drawio_flowchart(path: Path) -> None:
    """Сохраняет упрощённый исходник блок-схемы для draw.io."""
    vertices = [
        (
            "start", "Старт",
            "ellipse;whiteSpace=wrap;html=1;fillColor=#D6F3EA;"
            "strokeColor=#0E9F86;fontStyle=1;",
            430, 40, 180, 60,
        ),
        (
            "read", "Прочитать пару (q, a)",
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
            "strokeColor=#C7DAD3;",
            390, 140, 260, 60,
        ),
        (
            "rule", "Правило есть?",
            "rhombus;whiteSpace=wrap;html=1;fillColor=#FCEFD5;"
            "strokeColor=#A96B12;",
            400, 240, 240, 100,
        ),
        (
            "apply", "Записать b, сдвинуть D, q := q′",
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
            "strokeColor=#C7DAD3;",
            370, 380, 300, 70,
        ),
        (
            "halt", "q′ — останов?",
            "rhombus;whiteSpace=wrap;html=1;fillColor=#FCEFD5;"
            "strokeColor=#A96B12;",
            400, 490, 240, 100,
        ),
        (
            "limit", "Шагов меньше лимита?",
            "rhombus;whiteSpace=wrap;html=1;fillColor=#D6F3EA;"
            "strokeColor=#0E9F86;",
            390, 630, 260, 100,
        ),
        (
            "stop_stuck", "Стоп: нет правила",
            "ellipse;whiteSpace=wrap;html=1;fillColor=#FBE4E2;"
            "strokeColor=#C94C47;",
            80, 250, 190, 80,
        ),
        (
            "stop_halt", "Стоп: достигнут qz",
            "ellipse;whiteSpace=wrap;html=1;fillColor=#D6F3EA;"
            "strokeColor=#0E9F86;",
            760, 500, 190, 80,
        ),
        (
            "stop_limit", "Стоп: лимит шагов",
            "ellipse;whiteSpace=wrap;html=1;fillColor=#FCEFD5;"
            "strokeColor=#A96B12;",
            760, 640, 190, 80,
        ),
    ]
    edges = [
        ("start", "read", "да"),
        ("read", "rule", ""),
        ("rule", "stop_stuck", "нет"),
        ("rule", "apply", "да"),
        ("apply", "halt", ""),
        ("halt", "stop_halt", "да"),
        ("halt", "limit", "нет"),
        ("limit", "stop_limit", "да"),
        ("limit", "read", "нет"),
    ]
    body = []
    for cell_id, value, style, x, y, w, h in vertices:
        body.append(
            f'<mxCell id="{cell_id}" value="{escape(value)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
    for index, (source, target, label) in enumerate(edges):
        body.append(
            f'<mxCell id="edge{index}" value="{escape(label)}" '
            'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;'
            'endArrow=block;strokeColor=#5F746D;" '
            f'edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="app.diagrams.net"><diagram name="Блок-схема">'
        '<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="800">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
        + "".join(body)
        + "</root></mxGraphModel></diagram></mxfile>"
    )
    path.write_text(xml, encoding="utf-8")


def save_drawio_classes(path: Path) -> None:
    """Сохраняет упрощённый исходник диаграммы классов для draw.io."""
    boxes = [
        (
            "Program",
            "Program<br>rules: list[Rule]<br>initial_state: str<br>halt_state: str<br>"
            "parse(), find(), is_halt_state()",
            60, 80, 260, 190,
        ),
        (
            "Rule",
            "Rule<br>state, read, write<br>move, next_state<br>line_number",
            360, 80, 250, 170,
        ),
        (
            "Tape",
            "Tape<br>cells: dict[int, str]<br>head: int<br>"
            "read(), write(), move(), copy()",
            660, 80, 280, 190,
        ),
        (
            "Machine",
            "Machine<br>program, tape, state<br>steps, max_steps, status<br>"
            "step(), run(), reset()",
            150, 340, 290, 180,
        ),
        (
            "TraceEntry",
            "TraceEntry<br>step, state_before<br>read_symbol, write_symbol<br>"
            "move, state_after, note",
            520, 340, 290, 180,
        ),
        ("TuringError", "TuringError", 350, 600, 180, 50),
        ("ProgramSyntaxError", "ProgramSyntaxError", 60, 700, 180, 50),
        ("TapeParseError", "TapeParseError", 270, 700, 160, 50),
        ("StepLimitExceeded", "StepLimitExceeded", 460, 700, 180, 50),
    ]
    body = []
    for cell_id, value, x, y, w, h in boxes:
        style = (
            "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
            "strokeColor=#0E9F86;align=left;verticalAlign=top;spacing=8;"
        )
        if cell_id == "TuringError":
            style = (
                "rounded=0;whiteSpace=wrap;html=1;fillColor=#EAF4F0;"
                "strokeColor=#0E9F86;align=center;verticalAlign=middle;"
            )
        elif "Error" in cell_id:
            style = (
                "rounded=0;whiteSpace=wrap;html=1;fillColor=#FBE4E2;"
                "strokeColor=#C94C47;align=center;verticalAlign=middle;"
            )
        body.append(
            f'<mxCell id="{cell_id}" value="{escape(value)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
    edges = [
        ("Program", "Rule", "1..*"),
        ("Machine", "Program", "использует"),
        ("Machine", "Tape", "использует"),
        ("Machine", "TraceEntry", "пишет"),
        ("TuringError", "ProgramSyntaxError", ""),
        ("TuringError", "TapeParseError", ""),
        ("TuringError", "StepLimitExceeded", ""),
    ]
    for index, (source, target, label) in enumerate(edges):
        body.append(
            f'<mxCell id="e{index}" value="{escape(label)}" '
            'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;'
            'endArrow=block;strokeColor=#5F746D;" '
            f'edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="app.diagrams.net"><diagram name="Классы">'
        '<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="800">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
        + "".join(body)
        + "</root></mxGraphModel></diagram></mxfile>"
    )
    path.write_text(xml, encoding="utf-8")


def trim_image(image: Image.Image, padding: int = 36) -> Image.Image:
    """Обрезает белые поля вокруг рисунка."""
    background = Image.new("RGB", image.size, "#FFFFFF")
    difference = ImageChops.difference(image, background)
    box = difference.getbbox()
    if box is None:
        return image
    left = max(box[0] - padding, 0)
    top = max(box[1] - padding, 0)
    right = min(box[2] + padding, image.width)
    bottom = min(box[3] + padding, image.height)
    return image.crop((left, top, right, bottom))


def main() -> None:
    """Создаёт все диаграммы и исходники."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    diagrams = {
        "tape_scheme.png": make_tape_scheme(),
        "flowchart.png": make_flowchart(),
        "class_diagram.png": make_class_diagram(),
    }
    for name, image in diagrams.items():
        path = OUTPUT / name
        trim_image(image).save(path)
        print(f"сохранён {path}")
    save_drawio_tape(OUTPUT / "tape_scheme.drawio")
    save_drawio_flowchart(OUTPUT / "flowchart.drawio")
    save_drawio_classes(OUTPUT / "class_diagram.drawio")
    print("исходники draw.io сохранены")


if __name__ == "__main__":
    main()
