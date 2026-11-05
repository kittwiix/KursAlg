"""Вид ленты с плавным движением и подсветкой головки.

Полотно создаётся один раз: ячейки, символы и номера позиций — отдельные
элементы Canvas. При шаге они сдвигаются, а не перерисовываются заново,
поэтому лента движется плавно и без мерцания.
"""

from __future__ import annotations

import tkinter as tk

from .theme import Palette, font
from .widgets import rounded_rect


class TapeView(tk.Canvas):
    """Полотно ленты с закреплённой по центру головкой.

    Головка всегда находится в центре, а лента прокручивается под ней.
    Так бесконечную ленту можно показывать без прыжков и пересчёта
    координат за пределами экрана.
    """

    def __init__(self, master, palette: Palette) -> None:
        """Создаёт полотно и задаёт размеры ячеек."""
        super().__init__(
            master,
            height=142,
            bg=palette.tape_bg,
            highlightthickness=0,
            bd=0,
        )
        self._palette = palette
        self._cell_width = 58
        self._cell_height = 60
        self._gap = 8
        self._count = 0
        self._center = 0
        self._anchor = 0
        self._tape = None
        self._rect_items: list[int] = []
        self._symbol_items: list[int] = []
        self._index_items: list[int] = []
        self._positions: list[tuple[float, float, float, float]] = []
        self._head_items: list[int] = []
        self._animation_job = None
        self._animation_step = 0
        self._animation_shift = 0
        self._animation_dx = 0.0
        self._flash_job = None
        self._flashing_index = -1
        self.bind("<Configure>", self._on_configure)
        self._build()

    def _on_configure(self, _event: tk.Event) -> None:
        """Пересобирает ячейки, если окно заметно изменило ширину."""
        available = max(self.winfo_width() - 32, 200)
        needed = max(9, int(available / (self._cell_width + self._gap)))
        if needed % 2 == 0:
            needed -= 1
        if needed != self._count:
            self.after_idle(self._build)

    def _build(self) -> None:
        """Создаёт элементы ленты и головки заново.

        Этот метод вызывается только при изменении размера окна или темы,
        а не на каждом шаге. Во время выполнения шага используются уже
        готовые элементы.
        """
        self.delete("all")
        width = max(self.winfo_width(), 400)
        available = width - 32
        count = max(9, int(available / (self._cell_width + self._gap)))
        if count % 2 == 0:
            count -= 1
        self._count = count
        self._center = count // 2
        if self._tape is not None:
            self._anchor = self._tape.head - self._center
        else:
            self._anchor = -self._center
        total_width = count * self._cell_width + (count - 1) * self._gap
        start_x = (width - total_width) / 2
        y1 = 38
        y2 = y1 + self._cell_height
        self._rect_items = []
        self._symbol_items = []
        self._index_items = []
        self._positions = []
        for index in range(count):
            x1 = start_x + index * (self._cell_width + self._gap)
            x2 = x1 + self._cell_width
            rect = self.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=self._palette.cell,
                outline=self._palette.border,
                width=1,
                tags=("cell",),
            )
            symbol = self.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text="_",
                fill=self._palette.text,
                font=font(18, "bold"),
                tags=("cell",),
            )
            number = self.create_text(
                (x1 + x2) / 2,
                y2 + 13,
                text="0",
                fill=self._palette.muted,
                font=font(7),
                tags=("cell",),
            )
            self._rect_items.append(rect)
            self._symbol_items.append(symbol)
            self._index_items.append(number)
            self._positions.append((x1, y1, x2, y2))
        self._create_head()
        self._update_cells()

    def _create_head(self) -> None:
        """Рисует рамку головки, указатель и подпись над центром."""
        p = self._palette
        x1, y1, x2, y2 = self._positions[self._center]
        self._head_items = []
        outline = rounded_rect(
            self,
            x1 - 2,
            y1 - 2,
            x2 + 2,
            y2 + 2,
            9,
            fill="",
            outline=p.head,
            width=2,
            tags=("head",),
        )
        self._head_items.append(outline)
        cx = (x1 + x2) / 2
        triangle = self.create_polygon(
            cx - 6,
            22,
            cx + 6,
            22,
            cx,
            30,
            fill=p.head,
            outline="",
            tags=("head",),
        )
        self._head_items.append(triangle)
        label = self.create_text(
            cx,
            12,
            text="ГОЛОВКА",
            fill=p.head,
            font=font(7, "bold"),
            tags=("head",),
        )
        self._head_items.append(label)

    def set_tape(self, tape) -> None:
        """Показывает новую ленту и ставит головку в центр."""
        self._tape = tape
        if not self._rect_items or self._count == 0:
            self._build()
            return
        self._anchor = tape.head - self._center
        self._update_cells()

    def refresh(self) -> None:
        """Обновляет символы без анимации."""
        if self._tape is None:
            return
        self._update_cells()

    def _update_cells(self) -> None:
        """Переписывает символы и номера позиций для текущего сдвига."""
        if self._tape is None or not self._rect_items:
            return
        for index in range(self._count):
            self._paint_cell(index)

    def _paint_cell(self, index: int) -> None:
        """Красит одну ячейку по её текущему символу."""
        if not (0 <= index < self._count):
            return
        position = self._anchor + index
        symbol = self._tape.read(position)
        is_head = index == self._center
        p = self._palette
        fill = p.accent_soft if is_head else (p.cell if index % 2 == 0 else p.cell_alt)
        outline = p.head if is_head else p.border
        width = 2 if is_head else 1
        self.itemconfigure(
            self._rect_items[index],
            fill=fill,
            outline=outline,
            width=width,
        )
        self.itemconfigure(
            self._symbol_items[index],
            text=symbol,
            fill=p.muted if symbol == self._tape.blank else p.text,
        )
        self.itemconfigure(
            self._index_items[index],
            text=str(position),
            fill=p.head_text if is_head else p.muted,
        )

    def _layout_cells(self) -> None:
        """Возвращает элементы на исходные места после анимации."""
        for index in range(self._count):
            x1, y1, x2, y2 = self._positions[index]
            self.coords(self._rect_items[index], x1, y1, x2, y2)
            self.coords(self._symbol_items[index], (x1 + x2) / 2, (y1 + y2) / 2)
            self.coords(self._index_items[index], (x1 + x2) / 2, y2 + 13)

    def animate_step(self, entry) -> None:
        """Плавно сдвигает ленту на один шаг.

        Запись entry берётся из журнала исполнителя. Если головка осталась
        на месте, лента не двигается, но записанная ячейка подсвечивается.
        """
        if self._tape is None or entry is None:
            return
        self.finish_animation()
        shift = entry.head_after - entry.head_before
        if shift == 0:
            self._update_cells()
            self._flash_index(self._center)
            return
        stride = self._cell_width + self._gap
        self._animation_shift = shift
        self._animation_dx = -shift * stride
        self._animation_step = 0
        self._animation_job = self.after(12, self._animation_tick)

    def _animation_tick(self) -> None:
        """Делает очередной маленький сдвиг ленты."""
        steps = 8
        if self._animation_step >= steps:
            self._complete_animation()
            return
        self.move("cell", self._animation_dx / steps, 0)
        self._animation_step += 1
        self._animation_job = self.after(16, self._animation_tick)

    def _complete_animation(self) -> None:
        """Завершает сдвиг и обновляет данные ленты."""
        if self._animation_job is not None:
            try:
                self.after_cancel(self._animation_job)
            except tk.TclError:
                pass
            self._animation_job = None
        shift = self._animation_shift
        self._anchor += shift
        self._layout_cells()
        self._update_cells()
        self._animation_shift = 0
        self._animation_dx = 0.0
        self._flash_index(self._center - shift)

    def finish_animation(self) -> None:
        """Немедленно завершает анимацию, если она ещё идёт.

        Нужен при быстром автоматическом запуске и при снятии скриншотов,
        чтобы кадр не попал в середину движения.
        """
        if self._animation_job is not None:
            self._complete_animation()

    def _flash_index(self, index: int) -> None:
        """Подсвечивает ячейку, в которую только что записали символ."""
        if not (0 <= index < self._count):
            return
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except tk.TclError:
                pass
        self._flashing_index = index
        p = self._palette
        self.itemconfigure(
            self._rect_items[index],
            fill=p.warning_soft,
            outline=p.warning,
            width=2,
        )
        self._flash_job = self.after(240, self._end_flash)

    def _end_flash(self) -> None:
        """Возвращает ячейке обычный цвет после подсветки."""
        self._flash_job = None
        if self._flashing_index >= 0:
            self._paint_cell(self._flashing_index)
            self._flashing_index = -1

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру и пересобирает полотно."""
        self._palette = palette
        self.configure(bg=palette.tape_bg)
        self._build()
