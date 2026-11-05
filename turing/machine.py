"""Исполнитель машины Тьюринга и журнал выполненных шагов.

Класс Machine связывает программу и ленту: находит подходящее правило,
меняет символ, двигает головку и запоминает всё, что произошло. Интерфейс
вызывает step() по кнопке или по таймеру и показывает полученную запись.
"""

from __future__ import annotations

from dataclasses import dataclass

from .program import Program
from .tape import Tape

# Внутренние состояния исполнителя. В интерфейсе они переводятся на русский.
STATUS_READY = "ready"
STATUS_RUNNING = "running"
STATUS_HALTED = "halted"
STATUS_STUCK = "stuck"
STATUS_LIMIT = "limit"

FINISHED_STATUSES = (STATUS_HALTED, STATUS_STUCK, STATUS_LIMIT)


@dataclass
class TraceEntry:
    """Одна строка журнала выполнения.

    Хранит состояние до шага, прочитанный символ, запись, сдвиг и состояние
    после шага. Отдельное поле note поясняет служебные строки: останов по
    достижению qz, отсутствие правила или срабатывание лимита.
    """

    step: int
    state_before: str
    read_symbol: str
    write_symbol: str | None
    move: str | None
    state_after: str
    head_before: int
    head_after: int
    line_number: int = 0
    note: str = ""

    @property
    def move_text(self) -> str:
        """Переводит букву сдвига в понятное русское слово."""
        if self.move == "L":
            return "влево"
        if self.move == "R":
            return "вправо"
        if self.move == "N":
            return "на месте"
        return "—"

    @property
    def is_stop_row(self) -> bool:
        """Показывает, является ли строка служебной записью об остановке."""
        return self.write_symbol is None


class Machine:
    """Пошаговый исполнитель машины Тьюринга.

    Получает готовую программу и ленту, хранит копию исходной ленты для
    сброса и ведёт журнал. Один вызов step() выполняет ровно один переход.
    Ограничитель шагов защищает интерфейс от бесконечных программ.
    """

    def __init__(self, program: Program, tape: Tape, max_steps: int = 1000) -> None:
        """Создаёт исполнитель и запоминает начальное состояние.

        Лента копируется, чтобы кнопка «Сброс» могла вернуть её к исходному
        виду. Предел шагов должен быть положительным: нулевой лимит не дал бы
        машине сделать ни одного перехода.
        """
        if max_steps < 1:
            raise ValueError("Лимит шагов должен быть не меньше единицы.")
        self.program = program
        self.max_steps = int(max_steps)
        self._initial_tape = tape.copy()
        self._initial_state = program.initial_state
        self.tape = tape.copy()
        self.state = self._initial_state
        self.steps = 0
        self.history: list[TraceEntry] = []
        self.status = STATUS_READY
        self.stop_message = "Машина готова к запуску."

    @property
    def current_symbol(self) -> str:
        """Символ, который головка видит прямо сейчас."""
        return self.tape.read()

    @property
    def can_step(self) -> bool:
        """Можно ли сделать ещё один шаг."""
        return self.status not in FINISHED_STATUSES

    @property
    def is_finished(self) -> bool:
        """Останавливалась ли машина по любой причине."""
        return self.status in FINISHED_STATUSES

    @property
    def status_text(self) -> str:
        """Короткая подпись состояния для индикатора в окне."""
        if self.status == STATUS_READY:
            return "Готово"
        if self.status == STATUS_RUNNING:
            return "Выполняется"
        if self.status == STATUS_HALTED:
            return f"Останов: {self.state}"
        if self.status == STATUS_STUCK:
            return "Нет правила"
        return "Лимит шагов"

    def next_rule(self):
        """Возвращает правило, которое выполнится следующим, или None.

        Интерфейс подсвечивает это правило в редакторе. Если машина уже
        остановлена, подсвечивать нечего.
        """
        if not self.can_step:
            return None
        return self.program.find(self.state, self.tape.read())

    def step(self) -> TraceEntry | None:
        """Выполняет один переход и возвращает запись журнала.

        Если правила для текущей пары нет, машина переходит в состояние
        «нет правила» и добавляет в журнал служебную строку. Если после шага
        достигнуто состояние останова, статус меняется на «останов». Когда
        число шагов доходит до лимита, статус становится «лимит шагов».
        """
        if not self.can_step:
            return None

        rule = self.program.find(self.state, self.tape.read())
        if rule is None:
            self.status = STATUS_STUCK
            self.stop_message = (
                f"Нет правила для пары ({self.state}, {self.tape.read()}). "
                "Машина остановилась."
            )
            stop_row = TraceEntry(
                step=self.steps,
                state_before=self.state,
                read_symbol=self.tape.read(),
                write_symbol=None,
                move=None,
                state_after=self.state,
                head_before=self.tape.head,
                head_after=self.tape.head,
                note="нет правила",
            )
            self.history.append(stop_row)
            return None

        head_before = self.tape.head
        read_symbol = self.tape.read()
        self.tape.write(rule.write)
        self.tape.move(rule.move)
        self.state = rule.next_state
        self.steps += 1

        entry = TraceEntry(
            step=self.steps,
            state_before=rule.state,
            read_symbol=read_symbol,
            write_symbol=rule.write,
            move=rule.move,
            state_after=rule.next_state,
            head_before=head_before,
            head_after=self.tape.head,
            line_number=rule.line_number,
        )
        self.history.append(entry)

        if self.program.is_halt_state(self.state):
            self.status = STATUS_HALTED
            entry.note = "останов"
            self.stop_message = f"Достигнуто состояние останова {self.state}."
        elif self.steps >= self.max_steps:
            self.status = STATUS_LIMIT
            entry.note = "лимит шагов"
            self.stop_message = (
                f"Достигнут лимит шагов ({self.max_steps}). "
                "Возможно, программа зациклилась."
            )
        else:
            self.status = STATUS_RUNNING
            self.stop_message = "Машина работает."
        return entry

    def run(self) -> list[TraceEntry]:
        """Выполняет шаги до останова, ошибки или лимита.

        Метод удобен в тестах и в консольных проверках. В окне он не
        используется: там каждый шаг запускается таймером, чтобы лента
        успевала плавно двигаться.
        """
        while self.can_step:
            entry = self.step()
            if entry is None:
                break
        return list(self.history)

    def reset(self) -> None:
        """Возвращает машину к исходной ленте, состоянию и пустому журналу."""
        self.tape = self._initial_tape.copy()
        self.state = self._initial_state
        self.steps = 0
        self.history = []
        self.status = STATUS_READY
        self.stop_message = "Машина готова к запуску."

    def __repr__(self) -> str:
        """Короткое представление исполнителя для отладки."""
        return (
            f"Machine(state={self.state!r}, steps={self.steps}, "
            f"status={self.status!r})"
        )
