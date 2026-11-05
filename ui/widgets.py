"""Собственные элементы управления, нарисованные на Canvas.

Стандартные кнопки Tkinter выглядят по-разному на разных версиях Windows,
поэтому кнопки, ползунок скорости, плашки индикаторов и выпадающий список
нарисованы вручную. Все они умеют менять палитру и не зависят от ttk-темы.
"""

from __future__ import annotations

import tkinter as tk

from .theme import Palette, font, mono


def rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **options,
) -> int:
    """Рисует прямоугольник со скруглёнными углами.

    Canvas не имеет готовой фигуры с радиусом, поэтому используется
    сглаженный многоугольник. Возвращается идентификатор фигуры, чтобы
    её можно было потом перекрасить.
    """
    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=18, **options)


class RoundedButton(tk.Canvas):
    """Кнопка со скруглением, подсветкой и нажатием.

    Поддерживает несколько стилей: основная, мягкая, прозрачная и опасная.
    Команда вызывается только при отпускании кнопки внутри её области,
    как в обычных оконных приложениях.
    """

    def __init__(
        self,
        master,
        text: str,
        command,
        palette: Palette,
        kind: str = "primary",
        width: int = 120,
        height: int = 38,
        background: str | None = None,
        font_size: int = 10,
        icon: str = "",
    ) -> None:
        """Создаёт кнопку и запоминает её команду и стиль."""
        super().__init__(
            master,
            width=width,
            height=height,
            bg=background or palette.surface,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._text = text
        self._icon = icon
        self._command = command
        self._kind = kind
        self._palette = palette
        self._font_size = font_size
        self._enabled = True
        self._hover = False
        self._pressed = False
        self._fixed_width = width
        self._fixed_height = height
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def _on_configure(self, event: tk.Event) -> None:
        """Запоминает новый размер, если кнопку растянули по сетке."""
        self._fixed_width = max(event.width, 20)
        self._fixed_height = max(event.height, 20)
        self._draw()

    def _colors(self) -> tuple[str, str, str]:
        """Подбирает фон, текст и контур для текущего состояния."""
        p = self._palette
        if not self._enabled:
            return p.surface_alt, p.muted, p.border
        if self._kind == "primary":
            if self._pressed:
                fill = p.accent_pressed
            elif self._hover:
                fill = p.accent_hover
            else:
                fill = p.accent
            return fill, "#FFFFFF", ""
        if self._kind == "soft":
            fill = p.accent_soft if not self._pressed else p.surface_alt
            if self._hover:
                fill = p.surface_alt
            return fill, p.accent, ""
        if self._kind == "danger":
            if self._hover:
                return p.danger, "#FFFFFF", ""
            return p.danger_soft, p.danger, ""
        fill = p.surface_alt if (self._hover or self._pressed) else p.surface
        return fill, p.text, p.border

    def _draw(self) -> None:
        """Перерисовывает фон, контур и подпись кнопки."""
        self.delete("all")
        fill, foreground, outline = self._colors()
        width = self._fixed_width
        height = self._fixed_height
        rounded_rect(
            self,
            2,
            2,
            width - 2,
            height - 2,
            10,
            fill=fill,
            outline=outline,
            width=1,
        )
        label = f"{self._icon}  {self._text}" if self._icon else self._text
        self.create_text(
            width / 2,
            height / 2,
            text=label,
            fill=foreground,
            font=font(self._font_size, "bold" if self._kind == "primary" else "normal"),
        )

    def _on_enter(self, _event: tk.Event) -> None:
        """Включает подсветку при наведении."""
        if self._enabled:
            self._hover = True
            self._draw()

    def _on_leave(self, _event: tk.Event) -> None:
        """Убирает подсветку и сбрасывает нажатие."""
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, _event: tk.Event) -> None:
        """Показывает нажатое состояние."""
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, event: tk.Event) -> None:
        """Выполняет команду, если курсор остался внутри кнопки."""
        if not self._enabled:
            return
        inside = 0 <= event.x <= self._fixed_width and 0 <= event.y <= self._fixed_height
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        if inside and was_pressed:
            self._command()

    def set_text(self, text: str) -> None:
        """Меняет подпись кнопки, например «Запустить» на «Пауза»."""
        self._text = text
        self._draw()

    def set_enabled(self, enabled: bool) -> None:
        """Включает или выключает кнопку."""
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру."""
        self._palette = palette
        self.configure(bg=palette.surface)
        self._draw()


class WindowButton(tk.Canvas):
    """Кнопка заголовка окна: свернуть, развернуть, закрыть, тема.

    Рисуется отдельно от RoundedButton, потому что в заголовке нужен
    компактный квадрат с одним символом и особая подсветка закрытия.
    """

    def __init__(
        self,
        master,
        symbol: str,
        command,
        palette: Palette,
        danger: bool = False,
        width: int = 44,
        height: int = 34,
    ) -> None:
        """Создаёт кнопку с символом и обработчиком нажатия."""
        super().__init__(
            master,
            width=width,
            height=height,
            bg=palette.titlebar,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._symbol = symbol
        self._command = command
        self._palette = palette
        self._danger = danger
        self._hover = False
        self._width = width
        self._height = height
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _draw(self) -> None:
        """Рисует фон и символ в зависимости от наведения."""
        self.delete("all")
        p = self._palette
        fill = p.titlebar
        foreground = p.titlebar_text
        if self._hover:
            fill = p.danger if self._danger else p.surface_alt
            foreground = "#FFFFFF" if self._danger else p.text
        rounded_rect(
            self,
            3,
            3,
            self._width - 3,
            self._height - 3,
            8,
            fill=fill,
            outline="",
        )
        self.create_text(
            self._width / 2,
            self._height / 2,
            text=self._symbol,
            fill=foreground,
            font=font(11, "normal"),
        )

    def _on_enter(self, _event: tk.Event) -> None:
        """Включает подсветку."""
        self._hover = True
        self._draw()

    def _on_leave(self, _event: tk.Event) -> None:
        """Выключает подсветку."""
        self._hover = False
        self._draw()

    def _on_click(self, _event: tk.Event) -> None:
        """Выполняет действие кнопки."""
        self._command()

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру."""
        self._palette = palette
        self.configure(bg=palette.titlebar)
        self._draw()


