"""Тесты разбора таблицы переходов."""

import pytest

from turing.errors import ProgramSyntaxError
from turing.program import Program, Rule


def test_parse_simple_program() -> None:
    """Одна строка превращается в одно правило с нужными полями."""
    program = Program.parse("q0 1 -> q1 0 R")
    assert program.rule_count == 1
    rule = program.rules[0]
    assert rule.state == "q0"
    assert rule.read == "1"
    assert rule.write == "0"
    assert rule.move == "R"
    assert rule.next_state == "q1"


def test_parse_skips_comments_and_blank_lines() -> None:
    """Комментарии и пустые строки не считаются правилами."""
    text = "# комментарий\n\nq0 1 -> q1 0 R\n\n# ещё комментарий\n"
    program = Program.parse(text)
    assert program.rule_count == 1


def test_parse_inline_comment() -> None:
    """Комментарий после правила не мешает разбору."""
    program = Program.parse("q0 1 -> q1 0 R  # перейти вправо")
    assert program.rules[0].next_state == "q1"


def test_parse_unicode_arrow() -> None:
    """Стрелка → поддерживается наравне с ->."""
    program = Program.parse("q0 1 → q1 0 L")
    assert program.rules[0].move == "L"


def test_parse_is_case_insensitive() -> None:
    """Состояния и буквы сдвига можно писать в любом регистре."""
    program = Program.parse("Q0 1 -> QZ 0 r")
    rule = program.rules[0]
    assert rule.state == "q0"
    assert rule.next_state == "qz"
    assert rule.move == "R"


def test_duplicate_rule_reports_line() -> None:
    """Два правила для одной пары — ошибка с номером второй строки."""
    text = "q0 1 -> q1 0 R\nq0 1 -> q2 0 L"
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse(text)
    assert error.value.line_number == 2
    assert "уже задано" in str(error.value)


def test_missing_arrow_reports_line() -> None:
    """Без стрелки нельзя понять, где левая и правая части правила."""
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse("q0 1 q1 0 R")
    assert error.value.line_number == 1
    assert "стрелка" in str(error.value)


def test_two_arrows_is_error() -> None:
    """Две стрелки в одной строке тоже считаются опечаткой."""
    with pytest.raises(ProgramSyntaxError):
        Program.parse("q0 1 -> q1 -> 0 R")


def test_left_part_needs_two_tokens() -> None:
    """Слева должны быть ровно состояние и символ."""
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse("q0 -> q1 0 R")
    assert "Слева" in str(error.value)


def test_right_part_needs_three_tokens() -> None:
    """Справа нужны состояние, символ и сдвиг."""
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse("q0 1 -> q1 0")
    assert "Справа" in str(error.value)


def test_invalid_move_is_error() -> None:
    """Сдвиг может быть только L, R или N."""
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse("q0 1 -> q1 0 X")
    assert "Сдвиг" in str(error.value)


def test_multichar_symbol_is_error() -> None:
    """Символ из двух знаков не помещается в ячейку."""
    with pytest.raises(ProgramSyntaxError):
        Program.parse("q0 10 -> q1 0 R")


def test_bad_state_character_is_error() -> None:
    """В имени состояния допустимы буквы, цифры, _ и !."""
    with pytest.raises(ProgramSyntaxError):
        Program.parse("q0? 1 -> q1 0 R")


def test_state_cannot_start_with_digit() -> None:
    """Имя состояния должно начинаться с буквы или подчёркивания."""
    with pytest.raises(ProgramSyntaxError):
        Program.parse("0q 1 -> q1 0 R")


def test_empty_program_is_error() -> None:
    """Пустая программа не может ничего выполнить."""
    with pytest.raises(ProgramSyntaxError) as error:
        Program.parse("# только комментарий\n\n")
    assert error.value.line_number == 0


def test_find_existing_rule() -> None:
    """Поиск возвращает правило для пары состояние-символ."""
    program = Program.parse("q0 1 -> q1 0 R")
    rule = program.find("q0", "1")
    assert rule is not None
    assert rule.next_state == "q1"


def test_find_missing_rule() -> None:
    """Для неизвестной пары возвращается None."""
    program = Program.parse("q0 1 -> q1 0 R")
    assert program.find("q0", "0") is None


def test_states_are_sorted() -> None:
    """Список состояний не зависит от порядка строк."""
    program = Program.parse("q2 1 -> q1 0 R\nq1 1 -> q0 0 L")
    assert program.states() == ["q0", "q1", "q2"]


def test_qz_is_halt_state() -> None:
    """Классическое qz считается остановом."""
    program = Program.parse("q0 1 -> qz 0 R")
    assert program.is_halt_state("qz")


def test_qz_prefix_is_halt_state() -> None:
    """Имена qz_less, qz_equal и подобные тоже означают останов."""
    program = Program.parse("q0 1 -> qz_less 0 R")
    assert program.is_halt_state("qz_less")


def test_q_exclamation_is_halt_state() -> None:
    """Запись q! из учебников поддерживается."""
    program = Program.parse("q0 1 -> q! 0 R")
    assert program.is_halt_state("q!")


def test_regular_state_is_not_halt() -> None:
    """Обычное рабочее состояние не считается остановом."""
    program = Program.parse("q0 1 -> q1 0 R")
    assert not program.is_halt_state("q1")


def test_rule_as_text() -> None:
    """Правило умеет записываться обратно в строку."""
    rule = Rule("q0", "1", "0", "R", "q1", 3)
    assert rule.as_text() == "q0 1 -> q1 0 R"


def test_program_len() -> None:
    """len программы равен числу правил."""
    program = Program.parse("q0 1 -> q1 0 R\nq1 0 -> qz 1 N")
    assert len(program) == 2


def test_constructor_rejects_duplicates() -> None:
    """Проверка повторов работает и при создании из готовых правил."""
    rules = [
        Rule("q0", "1", "0", "R", "q1", 1),
        Rule("q0", "1", "1", "L", "q2", 2),
    ]
    with pytest.raises(ProgramSyntaxError):
        Program(rules)


def test_initial_state_is_lowercase() -> None:
    """Начальное состояние хранится в нижнем регистре."""
    program = Program.parse("q0 1 -> q1 0 R")
    assert program.initial_state == "q0"


def test_blank_symbol_is_allowed() -> None:
    """Подчёркивание обозначает пустую ячейку и допустимо в правилах."""
    program = Program.parse("q0 _ -> qz _ N")
    assert program.find("q0", "_") is not None
