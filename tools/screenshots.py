"""Снимает скриншоты работающей программы для отчёта и презентации.

Скрипт запускает настоящее окно Tkinter, загружает примеры, выполняет шаги
и сохраняет снимки области окна. Запуск:

    python tools/screenshots.py
"""

from __future__ import annotations

import ctypes
import sys
import time
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.app import TuringApp  # noqa: E402

OUTPUT = ROOT / "docs" / "screenshots"


def settle(app: TuringApp, seconds: float = 0.35) -> None:
    """Даёт окну время перерисоваться и завершает анимацию ленты."""
    app.update_idletasks()
    app.update()
    time.sleep(seconds)
    app.tape_view.finish_animation()
    app.update_idletasks()
    app.update()


def capture(app: TuringApp, name: str) -> None:
    """Сохраняет снимок только области окна, без рабочего стола."""
    settle(app)
    ctypes.windll.user32.SetCursorPos(4, 4)
    app.update_idletasks()
    app.update()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    width = app.winfo_width()
    height = app.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    image.save(path)
    print(f"сохранён {path} ({image.width}x{image.height})")


def main() -> None:
    """Создаёт окно и снимает все нужные кадры."""
    app = TuringApp()
    app.geometry("1280x860+40+30")
    app.attributes("-topmost", True)
    app.lift()
    app.focus_force()
    settle(app, 0.6)

    app.load_example("addition")
    for _ in range(4):
        app.step_once()
        app.update()
        time.sleep(0.12)
    capture(app, "main_light.png")

    app.load_example("copy")
    for _ in range(18):
        app.step_once()
        app.update()
        time.sleep(0.05)
    app.tape_view.finish_animation()
    app.set_theme("dark")
    capture(app, "main_dark.png")

    app.set_theme("light")
    app.load_example("loop")
    app.update()
    app.run_to_end()
    capture(app, "limit_warning.png")

    app.load_example("addition")
    app.run_to_end()
    capture(app, "addition_result.png")

    app.load_example("addition")
    app.editor.set_text(
        "q0 1 -> q1 0 R\n"
        "q0 1 -> q2 0 L\n"
        "q1 _ -> qz _ N\n"
    )
    app._validate_live(app.editor.get_text())
    app._build_machine()
    app.update()
    capture(app, "syntax_error.png")

    app.load_example("erase")
    app.tape_var.set("|")
    app._reset_machine()
    app.update()
    capture(app, "empty_tape.png")

    app.destroy()
    print("готово")


if __name__ == "__main__":
    main()