class StatusChip(tk.Canvas):
    """Плашка с названием и значением показателя.

    Используется для состояния машины, символа под головкой, номера шага
    и статуса выполнения. Ширина подстраивается под окно.
    """

    def __init__(
        self,
        master,
        label: str,
        value: str,
        palette: Palette,
        accent: bool = False,
    ) -> None:
        """Создаёт плашку с подписью и начальным значением."""
        super().__init__(
            master,
            height=58,
            bg=palette.surface,
            highlightthickness=0,
            bd=0,
        )
        self._label = label
        self._value = value
        self._palette = palette
        self._accent = accent
        self._width = 180
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def _on_configure(self, event: tk.Event) -> None:
        """Запоминает ширину, которую выделила сетка."""
        self._width = max(event.width, 60)
        self._draw()

    def _draw(self) -> None:
        """Рисует фон, цветную полоску и два текста."""
        self.delete("all")
        p = self._palette
        fill = p.accent_soft if self._accent else p.surface_alt
        rounded_rect(
            self,
            1,
            1,
            self._width - 1,
            57,
            12,
            fill=fill,
            outline="",
        )
        bar_color = p.accent if self._accent else p.border
        rounded_rect(self, 12, 16, 16, 42, 2, fill=bar_color, outline="")
        self.create_text(
            26,
            17,
            text=self._label.upper(),
            anchor="w",
            fill=p.muted,
            font=font(7, "bold"),
        )
        self.create_text(
            26,
            37,
            text=self._value,
            anchor="w",
            fill=p.accent if self._accent else p.text,
            font=font(12, "bold"),
        )

    def set_value(self, value: str, accent: bool | None = None) -> None:
        """Обновляет значение и при необходимости цвет полоски."""
        self._value = value
        if accent is not None:
            self._accent = accent
        self._draw()

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру."""
        self._palette = palette
        self.configure(bg=palette.surface)
        self._draw()


class SpeedSlider(tk.Canvas):
    """Ползунок скорости автоматического выполнения.

    Значение 0 соответствует медленному режиму, 100 — быстрому. Пауза
    между шагами вычисляется в миллисекундах и передаётся в приложение
    через callback.
    """

    def __init__(
        self,
        master,
        palette: Palette,
        on_change,
        width: int = 220,
    ) -> None:
        """Создаёт ползунок и подписывает края шкалы."""
        super().__init__(
            master,
            width=width,
            height=44,
            bg=palette.surface,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._palette = palette
        self._on_change = on_change
        self._width = width
        self._value = 55
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def _on_configure(self, event: tk.Event) -> None:
        """Подстраивает ширину под контейнер."""
        self._width = max(event.width, 120)
        self._draw()

    def _knob_x(self) -> float:
        """Вычисляет положение кружка по текущему значению."""
        return 12 + (self._width - 24) * self._value / 100

    def _set_from_x(self, x: float) -> None:
        """Переводит координату курсора в значение от 0 до 100."""
        width = max(self._width - 24, 1)
        value = int(round((x - 12) / width * 100))
        value = max(0, min(100, value))
        if value != self._value:
            self._value = value
            self._draw()
            self._on_change(self._value)

    def _on_click(self, event: tk.Event) -> None:
        """Ставит ползунок в точку нажатия."""
        self._set_from_x(event.x)

    def _on_drag(self, event: tk.Event) -> None:
        """Двигает ползунок за курсором."""
        self._set_from_x(event.x)

    def _draw(self) -> None:
        """Рисует дорожку, заполненную часть и кружок."""
        self.delete("all")
        p = self._palette
        left = 12
        right = self._width - 12
        rounded_rect(self, left, 14, right, 21, 3, fill=p.surface_alt, outline="")
        knob_x = self._knob_x()
        if knob_x > left + 2:
            rounded_rect(self, left, 14, knob_x, 21, 3, fill=p.accent, outline="")
        self.create_oval(
            knob_x - 8,
            10,
            knob_x + 8,
            26,
            fill=p.surface,
            outline=p.accent,
            width=3,
        )
        self.create_text(
            left,
            34,
            text="медленно",
            anchor="w",
            fill=p.muted,
            font=font(7),
        )
        self.create_text(
            right,
            34,
            text="быстро",
            anchor="e",
            fill=p.muted,
            font=font(7),
        )

    @property
    def delay_ms(self) -> int:
        """Пауза между шагами в миллисекундах."""
        return int(round(700 - 660 * self._value / 100))

    def set_value(self, value: int) -> None:
        """Устанавливает значение без вызова callback."""
        self._value = max(0, min(100, int(value)))
        self._draw()

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру."""
        self._palette = palette
        self.configure(bg=palette.surface)
        self._draw()


