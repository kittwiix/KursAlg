"""Лента машины Тьюринга и головка чтения-записи.

Лента бесконечна в обе стороны, поэтому в памяти хранятся только те ячейки,
где стоит непустой символ. Все остальные позиции считаются пустыми. Такой
подход позволяет работать с длинными лентами и не выделять память заранее.
"""

from __future__ import annotations

from .errors import TapeParseError

# Пустая ячейка на экране и в текстовой записи обозначается подчёркиванием.
BLANK = "_"

# Вертикальная черта в начальной строке показывает, где стоит головка.
HEAD_MARKER = "|"


class Tape:
    """Хранит символы ленты и позицию головки.

    Класс отвечает только за данные: чтение, запись и сдвиг. Правила переходов
    и порядок выполнения живут в других классах. Ленту удобно создавать из
    строки вида «111|011», где черта стоит перед символом под головкой.
    """

    def __init__(
        self,
        cells: dict[int, str] | None = None,
        head: int = 0,
        blank: str = BLANK,
    ) -> None:
        """Создаёт ленту из словаря позиций и начальной позиции головки.

        Пустые символы в словарь не попадают: если ячейку стёрли, ключ
        удаляется. Благодаря этому лента действительно ведёт себя как
        бесконечная, а не как список фиксированной длины.
        """
        if len(blank) != 1:
            raise ValueError("Обозначение пустой ячейки должно быть одним символом.")
        self._blank = blank
        self._cells: dict[int, str] = {}
        if cells:
            for position, symbol in cells.items():
                self._check_symbol(symbol)
                if symbol != blank:
                    self._cells[int(position)] = symbol
        self._head = int(head)
        self._initial_cells = dict(self._cells)
        self._initial_head = self._head

    @classmethod
    def from_text(cls, text: str, blank: str = BLANK) -> "Tape":
        """Разбирает строку начальной ленты.

        Пробелы и табуляции игнорируются, чтобы запись можно было делать
        для читаемости. Символ «|» задаёт позицию головки: он стоит перед
        той ячейкой, которую головка читает. Например, «11|01» означает,
        что под головкой находится третий символ.
        """
        symbols: list[str] = []
        head: int | None = None
        marker_seen = False

        for character in text:
            if character.isspace():
                continue
            if character == HEAD_MARKER:
                if marker_seen:
                    raise TapeParseError(
                        "Маркер головки | должен встречаться в записи только один раз."
                    )
                marker_seen = True
                head = len(symbols)
                continue
            if len(character) != 1:
                raise TapeParseError("Каждая ячейка ленты должна содержать один символ.")
            symbols.append(character)

        cells = {position: symbol for position, symbol in enumerate(symbols)}
        if head is None:
            head = 0
        return cls(cells=cells, head=head, blank=blank)

    def _check_symbol(self, symbol: str) -> None:
        """Проверяет, что символ можно положить в одну ячейку."""
        if len(symbol) != 1:
            raise TapeParseError("Символ ячейки должен состоять ровно из одного знака.")
        if symbol == HEAD_MARKER:
            raise TapeParseError("Символ | зарезервирован для обозначения головки.")
        if symbol.isspace():
            raise TapeParseError("Пробел нельзя записать в ячейку, используйте _.")

    def read(self, position: int | None = None) -> str:
        """Читает символ в указанной позиции или под головкой."""
        if position is None:
            position = self._head
        return self._cells.get(position, self._blank)

    def write(self, symbol: str, position: int | None = None) -> str:
        """Записывает символ и возвращает то, что было в ячейке раньше.

        Если записывается пустой символ, ключ удаляется. Именно так машина
        «стирает» ячейку, не создавая бесконечный словарь пустых значений.
        """
        self._check_symbol(symbol)
        if position is None:
            position = self._head
        previous = self._cells.get(position, self._blank)
        if symbol == self._blank:
            self._cells.pop(position, None)
        else:
            self._cells[position] = symbol
        return previous

    def move(self, direction: str) -> int:
        """Двигает головку влево, вправо или оставляет на месте.

        Направление приходит из правила в верхнем регистре: L, R или N.
        Метод возвращает новую позицию головки, чтобы интерфейсу было
        удобно сразу обновить подпись под лентой.
        """
        direction = direction.upper()
        if direction == "L":
            self._head -= 1
        elif direction == "R":
            self._head += 1
        elif direction == "N":
            pass
        else:
            raise ValueError(f"Неизвестное направление сдвига: {direction}")
        return self._head

    def reset(self) -> None:
        """Возвращает ленту и головку в состояние на момент создания."""
        self._cells = dict(self._initial_cells)
        self._head = self._initial_head

    def copy(self) -> "Tape":
        """Создаёт независимую копию ленты.

        Копия нужна исполнителю: он не должен менять объект, который
        интерфейс хранит как исходную ленту для кнопки «Сброс».
        """
        return Tape(cells=dict(self._cells), head=self._head, blank=self._blank)

    def snapshot(self) -> dict[int, str]:
        """Возвращает копию словаря непустых ячеек."""
        return dict(self._cells)

    def visible_cells(self, start: int, count: int) -> list[tuple[int, str]]:
        """Готовит данные для рисования окна ленты.

        Возвращает пары «позиция — символ» для count подряд идущих ячеек.
        Пустые ячейки тоже попадают в результат, иначе на экране были бы
        дырки вместо ровного ряда.
        """
        return [(position, self.read(position)) for position in range(start, start + count)]

    def nonblank_bounds(self) -> tuple[int, int]:
        """Возвращает границы непустой части ленты.

        Если на ленте нет ни одного символа, обе границы совпадают с
        позицией головки. Метод помогает при сохранении ленты в текст.
        """
        if not self._cells:
            return self._head, self._head
        return min(self._cells), max(self._cells)

    def to_text(self, with_marker: bool = True) -> str:
        """Собирает ленту обратно в строку.

        Пустые ячейки внутри непустого участка записываются подчёркиванием.
        Если with_marker истинно, перед позицией головки вставляется «|».
        """
        left, right = self.nonblank_bounds()
        left = min(left, self._head)
        right = max(right, self._head)
        characters: list[str] = []
        for position in range(left, right + 1):
            if with_marker and position == self._head:
                characters.append(HEAD_MARKER)
            characters.append(self.read(position))
        if with_marker and self._head > right:
            characters.append(HEAD_MARKER)
        return "".join(characters)

    @property
    def head(self) -> int:
        """Текущая позиция головки."""
        return self._head

    @property
    def blank(self) -> str:
        """Символ, которым обозначается пустая ячейка."""
        return self._blank

    @property
    def cell_count(self) -> int:
        """Количество непустых ячеек, которые реально хранятся в памяти."""
        return len(self._cells)

    def __len__(self) -> int:
        """Позволяет узнать число непустых ячеек через len(tape)."""
        return len(self._cells)

    def __repr__(self) -> str:
        """Короткое представление ленты для отладки и тестов."""
        return f"Tape(head={self._head}, cells={self._cells!r})"
