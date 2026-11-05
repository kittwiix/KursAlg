"""Своя рамка окна вместо стандартной рамки Windows.

Заголовок, кнопки свернуть/развернуть/закрыть и изменение размера за края
сделаны вручную. Так окно выглядит одинаково и в светлой, и в тёмной теме.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import tkinter as tk

from .theme import Palette, font
from .widgets import WindowButton, rounded_rect


class CustomWindow(tk.Tk):
    """Главное окно с собственной рамкой и заголовком.

    Наследуется от tk.Tk и создаёт внутри два контейнера: titlebar и content.
    Приложение размещает свои элементы в content. Перетаскивание заголовка,
    двойной клик и изменение размера обрабатываются здесь же.
    """

    def __init__(self, title: str, subtitle: str, palette: Palette) -> None:
        """Создаёт окно, заголовок и области для содержимого."""
        super().__init__()
        self._palette = palette
        self._window_title = title
        self._subtitle = subtitle
        self._drag_x = 0
        self._drag_y = 0
        self._maximized = False
        self._restore_geometry = "1280x860+80+40"
        self._resize_edge = ""
        self._resize_start = (0, 0, 0, 0, 0, 0)

        self.overrideredirect(True)
        self.geometry("1280x860+80+40")
        self.minsize(1040, 720)
        self.configure(bg=palette.border)

        self.shell = tk.Frame(self, bg=palette.border)
        self.shell.pack(fill="both", expand=True, padx=1, pady=1)
        self.inner = tk.Frame(self.shell, bg=palette.bg)
        self.inner.pack(fill="both", expand=True)

        self.titlebar = tk.Frame(self.inner, bg=palette.titlebar, height=56)
        self.titlebar.pack(side="top", fill="x")
        self.titlebar.pack_propagate(False)

        self.content = tk.Frame(self.inner, bg=palette.bg)
        self.content.pack(side="top", fill="both", expand=True)

        self._build_titlebar()
        self._build_resize_grips()
        self._enable_taskbar_button()
        self.bind("<Map>", self._on_map)

    def _build_titlebar(self) -> None:
        """Создаёт логотип, название, подзаголовок и кнопки окна."""
        p = self._palette
        self.logo = tk.Canvas(
            self.titlebar,
            width=34,
            height=34,
            bg=p.titlebar,
            highlightthickness=0,
            bd=0,
        )
        self.logo.pack(side="left", padx=(18, 10))
        self._draw_logo()

        self.title_box = tk.Frame(self.titlebar, bg=p.titlebar)
        self.title_box.pack(side="left", fill="y", pady=11)
        self.title_label = tk.Label(
            self.title_box,
            text=self._window_title,
            bg=p.titlebar,
            fg=p.titlebar_text,
            font=font(11, "bold"),
            anchor="w",
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            self.title_box,
            text=self._subtitle,
            bg=p.titlebar,
            fg=p.muted,
            font=font(8),
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w")

        self.close_button = WindowButton(
            self.titlebar, "✕", self._close, p, danger=True
        )
        self.close_button.pack(side="right", padx=(0, 10), pady=11)
        self.max_button = WindowButton(
            self.titlebar, "□", self._toggle_maximize, p
        )
        self.max_button.pack(side="right", pady=11)
        self.min_button = WindowButton(
            self.titlebar, "—", self._minimize, p
        )
        self.min_button.pack(side="right", pady=11)
        self.theme_button = WindowButton(
            self.titlebar, "☾", self._theme_clicked, p
        )
        self.theme_button.pack(side="right", padx=(0, 8), pady=11)

        for widget in (
            self.titlebar,
            self.logo,
            self.title_box,
            self.title_label,
            self.subtitle_label,
        ):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            widget.bind("<Double-Button-1>", self._toggle_maximize)

    def _draw_logo(self) -> None:
        """Рисует маленький знак ленты в квадрате акцентного цвета."""
        p = self._palette
        self.logo.delete("all")
        rounded_rect(self.logo, 1, 1, 33, 33, 9, fill=p.accent, outline="")
        self.logo.create_text(
            9,
            17,
            text="1",
            fill="#FFFFFF",
            font=font(10, "bold"),
        )
        self.logo.create_text(
            17,
            17,
            text="0",
            fill="#FFFFFF",
            font=font(10, "bold"),
        )
        self.logo.create_text(
            25,
            17,
            text="1",
            fill="#FFFFFF",
            font=font(10, "bold"),
        )

    def _enable_taskbar_button(self) -> None:
        """Просит Windows показать кнопку окна на панели задач.

        Окно без стандартной рамки по умолчанию не попадает на панель задач.
        Расширенный стиль WS_EX_APPWINDOW исправляет это. Если вызов Windows
        недоступен, окно продолжает работать без кнопки на панели.
        """
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()
            gwl_exstyle = -20
            ws_ex_appwindow = 0x00040000
            ws_ex_toolwindow = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, gwl_exstyle)
            style = (style | ws_ex_appwindow) & ~ws_ex_toolwindow
            ctypes.windll.user32.SetWindowLongW(hwnd, gwl_exstyle, style)
        except Exception:
            pass

    def _build_resize_grips(self) -> None:
        """Создаёт невидимые полосы по краям для изменения размера."""
        self._grips: list[tk.Frame] = []
        specs = [
            ("top", {"x": 8, "y": 0, "relwidth": 1, "width": -16, "height": 4},
             "sb_v_double_arrow"),
            ("bottom", {"x": 8, "rely": 1, "y": -4, "relwidth": 1,
                        "width": -16, "height": 4}, "sb_v_double_arrow"),
            ("left", {"x": 0, "y": 8, "relheight": 1, "height": -16, "width": 4},
             "sb_h_double_arrow"),
            ("right", {"x": -4, "rely": 0, "y": 8, "relx": 1, "relheight": 1,
                       "height": -16, "width": 4}, "sb_h_double_arrow"),
            ("nw", {"x": 0, "y": 0, "width": 8, "height": 8}, "size_nw_se"),
            ("ne", {"relx": 1, "x": -8, "y": 0, "width": 8, "height": 8}, "size_ne_sw"),
            ("sw", {"x": 0, "rely": 1, "y": -8, "width": 8, "height": 8}, "size_ne_sw"),
            ("se", {"relx": 1, "x": -8, "rely": 1, "y": -8, "width": 8, "height": 8}, "size_nw_se"),
        ]
        for edge, place_options, cursor in specs:
            grip = tk.Frame(self, bg=self._palette.bg, cursor=cursor)
            grip.place(**place_options)
            grip.bind("<ButtonPress-1>", lambda event, name=edge: self._start_resize(name, event))
            grip.bind("<B1-Motion>", self._do_resize)
            grip.lift()
            self._grips.append(grip)

    def _start_drag(self, event: tk.Event) -> None:
        """Запоминает точку, за которую пользователь взял заголовок."""
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _do_drag(self, event: tk.Event) -> None:
        """Перемещает окно вслед за курсором."""
        if self._maximized:
            return
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _start_resize(self, edge: str, event: tk.Event) -> None:
        """Запоминает размеры окна перед изменением."""
        self._resize_edge = edge
        self._resize_start = (
            event.x_root,
            event.y_root,
            self.winfo_x(),
            self.winfo_y(),
            self.winfo_width(),
            self.winfo_height(),
        )

    def _do_resize(self, event: tk.Event) -> None:
        """Меняет размер окна в зависимости от потянутого края."""
        if not self._resize_edge or self._maximized:
            return
        start_x, start_y, x, y, width, height = self._resize_start
        dx = event.x_root - start_x
        dy = event.y_root - start_y
        edge = self._resize_edge
        min_width, min_height = 1040, 720
        if "w" in edge:
            x += dx
            width -= dx
        if "e" in edge:
            width += dx
        if "n" in edge:
            y += dy
            height -= dy
        if "s" in edge:
            height += dy
        if width < min_width:
            if "w" in edge:
                x -= min_width - width
            width = min_width
        if height < min_height:
            if "n" in edge:
                y -= min_height - height
            height = min_height
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _toggle_maximize(self, _event: tk.Event | None = None) -> None:
        """Разворачивает окно на весь рабочий стол или возвращает размер."""
        if self._maximized:
            self.geometry(self._restore_geometry)
            self._maximized = False
            self.max_button._symbol = "□"
            self.max_button._draw()
            return
        self._restore_geometry = self.geometry()
        left, top, right, bottom = self._work_area()
        self.geometry(f"{right - left}x{bottom - top}+{left}+{top}")
        self._maximized = True
        self.max_button._symbol = "❐"
        self.max_button._draw()

    def _work_area(self) -> tuple[int, int, int, int]:
        """Возвращает рабочую область экрана без панели задач."""
        try:
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            return rect.left, rect.top, rect.right, rect.bottom
        except Exception:
            return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def _minimize(self) -> None:
        """Сворачивает окно, сохраняя возможность вернуться."""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
            ctypes.windll.user32.ShowWindow(hwnd, 6)
        except Exception:
            self.iconify()

    def _close(self) -> None:
        """Закрывает приложение."""
        self.destroy()

    def _theme_clicked(self) -> None:
        """Вызывает обработчик переключения темы, если он задан."""
        callback = getattr(self, "theme_callback", None)
        if callback is not None:
            callback()

    def set_theme_symbol(self, symbol: str) -> None:
        """Меняет значок на кнопке темы: луна или солнце."""
        self.theme_button._symbol = symbol
        self.theme_button._draw()

    def _on_map(self, _event: tk.Event) -> None:
        """Возвращает окно на передний план после восстановления."""
        self.lift()

    def apply_theme(self, palette: Palette) -> None:
        """Перекрашивает рамку, заголовок и кнопки окна."""
        self._palette = palette
        self.configure(bg=palette.border)
        self.shell.configure(bg=palette.border)
        self.inner.configure(bg=palette.bg)
        self.titlebar.configure(bg=palette.titlebar)
        self.title_box.configure(bg=palette.titlebar)
        self.title_label.configure(bg=palette.titlebar, fg=palette.titlebar_text)
        self.subtitle_label.configure(bg=palette.titlebar, fg=palette.muted)
        self.logo.configure(bg=palette.titlebar)
        self._draw_logo()
        for button in (self.close_button, self.max_button, self.min_button, self.theme_button):
            button.apply_theme(palette)
        for grip in self._grips:
            grip.configure(bg=palette.bg)
