"""Редактор программы с номерами строк и подсветкой синтаксиса.

Пользователь пишет таблицу переходов обычным текстом. Редактор раскрашивает
состояния, стрелки и направления сдвига, показывает номера строк и умеет
подсветить строку с ошибкой или выполняемое правило.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import Palette, font, mono


class ProgramEditor(tk.Frame):
    """Текстовый редактор таблицы переходов.

    Содержит поле Text, полотно с номерами строк и полосу прокрутки.
    Изменения передаются в приложение через callback с небольшой задержкой,
    чтобы проверка синтаксиса не запускалась на каждую нажатую клавишу.
    """

    def __init__(self, master, palette: Palette, on_change) -> None:
        """Создаёт редактор и подписывается на изменения текста."""
        super().__init__(master, bg=palette.surface)
        self._palette = palette
        self._on_change = on_change
        self._change_job = None
        self._suppress_change = False
        self._active_line = 0
        self._error_line = 0

        self.header_frame = tk.Frame(self, bg=palette.surface)
        self.header_frame.pack(side="top", fill="x", padx=14, pady=(10, 6))
        self.title_label = tk.Label(
            self.header_frame,
            text="Программа",
            bg=palette.surface,
            fg=palette.text,
            font=font(10, "bold"),
        )
        self.title_label.pack(side="left")
        self.status_label = tk.Label(
            self.header_frame,
            text="",
            bg=palette.surface,
            fg=palette.muted,
            font=font(8),
        )
        self.status_label.pack(side="right")

        self.body_frame = tk.Frame(self, bg=palette.code_bg)
        self.body_frame.pack(side="top", fill="both", expand=True, padx=14, pady=(0, 12))
        self.body_frame.grid_rowconfigure(0, weight=1)
        self.body_frame.grid_columnconfigure(1, weight=1)

        self.line_numbers = tk.Canvas(
            self.body_frame,
            width=42,
            bg=palette.code_bg,
            highlightthickness=0,
            bd=0,
        )
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.text = tk.Text(
            self.body_frame,
            wrap="none",
            undo=True,
            bg=palette.code_bg,
            fg=palette.code_text,
            insertbackground=palette.text,
            selectbackground=palette.selection,
            selectforeground=palette.text,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=palette.border,
            highlightcolor=palette.accent,
            padx=10,
            pady=8,
            font=mono(10),
            spacing1=0,
            spacing3=0,
        )
        self.text.grid(row=0, column=1, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self.body_frame,
            orient="vertical",
            command=self._on_scroll,
            style="Vertical.TScrollbar",
        )
        self.scrollbar.grid(row=0, column=2, sticky="ns")
        self.text.configure(yscrollcommand=self._on_text_scroll)

        self._configure_tags()
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._schedule_numbers)
        self.text.bind("<ButtonRelease-1>", self._schedule_numbers)
        self.text.bind("<MouseWheel>", self._on_wheel)
        self.text.bind("<Configure>", self._schedule_numbers)
        self._schedule_numbers()

    def _configure_tags(self) -> None:
        """Создаёт теги подсветки для текущей палитры."""
        p = self._palette
        self.text.tag_configure("comment", foreground=p.code_comment)
        self.text.tag_configure("arrow", foreground=p.accent, font=mono(10, "bold"))
        self.text.tag_configure("state", foreground=p.code_state, font=mono(10, "bold"))
        self.text.tag_configure("move", foreground=p.code_move, font=mono(10, "bold"))
        self.text.tag_configure("symbol", foreground=p.code_symbol)
        self.text.tag_configure("active_line", background=p.accent_soft)
        self.text.tag_configure("error_line", background=p.danger_soft)
        self.text.tag_raise("active_line")
        self.text.tag_raise("error_line")

    def _on_modified(self, _event: tk.Event) -> None:
        """Запускает проверку текста после паузы в наборе."""
        if self.text.edit_modified():
            self.text.edit_modified(False)
            if self._suppress_change:
                return
            if self._change_job is not None:
                self.after_cancel(self._change_job)
            self._change_job = self.after(280, self._notify_change)
            self._schedule_numbers()

    def _notify_change(self) -> None:
        """Передаёт новый текст приложению для проверки синтаксиса."""
        self._change_job = None
        self._on_change(self.get_text())

    def _schedule_numbers(self, _event: tk.Event | None = None) -> None:
        """Планирует перерисовку номеров строк."""
        self.after_idle(self._redraw_numbers)

    def _redraw_numbers(self) -> None:
        """Рисует номера только для видимых строк."""
        self.line_numbers.delete("all")
        first_index = self.text.index("@0,0")
        try:
            first_line = int(first_index.split(".")[0])
        except (ValueError, IndexError):
            first_line = 1
        last_line = int(self.text.index("end-1c").split(".")[0])
        width = max(self.line_numbers.winfo_width(), 42)
        for line in range(first_line, last_line + 1):
            info = self.text.dlineinfo(f"{line}.0")
            if info is None:
                continue
            x, y, _line_width, height, _baseline = info
            color = self._palette.accent if line == self._active_line else self._palette.muted
            if line == self._error_line:
                color = self._palette.danger
            self.line_numbers.create_text(
                width - 8,
                y + height / 2,
                text=str(line),
                anchor="e",
                fill=color,
                font=font(8),
            )

    def _on_scroll(self, *args) -> None:
        """Прокручивает текст и обновляет номера строк."""
        self.text.yview(*args)
        self._redraw_numbers()

    def _on_text_scroll(self, first: str, last: str) -> None:
        """Синхронизирует полосу прокрутки с текстом."""
        self.scrollbar.set(first, last)
        self._redraw_numbers()

    def _on_wheel(self, event: tk.Event):
        """Прокручивает текст колесом мыши."""
        self.text.yview_scroll(int(-event.delta / 120), "units")
        self._redraw_numbers()
        return "break"

    def _token_spans(self, line: str):
        """Разбивает строку на слова и возвращает их позиции.

        Обычный split() не подходит, потому что для подсветки нужны начала
        и концы слов. Поэтому строка просматривается вручную, без регулярок.
        """
        index = 0
        length = len(line)
        while index < length:
            if line[index].isspace():
                index += 1
                continue
            start = index
            while index < length and not line[index].isspace():
                index += 1
            yield start, index, line[start:index]

    def _apply_syntax(self) -> None:
        """Раскрашивает комментарии, состояния, стрелки и сдвиги."""
        for tag in ("comment", "arrow", "state", "move", "symbol"):
            self.text.tag_remove(tag, "1.0", "end")
        line_count = int(self.text.index("end-1c").split(".")[0])
        for line_number in range(1, line_count + 1):
            line = self.text.get(f"{line_number}.0", f"{line_number}.end")
            if not line:
                continue
            comment_start = line.find("#")
            code_part = line if comment_start < 0 else line[:comment_start]
            if comment_start >= 0:
                self.text.tag_add(
                    "comment",
                    f"{line_number}.{comment_start}",
                    f"{line_number}.{len(line)}",
                )
            for start, end, token in self._token_spans(code_part):
                tag = ""
                if token in ("->", "→"):
                    tag = "arrow"
                elif token.upper() in ("L", "R", "N"):
                    tag = "move"
                elif token.lower().startswith("q"):
                    tag = "state"
                elif len(token) == 1:
                    tag = "symbol"
                if tag:
                    self.text.tag_add(
                        tag,
                        f"{line_number}.{start}",
                        f"{line_number}.{end}",
                    )

    def get_text(self) -> str:
        """Возвращает весь текст программы."""
        return self.text.get("1.0", "end-1c")

    def set_text(self, text: str) -> None:
        """Заменяет текст программы и сбрасывает подсветку ошибок."""
        self._suppress_change = True
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self._suppress_change = False
        self.clear_error()
        self.clear_active_line()
        self._apply_syntax()
        self._redraw_numbers()

    def set_status(self, text: str, kind: str = "normal") -> None:
        """Показывает состояние проверки справа от заголовка."""
        colors = {
            "normal": self._palette.muted,
            "ok": self._palette.success,
            "error": self._palette.danger,
        }
        self.status_label.configure(text=text, fg=colors.get(kind, self._palette.muted))

    def mark_error(self, line_number: int) -> None:
        """Подсвечивает строку с ошибкой и прокручивает к ней."""
        self.clear_error()
        if line_number < 1:
            return
        self._error_line = line_number
        self.text.tag_add(
            "error_line",
            f"{line_number}.0",
            f"{line_number}.end+1c",
        )
        self.text.see(f"{line_number}.0")
        self._redraw_numbers()

    def clear_error(self) -> None:
        """Убирает подсветку ошибки."""
        self.text.tag_remove("error_line", "1.0", "end")
        self._error_line = 0
        self._redraw_numbers()

    def highlight_line(self, line_number: int) -> None:
        """Подсвечивает правило, которое будет выполнено следующим."""
        self.clear_active_line()
        if line_number < 1:
            return
        self._active_line = line_number
        self.text.tag_add(
            "active_line",
            f"{line_number}.0",
            f"{line_number}.end+1c",
        )
        self.text.see(f"{line_number}.0")
        self._redraw_numbers()

    def clear_active_line(self) -> None:
        """Снимает подсветку выполняемого правила."""
        self.text.tag_remove("active_line", "1.0", "end")
        self._active_line = 0
        self._redraw_numbers()

    def apply_theme(self, palette: Palette) -> None:
        """Перекрашивает редактор и все теги подсветки."""
        self._palette = palette
        self.configure(bg=palette.surface)
        self.header_frame.configure(bg=palette.surface)
        self.body_frame.configure(bg=palette.code_bg)
        self.title_label.configure(bg=palette.surface, fg=palette.text)
        self.status_label.configure(bg=palette.surface, fg=palette.muted)
        self.text.configure(
            bg=palette.code_bg,
            fg=palette.code_text,
            insertbackground=palette.text,
            selectbackground=palette.selection,
            selectforeground=palette.text,
            highlightbackground=palette.border,
            highlightcolor=palette.accent,
        )
        self.line_numbers.configure(bg=palette.code_bg)
        self._configure_tags()
        self._apply_syntax()
        self._redraw_numbers()
