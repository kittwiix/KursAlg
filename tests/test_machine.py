"""Тесты исполнителя машины Тьюринга."""

import pytest

from turing.machine import (
    STATUS_HALTED,
    STATUS_LIMIT,
    STATUS_READY,
    STATUS_RUNNING,
    STATUS_STUCK,
    Machine,
    TraceEntry,
)
from turing.program import Program
from turing.tape import Tape


def make_machine(program_text: str, tape_text: str, limit: int = 100) -> Machine:
    """Собирает машину из двух строк — так тесты остаются короткими."""
    return Machine(Program.parse(program_text), Tape.from_text(tape_text), limit)


def test_initial_status_is_ready() -> None:
    """До первого шага машина находится в состоянии «готово»."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    assert machine.status == STATUS_READY
    assert machine.steps == 0
    assert machine.can_step


def test_step_writes_symbol_and_moves() -> None:
    """Один шаг меняет символ, двигает головку и состояние."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    entry = machine.step()
    assert entry is not None
    assert machine.tape.read(0) == "0"
    assert machine.tape.head == 1
    assert machine.state == "q1"
    assert machine.steps == 1
    assert machine.status == STATUS_RUNNING


def test_trace_entry_fields() -> None:
    """Запись журнала хранит всё, что нужно для таблицы."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    entry = machine.step()
    assert entry is not None
    assert entry.step == 1
    assert entry.state_before == "q0"
    assert entry.read_symbol == "1"
    assert entry.write_symbol == "0"
    assert entry.move == "R"
    assert entry.state_after == "q1"
    assert entry.head_before == 0
    assert entry.head_after == 1
    assert entry.note == ""


def test_halt_on_qz() -> None:
    """Состояние qz останавливает машину, а запись помечается как останов."""
    machine = make_machine("q0 1 -> qz 0 N", "|1")
    entry = machine.step()
    assert machine.status == STATUS_HALTED
    assert machine.is_finished
    assert not machine.can_step
    assert entry is not None
    assert entry.note == "останов"


def test_halt_on_qz_prefix() -> None:
    """Состояния вида qz_less тоже считаются остановом."""
    machine = make_machine("q0 1 -> qz_less 0 N", "|1")
    machine.step()
    assert machine.status == STATUS_HALTED
    assert "qz_less" in machine.status_text


def test_missing_rule_stops_machine() -> None:
    """Если правила нет, машина останавливается и пишет служебную строку."""
    machine = make_machine("q0 1 -> q0 1 R", "|0")
    result = machine.step()
    assert result is None
    assert machine.status == STATUS_STUCK
    assert len(machine.history) == 1
    assert machine.history[0].note == "нет правила"
    assert machine.history[0].is_stop_row


def test_step_limit_stops_machine() -> None:
    """Бесконечная программа останавливается по лимиту шагов."""
    program = "q0 1 -> q0 1 R\nq0 _ -> q0 _ R"
    machine = make_machine(program, "|1", limit=3)
    machine.run()
    assert machine.steps == 3
    assert machine.status == STATUS_LIMIT
    assert machine.history[-1].note == "лимит шагов"


def test_halt_has_priority_over_limit() -> None:
    """Если последний разрешённый шаг ведёт в qz, это останов, а не лимит."""
    machine = make_machine("q0 1 -> qz 0 N", "|1", limit=1)
    machine.step()
    assert machine.status == STATUS_HALTED


def test_reset_restores_everything() -> None:
    """Сброс возвращает ленту, состояние, счётчик и журнал."""
    machine = make_machine("q0 1 -> q0 1 R", "|1")
    machine.step()
    machine.step()
    machine.reset()
    assert machine.steps == 0
    assert machine.state == "q0"
    assert machine.history == []
    assert machine.tape.head == 0
    assert machine.tape.read(0) == "1"
    assert machine.status == STATUS_READY


def test_run_returns_history() -> None:
    """run() выполняет программу до останова и возвращает журнал."""
    machine = make_machine("q0 1 -> q1 0 R\nq1 _ -> qz _ N", "|1")
    history = machine.run()
    assert len(history) == 2
    assert machine.status == STATUS_HALTED


def test_no_step_after_finish() -> None:
    """После останова step() ничего не делает."""
    machine = make_machine("q0 1 -> qz 0 N", "|1")
    machine.step()
    assert machine.step() is None


def test_next_rule_returns_upcoming_rule() -> None:
    """Следующее правило нужно для подсветки в редакторе."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    rule = machine.next_rule()
    assert rule is not None
    assert rule.next_state == "q1"


def test_next_rule_is_none_after_halt() -> None:
    """После останова подсвечивать нечего."""
    machine = make_machine("q0 1 -> qz 0 N", "|1")
    machine.step()
    assert machine.next_rule() is None


def test_current_symbol() -> None:
    """Свойство current_symbol показывает символ под головкой."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    assert machine.current_symbol == "1"
    machine.step()
    assert machine.current_symbol == "_"


def test_max_steps_must_be_positive() -> None:
    """Нулевой лимит не имеет смысла и запрещён."""
    with pytest.raises(ValueError):
        make_machine("q0 1 -> q1 0 R", "|1", limit=0)


def test_status_text_russian() -> None:
    """Подписи состояния предназначены для интерфейса."""
    machine = make_machine("q0 1 -> q1 0 R", "|1")
    assert machine.status_text == "Готово"
    machine.step()
    assert machine.status_text == "Выполняется"


def test_move_text() -> None:
    """Буквы сдвига переводятся в слова."""
    assert TraceEntry(1, "q0", "1", "0", "L", "q1", 0, -1).move_text == "влево"
    assert TraceEntry(1, "q0", "1", "0", "R", "q1", 0, 1).move_text == "вправо"
    assert TraceEntry(1, "q0", "1", "0", "N", "q1", 0, 0).move_text == "на месте"
    assert TraceEntry(1, "q0", "1", None, None, "q0", 0, 0).move_text == "—"


def test_head_positions_in_trace() -> None:
    """В журнале сохраняются позиции головки до и после шага."""
    machine = make_machine("q0 1 -> q1 0 L", "|1")
    entry = machine.step()
    assert entry is not None
    assert entry.head_before == 0
    assert entry.head_after == -1


def test_write_blank_in_step() -> None:
    """Правило может стирать ячейку."""
    machine = make_machine("q0 1 -> qz _ N", "|1")
    machine.step()
    assert machine.tape.read(0) == "_"
    assert machine.tape.cell_count == 0


def test_stop_message_contains_state() -> None:
    """Сообщение об останове называет состояние."""
    machine = make_machine("q0 1 -> qz 0 N", "|1")
    machine.step()
    assert "qz" in machine.stop_message


def test_stuck_message_contains_pair() -> None:
    """Сообщение об отсутствии правила показывает пару."""
    machine = make_machine("q0 1 -> q0 1 R", "|0")
    machine.step()
    assert "(q0, 0)" in machine.stop_message