class Dropdown(tk.Canvas):
    """Компактный выпадающий список на Canvas.

    Показывает выбранный пункт и открывает обычное меню Tkinter. Меню
    перекрашивается вместе с темой, поэтому список не выбивается из окна.
    """

    def __init__(
        self,
        master,
        palette: Palette,
        items: list[tuple[str, str]],
        on_change,
        width: int = 280,
    ) -> None:
        """Создаёт список и запоминает обработчик выбора."""
        super().__init__(
            master,
            width=width,
            height=38,
            bg=palette.surface,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._palette = palette
        self._items = list(items)
        self._on_change = on_change
        self._width = width
        self._value = self._items[0][0] if self._items else ""
        self._menu = tk.Menu(self, tearoff=0)
        self.bind("<Button-1>", self._open)
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def _on_configure(self, event: tk.Event) -> None:
        """Подстраивает ширину под контейнер."""
        self._width = max(event.width, 120)
        self._draw()

    def _selected_title(self) -> str:
        """Возвращает подпись выбранного пункта."""
        for key, title in self._items:
            if key == self._value:
                return title
        return "Выберите пример"

    def _draw(self) -> None:
        """Рисует рамку, подпись и стрелку."""
        self.delete("all")
        p = self._palette
        rounded_rect(
            self,
            1,
            1,
            self._width - 1,
            37,
            10,
            fill=p.surface_alt,
            outline=p.border,
            width=1,
        )
        self.create_text(
            14,
            19,
            text=self._selected_title(),
            anchor="w",
            fill=p.text,
            font=font(10),
        )
        self.create_text(
            self._width - 18,
            19,
            text="▾",
            anchor="e",
            fill=p.accent,
            font=font(12, "bold"),
        )

    def _open(self, _event: tk.Event) -> None:
        """Открывает меню под списком."""
        self._menu.delete(0, "end")
        p = self._palette
        self._menu.configure(
            bg=p.surface,
            fg=p.text,
            activebackground=p.accent,
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            font=font(10),
        )
        for key, title in self._items:
            self._menu.add_command(
                label=title,
                command=lambda chosen=key: self._choose(chosen),
            )
        try:
            self._menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + 40)
        finally:
            self._menu.grab_release()

    def _choose(self, key: str) -> None:
        """Запоминает выбранный пункт и сообщает приложению."""
        self._value = key
        self._draw()
        self._on_change(key)

    def get_value(self) -> str:
        """Возвращает ключ выбранного пункта."""
        return self._value

    def set_items(self, items: list[tuple[str, str]]) -> None:
        """Заменяет список пунктов."""
        self._items = list(items)
        if self._items and not any(key == self._value for key, _ in self._items):
            self._value = self._items[0][0]
        self._draw()

    def set_value(self, key: str) -> None:
        """Выбирает пункт по ключу без вызова callback."""
        self._value = key
        self._draw()

    def apply_theme(self, palette: Palette) -> None:
        """Применяет новую палитру."""
        self._palette = palette
        self.configure(bg=palette.surface)
        self._draw()


def style_entry(entry: tk.Entry, palette: Palette, use_mono: bool = False) -> None:
    """Приводит обычный Entry к стилю приложения.

    Функция нужна для полей ввода ленты и лимита шагов: стандартный вид
    Entry слишком сильно отличается от остальных элементов.
    """
    entry.configure(
        bg=palette.code_bg,
        fg=palette.code_text,
        insertbackground=palette.text,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=palette.border,
        highlightcolor=palette.accent,
        selectbackground=palette.selection,
        selectforeground=palette.text,
        font=mono(11) if use_mono else font(10),
    )
