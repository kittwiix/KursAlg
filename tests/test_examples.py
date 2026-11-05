"""Тесты готовых примеров программ."""

import pytest

from turing.examples import EXAMPLES, example_titles, get_example
from turing.machine import Machine
from turing.program import Program
from turing.tape import Tape


def run_example(key: str, tape_text: str | None = None) -> Machine:
    """Запускает пример до конца и возвращает готовую машину."""
    example = get_example(key)
    text = tape_text if tape_text is not None else example.tape_text
    machine = Machine(
        Program.parse(example.program_text),
        Tape.from_text(text),
        example.suggested_limit,
    )
    machine.run()
    return machine


def test_all_examples_parse() -> None:
    """Каждый пример должен разбираться без ошибок."""
    for example in EXAMPLES:
        program = Program.parse(example.program_text)
        assert program.rule_count > 0


def test_example_keys_are_unique() -> None:
    """Ключи нужны для выпадающего списка, поэтому повторяться не должны."""
    keys = [example.key for example in EXAMPLES]
    assert len(keys) == len(set(keys))


def test_example_titles_returns_pairs() -> None:
    """Список названий содержит все примеры."""
    titles = dict(example_titles())
    assert len(titles) == len(EXAMPLES)
    assert "addition" in titles


def test_unknown_example_raises() -> None:
    """Неизвестный ключ — ошибка программы, а не пользователя."""
    with pytest.raises(KeyError):
        get_example("unknown")


def test_all_descriptions_are_filled() -> None:
    """У каждого примера есть описание для интерфейса."""
    for example in EXAMPLES:
        assert example.title
        assert example.description
        assert example.suggested_limit > 0


def test_addition_result() -> None:
    """Сложение 3 и 2 даёт пять единиц за восемь шагов."""
    machine = run_example("addition")
    assert machine.status == "halted"
    assert machine.steps == 8
    assert machine.tape.to_text(with_marker=False) == "11111_"


def test_copy_result() -> None:
    """Копирование 111 даёт 1110111."""
    machine = run_example("copy")
    assert machine.status == "halted"
    assert machine.tape.to_text(with_marker=False).lstrip("_") == "1110111"


def test_compare_greater() -> None:
    """3 больше 2 — машина останавливается в qz_greater."""
    machine = run_example("compare")
    assert machine.state == "qz_greater"
    assert machine.status == "halted"


def test_compare_less() -> None:
    """2 меньше 3 — машина останавливается в qz_less."""
    machine = run_example("compare", "|110111")
    assert machine.state == "qz_less"


def test_compare_equal() -> None:
    """3 равно 3 — машина останавливается в qz_equal."""
    machine = run_example("compare", "|1110111")
    assert machine.state == "qz_equal"


def test_compare_zero_and_number() -> None:
    """Пустое первое число меньше непустого."""
    machine = run_example("compare", "|0111")
    assert machine.state == "qz_less"


def test_compare_number_and_zero() -> None:
    """Непустое первое число больше пустого второго."""
    machine = run_example("compare", "|1110")
    assert machine.state == "qz_greater"


def test_erase_result_is_blank() -> None:
    """Стирание оставляет ленту пустой."""
    machine = run_example("erase")
    assert machine.status == "halted"
    assert machine.tape.cell_count == 0


def test_loop_hits_limit() -> None:
    """Зацикленный пример обязан остановиться по лимиту."""
    machine = run_example("loop")
    assert machine.status == "limit"
    assert machine.steps == 60


def test_example_count() -> None:
    """В интерфейсе должно быть ровно пять обязательных примеров."""
    assert len(EXAMPLES) == 5
