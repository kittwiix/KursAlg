"""Главное окно интерпретатора машины Тьюринга.

Здесь соединяются ядро и интерфейс: пользователь редактирует программу,
задаёт начальную ленту, выполняет шаги и видит журнал. Вся логика машины
остаётся в пакете turing, а этот модуль только показывает её состояние.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from turing.errors import ProgramSyntaxError, TapeParseError
from turing.examples import example_titles, get_example
from turing.machine import (
    STATUS_HALTED,
    STATUS_LIMIT,
    STATUS_STUCK,
    Machine,
)
from turing.program import Program
from turing.tape import Tape

from .chrome import CustomWindow
from .editor import ProgramEditor
from .tape_view import TapeView
from .theme import DARK, LIGHT, Palette, font, mono
from .widgets import Dropdown, RoundedButton, SpeedSlider, StatusChip, style_entry


class TuringApp(CustomWindow):
    """Окно программы и обработчики действий пользователя.

    Класс хранит текущую машину, запускает таймер автоматического выполнения
    и обновляет ленту, индикаторы и журнал. При изменении программы или
    начальной ленты машина пересобирается автоматически.
    """

    def __init__(self) -> None:
        """Создаёт окно, строит интерфейс и загружает первый пример."""
        self.palette = LIGHT
        super().__init__(
            "Машина Тьюринга",
            "пошаговый интерпретатор и визуализация ленты",
            LIGHT,
        )
        self.machine: Machine | None = None
        self.program: Program | None = None
        self.running = False
        self._after_job = None
        self._machine_signature: tuple[str, str, int] | None = None
        self._theme_name = "light"
        self.theme_callback = self.toggle_theme
        self._build_ui()
        self._configure_ttk()
        self._bind_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.load_example("addition")
        self.after(120, self.editor.text.focus_set)

    def _build_ui(self) -> None:
        """Создаёт все панели главного окна."""
        p = self.palette
        self.content.configure(bg=p.bg)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(4, weight=1)

        self._build_topbar()
        self._build_description()
        self._build_tape_card()
        self._build_indicators()
        self._build_main_area()
        self._build_controls()
        self._build_statusbar()

    def _build_topbar(self) -> None:
        """Создаёт строку с примерами, файлами и лимитом шагов."""
        p = self.palette
        self.topbar = tk.Frame(self.content, bg=p.bg)
        self.topbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 8))
        self.topbar.grid_columnconfigure(4, weight=1)

        self.example_label = tk.Label(
            self.topbar,
            text="Пример",
            bg=p.bg,
            fg=p.muted,
            font=font(8),
        )
        self.example_label.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.example_dropdown = Dropdown(
            self.topbar,
            p,
            example_titles(),
            self.load_example,
            width=300,
        )
        self.example_dropdown.grid(row=0, column=1, sticky="w", padx=(0, 10))

        self.open_button = RoundedButton(
            self.topbar,
            "Открыть",
            self._open_file,
            p,
            kind="ghost",
            width=104,
            height=36,
            background=p.bg,
            icon="⌂",
        )
        self.open_button.grid(row=0, column=2, padx=(0, 8))

        self.save_button = RoundedButton(
            self.topbar,
            "Сохранить",
            self._save_file,
            p,
            kind="ghost",
            width=114,
            height=36,
            background=p.bg,
            icon="↓",
        )
        self.save_button.grid(row=0, column=3, padx=(0, 8))

        self.limit_label = tk.Label(
            self.topbar,
            text="Лимит шагов",
            bg=p.bg,
            fg=p.muted,
            font=font(8),
        )
        self.limit_label.grid(row=0, column=5, padx=(8, 6))

        self.limit_var = tk.StringVar(value="1000")
        self.limit_entry = tk.Entry(
            self.topbar,
            textvariable=self.limit_var,
            width=8,
            justify="center",
        )
        style_entry(self.limit_entry, p)
        self.limit_entry.grid(row=0, column=6, ipady=6)

        self.limit_suffix = tk.Label(
            self.topbar,
            text="шагов",
            bg=p.bg,
            fg=p.muted,
            font=font(8),
        )
        self.limit_suffix.grid(row=0, column=7, padx=(6, 0))

    def _build_description(self) -> None:
        """Создаёт полосу с описанием выбранного примера."""
        p = self.palette
        self.desc_card = tk.Frame(self.content, bg=p.surface_alt)
        self.desc_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.desc_bar = tk.Frame(self.desc_card, bg=p.accent, width=4)
        self.desc_bar.pack(side="left", fill="y")
        self.desc_label = tk.Label(
            self.desc_card,
            text="",
            bg=p.surface_alt,
            fg=p.text,
            font=font(9),
            anchor="w",
            justify="left",
        )
        self.desc_label.pack(side="left", fill="x", expand=True, padx=12, pady=8)
        self.desc_card.bind("<Configure>", self._resize_description)

    def _resize_description(self, event: tk.Event) -> None:
        """Подстраивает перенос строк под ширину окна."""
        self.desc_label.configure(wraplength=max(event.width - 70, 360))

    def _build_tape_card(self) -> None:
        """Создаёт карточку ленты с заголовком и легендой."""
        p = self.palette
        self.tape_card = tk.Frame(
            self.content,
            bg=p.surface,
            highlightbackground=p.border,
            highlightthickness=1,
        )
        self.tape_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.tape_header = tk.Frame(self.tape_card, bg=p.surface)
        self.tape_header.pack(side="top", fill="x", padx=16, pady=(9, 0))
        self.tape_title = tk.Label(
            self.tape_header,
            text="Лента",
            bg=p.surface,
            fg=p.text,
            font=font(10, "bold"),
        )
        self.tape_title.pack(side="left")
        self.tape_legend = tk.Label(
            self.tape_header,
            text="головка — рамка   ·   пустая ячейка — _",
            bg=p.surface,
            fg=p.muted,
            font=font(8),
        )
        self.tape_legend.pack(side="left", padx=(14, 0))
        self.head_label = tk.Label(
            self.tape_header,
            text="позиция головки: 0",
            bg=p.surface,
            fg=p.muted,
            font=font(8),
        )
        self.head_label.pack(side="right")
        self.tape_view = TapeView(self.tape_card, p)
        self.tape_view.pack(fill="both", expand=True, padx=10, pady=(2, 6))

    def _build_indicators(self) -> None:
        """Создаёт четыре плашки с текущими показателями."""
        p = self.palette
        self.chips_frame = tk.Frame(self.content, bg=p.bg)
        self.chips_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        for column in range(4):
            self.chips_frame.grid_columnconfigure(column, weight=1)
        self.state_chip = StatusChip(self.chips_frame, "Состояние", "q0", p, accent=True)
        self.symbol_chip = StatusChip(self.chips_frame, "Под головкой", "_", p)
        self.step_chip = StatusChip(self.chips_frame, "Шаг", "0", p)
        self.status_chip = StatusChip(self.chips_frame, "Статус", "Готово", p)
        chips = [self.state_chip, self.symbol_chip, self.step_chip, self.status_chip]
        for index, chip in enumerate(chips):
            chip.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=(0 if index == 0 else 8, 0),
            )

    def _build_main_area(self) -> None:
        """Создаёт редактор программы и журнал выполнения."""
        p = self.palette
        self.main = tk.Frame(self.content, bg=p.bg)
        self.main.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=3)
        self.main.grid_columnconfigure(1, weight=2)

        self.editor_card = tk.Frame(
            self.main,
            bg=p.surface,
            highlightbackground=p.border,
            highlightthickness=1,
        )
        self.editor_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.editor = ProgramEditor(self.editor_card, p, self._validate_live)
        self.editor.pack(fill="both", expand=True)

        self.log_card = tk.Frame(
            self.main,
            bg=p.surface,
            highlightbackground=p.border,
            highlightthickness=1,
        )
        self.log_card.grid(row=0, column=1, sticky="nsew")
        self.log_header = tk.Frame(self.log_card, bg=p.surface)
        self.log_header.pack(side="top", fill="x", padx=14, pady=(10, 6))
        self.log_title = tk.Label(
            self.log_header,
            text="Журнал выполнения",
            bg=p.surface,
            fg=p.text,
            font=font(10, "bold"),
        )
        self.log_title.pack(side="left")
        self.clear_log_button = RoundedButton(
            self.log_header,
            "Очистить",
            self._clear_log,
            p,
            kind="soft",
            width=86,
            height=26,
            background=p.surface,
            font_size=8,
        )
        self.clear_log_button.pack(side="right")

        self.log_body = tk.Frame(self.log_card, bg=p.log_bg)
        self.log_body.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        columns = ("step", "state", "read", "write", "move", "next", "note")
        self.log = ttk.Treeview(
            self.log_body,
            columns=columns,
            show="headings",
            style="Log.Treeview",
            height=8,
        )
        headings = {
            "step": "Шаг",
            "state": "Было",
            "read": "Прочитано",
            "write": "Записано",
            "move": "Сдвиг",
            "next": "Стало",
            "note": "Примечание",
        }
        widths = {
            "step": 44,
            "state": 70,
            "read": 76,
            "write": 76,
            "move": 70,
            "next": 96,
            "note": 92,
        }
        for column in columns:
            self.log.heading(column, text=headings[column])
            self.log.column(
                column,
                width=widths[column],
                minwidth=40,
                anchor="center" if column in ("step", "read", "write", "move") else "w",
                stretch=True,
            )
        self.log_scroll = ttk.Scrollbar(
            self.log_body,
            orient="vertical",
            command=self.log.yview,
            style="Vertical.TScrollbar",
        )
        self.log_separator = tk.Frame(self.log_body, bg=p.log_bg, width=1)
        self.log.configure(yscrollcommand=self.log_scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        self.log_separator.pack(side="right", fill="y", padx=(1, 0))
        self.log_scroll.pack(side="right", fill="y")

    def _build_controls(self) -> None:
        """Создаёт поле начальной ленты, скорость и кнопки выполнения."""
        p = self.palette
        self.controls = tk.Frame(
            self.content,
            bg=p.surface,
            highlightbackground=p.border,
            highlightthickness=1,
        )
        self.controls.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.controls.grid_columnconfigure(1, weight=1)

        self.controls_left = tk.Frame(self.controls, bg=p.surface)
        self.controls_left.grid(row=0, column=0, sticky="w", padx=(14, 12), pady=10)
        self.tape_label = tk.Label(
            self.controls_left,
            text="Начальная лента",
            bg=p.surface,
            fg=p.muted,
            font=font(8),
        )
        self.tape_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.tape_var = tk.StringVar(value="|111011")
        self.tape_entry = tk.Entry(
            self.controls_left,
            textvariable=self.tape_var,
            width=24,
        )
        style_entry(self.tape_entry, p, use_mono=True)
        self.tape_entry.grid(row=1, column=0, ipady=6, sticky="w")
        self.apply_button = RoundedButton(
            self.controls_left,
            "Применить",
            self._apply_tape,
            p,
            kind="soft",
            width=100,
            height=34,
            background=p.surface,
            font_size=9,
        )
        self.apply_button.grid(row=1, column=1, padx=(8, 0))

        self.controls_center = tk.Frame(self.controls, bg=p.surface)
        self.controls_center.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=10)
        self.speed_title = tk.Label(
            self.controls_center,
            text="Скорость",
            bg=p.surface,
            fg=p.muted,
            font=font(8),
        )
        self.speed_title.grid(row=0, column=0, sticky="w")
        self.speed_label = tk.Label(
            self.controls_center,
            text="337 мс",
            bg=p.surface,
            fg=p.muted,
            font=font(8),
        )
        self.speed_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.speed_slider = SpeedSlider(
            self.controls_center,
            p,
            self._on_speed_change,
            width=220,
        )
        self.speed_slider.grid(row=1, column=0, columnspan=2, sticky="w")

        self.controls_right = tk.Frame(self.controls, bg=p.surface)
        self.controls_right.grid(row=0, column=2, sticky="e", padx=(0, 14), pady=10)
        self.reset_button = RoundedButton(
            self.controls_right,
            "Сброс",
            self._reset_machine,
            p,
            kind="ghost",
            width=92,
            height=38,
            background=p.surface,
        )
        self.reset_button.pack(side="left", padx=(0, 8))
        self.step_button = RoundedButton(
            self.controls_right,
            "Шаг",
            self.step_once,
            p,
            kind="soft",
            width=92,
            height=38,
            background=p.surface,
        )
        self.step_button.pack(side="left", padx=(0, 8))
        self.run_button = RoundedButton(
            self.controls_right,
            "Запустить",
            self.toggle_run,
            p,
            kind="primary",
            width=132,
            height=38,
            background=p.surface,
        )
        self.run_button.pack(side="left")

    def _build_statusbar(self) -> None:
        """Создаёт нижнюю строку с подсказкой и сообщением."""
        p = self.palette
        self.statusbar = tk.Frame(self.content, bg=p.surface_alt, height=30)
        self.statusbar.grid(row=6, column=0, sticky="ew")
        self.statusbar.pack_propagate(False)
        self.hint_label = tk.Label(
            self.statusbar,
            text=(
                "F5 — пуск/пауза   F6 — шаг   F7 — сброс   "
                "Ctrl+O — открыть   Ctrl+S — сохранить"
            ),
            bg=p.surface_alt,
            fg=p.muted,
            font=font(8),
        )
        self.hint_label.pack(side="left", padx=20)
        self.status_message = tk.Label(
            self.statusbar,
            text="Готово",
            bg=p.surface_alt,
            fg=p.text,
            font=font(8, "bold"),
        )
        self.status_message.pack(side="right", padx=(0, 20))
        self.status_dot = tk.Canvas(
            self.statusbar,
            width=10,
            height=10,
            bg=p.surface_alt,
            highlightthickness=0,
        )
        self.status_dot.pack(side="right", padx=(0, 6))
        self._draw_status_dot(p.muted)

    def _draw_status_dot(self, color: str) -> None:
        """Рисует цветной индикатор рядом с сообщением."""
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 8, 8, fill=color, outline="")

    def _configure_ttk(self) -> None:
        """Настраивает Treeview и полосы прокрутки под текущую палитру."""
        p = self.palette
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Log.Treeview",
            background=p.log_bg,
            fieldbackground=p.log_bg,
            foreground=p.text,
            font=font(8),
            rowheight=25,
            borderwidth=0,
        )
        style.configure(
            "Log.Treeview.Heading",
            background=p.surface_alt,
            foreground=p.muted,
            font=font(8, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Log.Treeview",
            background=[("selected", p.accent_soft)],
            foreground=[("selected", p.text)],
        )
        style.layout(
            "Vertical.TScrollbar",
            [
                (
                    "Vertical.Scrollbar.trough",
                    {
                        "sticky": "ns",
                        "children": [
                            (
                                "Vertical.Scrollbar.thumb",
                                {"expand": "1", "sticky": "nswe"},
                            )
                        ],
                    },
                )
            ],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=p.border,
            troughcolor=p.surface_alt,
            bordercolor=p.surface_alt,
            borderwidth=0,
            relief="flat",
            arrowcolor=p.muted,
            lightcolor=p.border,
            darkcolor=p.border,
            width=10,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", p.border), ("pressed", p.accent_soft)],
            arrowcolor=[("active", p.text)],
        )
        self.log.tag_configure("odd", background=p.log_alt)
        self.log.tag_configure("stop", foreground=p.danger)
        self.log.tag_configure("halt", foreground=p.success)
        self.log.tag_configure("limit", foreground=p.warning)

    def _bind_hotkeys(self) -> None:
        """Назначает горячие клавиши."""
        self.bind("<F5>", lambda _event: self.toggle_run())
        self.bind("<F6>", lambda _event: self.step_once())
        self.bind("<F7>", lambda _event: self._reset_machine())
        self.bind("<Control-o>", lambda _event: self._open_file())
        self.bind("<Control-s>", lambda _event: self._save_file())

    def load_example(self, key: str) -> None:
        """Загружает пример программы и его начальную ленту."""
        self._stop_run()
        example = get_example(key)
        self.example_dropdown.set_value(key)
        self.editor.set_text(example.program_text)
        self.tape_var.set(example.tape_text)
        self.limit_var.set(str(example.suggested_limit))
        self.desc_label.configure(text=example.description)
        self._reset_machine()
        self._set_status(f"Загружен пример «{example.title}».", "info")

    def _validate_live(self, text: str) -> None:
        """Проверяет синтаксис по мере набора текста."""
        if not text.strip():
            self.editor.set_status("пустая программа", "error")
            return
        try:
            program = Program.parse(text)
        except ProgramSyntaxError as error:
            self.editor.mark_error(error.line_number)
            self.editor.set_status(f"ошибка в строке {error.line_number}", "error")
        else:
            self.editor.clear_error()
            self.editor.set_status(f"{program.rule_count} правил", "ok")

    def _parse_program(self) -> Program | None:
        """Разбирает программу и показывает ошибку с номером строки."""
        try:
            program = Program.parse(self.editor.get_text())
        except ProgramSyntaxError as error:
            self.editor.mark_error(error.line_number)
            self.editor.set_status(str(error), "error")
            self._set_status(str(error), "error")
            return None
        self.editor.clear_error()
        self.editor.set_status(
            f"{program.rule_count} правил · {len(program.states())} состояний",
            "ok",
        )
        return program

    def _read_limit(self) -> int:
        """Читает лимит шагов и проверяет, что это положительное число."""
        raw = self.limit_var.get().strip()
        try:
            value = int(raw)
        except ValueError:
            value = 1000
        if value < 1 or value > 1_000_000:
            value = 1000
            self._set_status(
                "Лимит шагов должен быть от 1 до 1 000 000. Установлено 1000.",
                "warning",
            )
        self.limit_var.set(str(value))
        return value

    def _build_machine(self) -> bool:
        """Создаёт новую машину из текущей программы и ленты."""
        program = self._parse_program()
        if program is None:
            return False
        try:
            tape = Tape.from_text(self.tape_var.get())
        except TapeParseError as error:
            self.editor.set_status("проверьте начальную ленту", "error")
            self._set_status(str(error), "error")
            return False
        limit = self._read_limit()
        self.program = program
        self.machine = Machine(program, tape, limit)
        self._machine_signature = (self.editor.get_text(), self.tape_var.get(), limit)
        self.tape_view.set_tape(self.machine.tape)
        self._clear_log()
        self._update_indicators()
        self.editor.clear_active_line()
        rule = self.machine.next_rule()
        if rule is not None:
            self.editor.highlight_line(rule.line_number)
        return True

    def _ensure_machine(self) -> bool:
        """Пересобирает машину, если программа или лента изменились."""
        signature = (
            self.editor.get_text(),
            self.tape_var.get(),
            self._read_limit(),
        )
        if self.machine is None or signature != self._machine_signature:
            return self._build_machine()
        return True

    def _reset_machine(self) -> None:
        """Возвращает машину к началу и очищает журнал."""
        self._stop_run()
        if not self._build_machine():
            return
        self.run_button.set_text("Запустить")
        self._set_status("Готово. Нажмите «Шаг» или «Запустить».", "info")

    def _apply_tape(self) -> None:
        """Применяет новую начальную ленту и сбрасывает машину."""
        self._reset_machine()

    def step_once(self) -> None:
        """Выполняет один шаг по кнопке или горячей клавише."""
        if self.running:
            self._stop_run()
        self._do_step()

    def _do_step(self) -> bool:
        """Выполняет шаг и обновляет все элементы окна."""
        if not self._ensure_machine():
            return False
        if self.machine is None:
            return False
        if self.machine.is_finished:
            self._set_status(
                "Машина остановлена. Нажмите «Сброс», чтобы начать заново.",
                "warning",
            )
            return False

        rule = self.machine.next_rule()
        if rule is not None:
            self.editor.highlight_line(rule.line_number)

        entry = self.machine.step()
        if entry is not None:
            self.tape_view.animate_step(entry)
            self._append_log(entry)
        elif self.machine.status == STATUS_STUCK and self.machine.history:
            self._append_log(self.machine.history[-1])

        self._update_indicators()
        if self.machine.is_finished:
            self._stop_run()
            if self.machine.status == STATUS_HALTED:
                self._set_status(self.machine.stop_message, "success")
            elif self.machine.status == STATUS_LIMIT:
                self._set_status(self.machine.stop_message, "warning")
            elif self.machine.status == STATUS_STUCK:
                self._set_status(self.machine.stop_message, "warning")
            return False
        next_rule = self.machine.next_rule()
        if next_rule is not None:
            self.editor.highlight_line(next_rule.line_number)
        return True

    def toggle_run(self) -> None:
        """Запускает автоматическое выполнение или ставит его на паузу."""
        if self.running:
            self._stop_run()
            self.run_button.set_text("Продолжить")
            self._set_status("Пауза. Нажмите «Продолжить» или F5.", "info")
            return
        if not self._ensure_machine():
            return
        if self.machine is not None and self.machine.is_finished:
            self._reset_machine()
            if not self._ensure_machine():
                return
        self.running = True
        self.run_button.set_text("Пауза")
        self._set_status("Выполняется...", "success")
        self._tick()

    def _tick(self) -> None:
        """Выполняет шаг и планирует следующий по таймеру."""
        if not self.running:
            return
        if self.machine is None or self.machine.is_finished:
            self._stop_run()
            return
        self._do_step()
        if self.running and self.machine is not None and not self.machine.is_finished:
            delay = max(self.speed_slider.delay_ms, 40)
            self._after_job = self.after(delay, self._tick)

    def _stop_run(self) -> None:
        """Останавливает таймер автоматического выполнения."""
        self.running = False
        if self._after_job is not None:
            try:
                self.after_cancel(self._after_job)
            except tk.TclError:
                pass
            self._after_job = None
        if hasattr(self, "run_button"):
            self.run_button.set_text("Запустить")

    def _on_speed_change(self, _value: int) -> None:
        """Обновляет подпись с задержкой между шагами."""
        self.speed_label.configure(text=f"{self.speed_slider.delay_ms} мс")

    def _append_log(self, entry) -> None:
        """Добавляет строку в журнал и прокручивает его вниз."""
        if entry.is_stop_row:
            values = (
                "—",
                entry.state_before,
                entry.read_symbol,
                "—",
                "—",
                "—",
                entry.note,
            )
        else:
            values = (
                entry.step,
                entry.state_before,
                entry.read_symbol,
                entry.write_symbol,
                entry.move_text,
                entry.state_after,
                entry.note or "—",
            )
        tag = "odd" if len(self.log.get_children()) % 2 else ""
        tags = (tag,) if tag else ()
        if entry.is_stop_row:
            tags = tags + ("stop",)
        elif entry.note == "останов":
            tags = tags + ("halt",)
        elif entry.note == "лимит шагов":
            tags = tags + ("limit",)
        self.log.insert("", "end", values=values, tags=tags)
        children = self.log.get_children()
        if children:
            self.log.see(children[-1])

    def _clear_log(self) -> None:
        """Удаляет все строки журнала."""
        if hasattr(self, "log"):
            for item in self.log.get_children():
                self.log.delete(item)

    def _update_indicators(self) -> None:
        """Обновляет плашки состояния, символа, шага и статуса."""
        if self.machine is None:
            self.state_chip.set_value("—", accent=False)
            self.symbol_chip.set_value("—")
            self.step_chip.set_value("0")
            self.status_chip.set_value("Нет машины", accent=False)
            self.head_label.configure(text="позиция головки: —")
            return
        symbol = self.machine.current_symbol
        self.state_chip.set_value(self.machine.state, accent=True)
        self.symbol_chip.set_value("пусто" if symbol == "_" else symbol)
        self.step_chip.set_value(str(self.machine.steps))
        self.status_chip.set_value(
            self.machine.status_text,
            accent=not self.machine.is_finished,
        )
        self.head_label.configure(text=f"позиция головки: {self.machine.tape.head}")

    def _set_status(self, text: str, kind: str = "info") -> None:
        """Показывает сообщение в нижней строке."""
        colors = {
            "info": self.palette.text,
            "success": self.palette.success,
            "warning": self.palette.warning,
            "error": self.palette.danger,
        }
        dot_colors = {
            "info": self.palette.muted,
            "success": self.palette.success,
            "warning": self.palette.warning,
            "error": self.palette.danger,
        }
        self.status_message.configure(
            text=text,
            fg=colors.get(kind, self.palette.text),
        )
        self._draw_status_dot(dot_colors.get(kind, self.palette.muted))

    def _open_file(self) -> None:
        """Открывает текст программы из файла."""
        path = filedialog.askopenfilename(
            title="Открыть программу",
            filetypes=[("Текст программы", "*.txt"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            text = open(path, "r", encoding="utf-8").read()
        except OSError as error:
            messagebox.showerror("Не удалось открыть файл", str(error))
            return
        self._stop_run()
        self.editor.set_text(text)
        self._validate_live(text)
        self._build_machine()
        self._set_status(f"Открыт файл: {path}", "info")

    def _save_file(self) -> None:
        """Сохраняет текст программы в файл."""
        path = filedialog.asksaveasfilename(
            title="Сохранить программу",
            defaultextension=".txt",
            initialfile="program.txt",
            filetypes=[("Текст программы", "*.txt"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.editor.get_text())
        except OSError as error:
            messagebox.showerror("Не удалось сохранить файл", str(error))
            return
        self._set_status(f"Программа сохранена: {path}", "success")

    def toggle_theme(self) -> None:
        """Переключает светлую и тёмную темы."""
        if self._theme_name == "light":
            self._theme_name = "dark"
            self.palette = DARK
            self.set_theme_symbol("☀")
        else:
            self._theme_name = "light"
            self.palette = LIGHT
            self.set_theme_symbol("☾")
        self.apply_theme(self.palette)

    def apply_theme(self, palette: Palette) -> None:
        """Применяет палитру ко всем элементам окна."""
        self.palette = palette
        super().apply_theme(palette)
        self.content.configure(bg=palette.bg)
        self.topbar.configure(bg=palette.bg)
        self.example_label.configure(bg=palette.bg, fg=palette.muted)
        self.limit_label.configure(bg=palette.bg, fg=palette.muted)
        self.limit_suffix.configure(bg=palette.bg, fg=palette.muted)
        style_entry(self.limit_entry, palette)
        self.limit_entry.configure(bg=palette.code_bg)

        self.desc_card.configure(bg=palette.surface_alt)
        self.desc_bar.configure(bg=palette.accent)
        self.desc_label.configure(bg=palette.surface_alt, fg=palette.text)

        self.tape_card.configure(
            bg=palette.surface,
            highlightbackground=palette.border,
        )
        self.tape_header.configure(bg=palette.surface)
        for widget in (self.tape_title, self.tape_legend, self.head_label):
            widget.configure(bg=palette.surface)
        self.tape_title.configure(fg=palette.text)
        self.tape_legend.configure(fg=palette.muted)
        self.head_label.configure(fg=palette.muted)

        self.chips_frame.configure(bg=palette.bg)
        self.main.configure(bg=palette.bg)
        self.editor_card.configure(
            bg=palette.surface,
            highlightbackground=palette.border,
        )
        self.log_card.configure(
            bg=palette.surface,
            highlightbackground=palette.border,
        )
        self.log_header.configure(bg=palette.surface)
        self.log_body.configure(bg=palette.log_bg)
        self.log_separator.configure(bg=palette.log_bg)
        self.log_title.configure(bg=palette.surface, fg=palette.text)

        self.controls.configure(
            bg=palette.surface,
            highlightbackground=palette.border,
        )
        self.controls_left.configure(bg=palette.surface)
        self.controls_center.configure(bg=palette.surface)
        self.controls_right.configure(bg=palette.surface)
        self.tape_label.configure(bg=palette.surface, fg=palette.muted)
        self.speed_title.configure(bg=palette.surface, fg=palette.muted)
        self.speed_label.configure(bg=palette.surface, fg=palette.muted)
        style_entry(self.tape_entry, palette, use_mono=True)

        self.statusbar.configure(bg=palette.surface_alt)
        self.hint_label.configure(bg=palette.surface_alt, fg=palette.muted)
        self.status_message.configure(bg=palette.surface_alt, fg=palette.text)
        self.status_dot.configure(bg=palette.surface_alt)

        for button in (
            self.open_button,
            self.save_button,
            self.apply_button,
            self.clear_log_button,
            self.reset_button,
            self.step_button,
            self.run_button,
        ):
            button.apply_theme(palette)
        self.example_dropdown.apply_theme(palette)
        self.speed_slider.apply_theme(palette)
        for chip in (self.state_chip, self.symbol_chip, self.step_chip, self.status_chip):
            chip.apply_theme(palette)
        self.editor.apply_theme(palette)
        self.tape_view.apply_theme(palette)
        self._configure_ttk()

    def run_to_end(self, max_steps: int = 5000) -> None:
        """Выполняет программу до остановки без анимации.

        Метод нужен инструменту скриншотов и ручной проверке. В обычной
        работе он не используется: пользователь нажимает кнопки сам.
        """
        if not self._ensure_machine() or self.machine is None:
            return
        guard = 0
        while self.machine.can_step and guard < max_steps:
            self._do_step()
            self.tape_view.finish_animation()
            guard += 1
        self.update()

    def set_theme(self, name: str) -> None:
        """Принудительно включает тему по имени light или dark."""
        if name not in ("light", "dark"):
            return
        if name == self._theme_name:
            return
        self.toggle_theme()

    def _on_close(self) -> None:
        """Останавливает таймер и закрывает окно."""
        self._stop_run()
        self.destroy()
