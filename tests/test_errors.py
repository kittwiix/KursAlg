"""Тесты иерархии исключений и текстов сообщений."""

from turing.errors import (
    ProgramSyntaxError,
    StepLimitExceeded,
    TapeParseError,
    TuringError,
)


def test_program_error_has_line_number() -> None:
    """Ошибка разбора показывает номер строки."""
    error = ProgramSyntaxError(7, "Не найдена стрелка.")
    assert error.line_number == 7
    assert str(error) == "Строка 7: Не найдена стрелка."


def test_program_error_without_line() -> None:
    """Общая ошибка программы не добавляет «Строка 0»."""
    error = ProgramSyntaxError(0, "В программе нет правил.")
    assert str(error) == "В программе нет правил."


def test_tape_error_message() -> None:
    """Ошибка ленты сохраняет понятный текст."""
    error = TapeParseError("Два маркера головки.")
    assert str(error) == "Два маркера головки."


def test_step_limit_message_contains_limit() -> None:
    """Сообщение о лимите называет число шагов."""
    error = StepLimitExceeded(250)
    assert "250" in str(error)
    assert error.limit == 250


def test_all_errors_share_base_class() -> None:
    """Все ошибки можно поймать одним except TuringError."""
    assert issubclass(ProgramSyntaxError, TuringError)
    assert issubclass(TapeParseError, TuringError)
    assert issubclass(StepLimitExceeded, TuringError)
