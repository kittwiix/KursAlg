"""Точка входа в программу.

Запуск: python main.py
Для работы достаточно стандартной библиотеки Python 3.10 или новее.
"""

from ui.app import TuringApp


def main() -> None:
    """Создаёт главное окно и запускает цикл обработки событий."""
    app = TuringApp()
    app.mainloop()


if __name__ == "__main__":
    main()
