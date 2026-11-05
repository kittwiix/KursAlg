"""Тесты ленты и головки машины Тьюринга."""

import pytest

from turing.errors import TapeParseError
from turing.tape import BLANK, Tape


def test_new_tape_is_blank() -> None:
    """Новая лента не содержит символов, а головка стоит в нулевой позиции."""
    tape = Tape()
    assert tape.read() == BLANK
    assert tape.head == 0
    assert tape.cell_count == 0


def test_write_and_read() -> None:
    """Запись символа сохраняется в указанной ячейке."""
    tape = Tape()
    previous = tape.write("1", position=3)
    assert previous == BLANK
    assert tape.read(3) == "1"
    assert tape.cell_count == 1


def test_write_blank_removes_cell() -> None:
    """Запись пустого символа удаляет ячейку из словаря."""
    tape = Tape(cells={2: "1"})
    previous = tape.write(BLANK, position=2)
    assert previous == "1"
    assert tape.cell_count == 0


def test_move_left_right_and_stay() -> None:
    """Головка двигается влево, вправо и остаётся на месте."""
    tape = Tape(head=2)
    assert tape.move("L") == 1
    assert tape.move("R") == 2
    assert tape.move("N") == 2


def test_move_is_case_insensitive() -> None:
    """Буква сдвига может быть записана в нижнем регистре."""
    tape = Tape(head=0)
    assert tape.move("r") == 1


def test_invalid_move_raises() -> None:
    """Неизвестное направление сдвига — ошибка программиста."""
    with pytest.raises(ValueError):
        Tape().move("X")


def test_from_text_marker_at_start() -> None:
    """Черта в начале строки ставит головку на первый символ."""
    tape = Tape.from_text("|111")
    assert tape.head == 0
    assert tape.read() == "1"
    assert tape.to_text() == "|111"


def test_from_text_marker_in_middle() -> None:
    """Черта в середине задаёт позицию конкретной ячейки."""
    tape = Tape.from_text("11|01")
    assert tape.head == 2
    assert tape.read() == "0"


def test_from_text_marker_at_end() -> None:
    """Черта в конце ставит головку на пустую ячейку после ленты."""
    tape = Tape.from_text("111|")
    assert tape.head == 3
    assert tape.read() == BLANK


def test_from_text_without_marker() -> None:
    """Без маркера головка остаётся в нулевой позиции."""
    tape = Tape.from_text("101")
    assert tape.head == 0
    assert tape.read() == "1"


def test_from_text_ignores_spaces() -> None:
    """Пробелы в записи ленты нужны только для читаемости."""
    tape = Tape.from_text("1 1 | 0 1")
    assert tape.head == 2
    assert tape.read() == "0"
    assert tape.cell_count == 4


def test_from_text_rejects_two_markers() -> None:
    """Два маркера головки — понятная ошибка разбора."""
    with pytest.raises(TapeParseError, match="только один раз"):
        Tape.from_text("1|1|0")


def test_from_text_empty_string() -> None:
    """Пустая строка даёт пустую ленту с головкой в нуле."""
    tape = Tape.from_text("")
    assert tape.head == 0
    assert tape.cell_count == 0


def test_copy_is_independent() -> None:
    """Изменение копии не меняет исходную ленту."""
    original = Tape.from_text("|101")
    copy = original.copy()
    copy.write("0")
    copy.move("R")
    assert original.read() == "1"
    assert original.head == 0
    assert copy.read(1) == "0"


def test_reset_restores_initial_state() -> None:
    """Сброс возвращает и символы, и позицию головки."""
    tape = Tape.from_text("|10")
    tape.write("0")
    tape.move("R")
    tape.write("1")
    tape.reset()
    assert tape.to_text() == "|10"
    assert tape.head == 0


def test_snapshot_returns_copy() -> None:
    """Снимок можно менять, не затрагивая саму ленту."""
    tape = Tape(cells={0: "1"})
    snapshot = tape.snapshot()
    snapshot[0] = "0"
    assert tape.read(0) == "1"


def test_visible_cells_includes_blanks() -> None:
    """Для рисования возвращается ровный ряд, включая пустые ячейки."""
    tape = Tape(cells={0: "1"})
    cells = tape.visible_cells(-1, 3)
    assert cells == [(-1, BLANK), (0, "1"), (1, BLANK)]


def test_to_text_with_marker() -> None:
    """Текст ленты собирается с маркером в нужном месте."""
    tape = Tape.from_text("|101")
    tape.move("R")
    assert tape.to_text() == "1|01"


def test_to_text_without_marker() -> None:
    """При сохранении маркер можно отключить."""
    tape = Tape.from_text("|101")
    assert tape.to_text(with_marker=False) == "101"


def test_len_returns_nonblank_cells() -> None:
    """len показывает число непустых ячеек, а не длину бесконечной ленты."""
    tape = Tape(cells={0: "1", 5: "0"})
    assert len(tape) == 2


def test_blank_must_be_single_character() -> None:
    """Обозначение пустой ячейки не может быть строкой из двух знаков."""
    with pytest.raises(ValueError):
        Tape(blank="__")


def test_write_rejects_two_characters() -> None:
    """В одну ячейку нельзя записать два символа."""
    with pytest.raises(TapeParseError):
        Tape().write("10")


def test_write_rejects_marker() -> None:
    """Черта зарезервирована для положения головки."""
    with pytest.raises(TapeParseError):
        Tape().write("|")


def test_write_rejects_space() -> None:
    """Пробел нельзя использовать как обычный символ."""
    with pytest.raises(TapeParseError):
        Tape().write(" ")
