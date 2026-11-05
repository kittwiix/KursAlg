"""Таблица переходов машины Тьюринга и её разбор.

Программа машины — это набор правил вида «состояние, прочитанный символ →
новое состояние, записанный символ, сдвиг». В этом модуле правила хранятся
в удобном для исполнителя виде, а текст пользователя превращается в них
с понятными сообщениями об ошибках и номерами строк.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ProgramSyntaxError
from .tape import BLANK

# Так принято обозначать начальное состояние в учебных примерах.
INITIAL_STATE = "q0"

# Состояние qz считается остановом. Дополнительно я разрешаю имена qz_less,
# qz_equal и подобные: они удобны, когда результат сравнения виден в самом
# состоянии останова. Восклицательный знак q! поддерживается как синоним.
HALT_STATE = "qz"

# Допустимые направления сдвига головки.
MOVES = ("L", "R", "N")

ARROW = "->"


@dataclass(frozen=True)
class Rule:
    """Одно правило перехода.

    Поля соответствуют строке программы: q0 1 -> q1 0 R. Класс неизменяемый,
    потому что правило после разбора не должно меняться. Номер строки нужен
    интерфейсу для подсветки выполняемого правила и сообщений об ошибках.
    """

    state: str
    read: str
    write: str
    move: str
    next_state: str
    line_number: int = 0

    def key(self) -> tuple[str, str]:
        """Возвращает пару «состояние, символ», по которой ищется правило."""
        return self.state, self.read

    def as_text(self) -> str:
        """Записывает правило в том же формате, что и в редакторе."""
        return (
            f"{self.state} {self.read} -> "
            f"{self.next_state} {self.write} {self.move}"
        )


class Program:
    """Хранит правила переходов и умеет искать нужное правило.

    Экземпляр создаётся либо из списка готовых Rule, либо методом parse()
    из текста. Внутри правила лежат в словаре по паре (состояние, символ),
    поэтому поиск одного перехода занимает одинаковое время даже в большой
    таблице.
    """

    def __init__(
        self,
        rules: list[Rule],
        initial_state: str = INITIAL_STATE,
        halt_state: str = HALT_STATE,
    ) -> None:
        """Создаёт программу и проверяет, что правила не противоречат друг другу."""
        if not rules:
            raise ProgramSyntaxError(0, "В программе нет ни одного правила.")
        self._rules = list(rules)
        self._by_key: dict[tuple[str, str], Rule] = {}
        for rule in self._rules:
            key = rule.key()
            if key in self._by_key:
                previous = self._by_key[key]
                raise ProgramSyntaxError(
                    rule.line_number,
                    "Правило для пары "
                    f"({rule.state}, {rule.read}) уже задано в строке "
                    f"{previous.line_number}.",
                )
            self._by_key[key] = rule
        self.initial_state = initial_state.lower()
        self.halt_state = halt_state.lower()

    @classmethod
    def parse(cls, text: str) -> "Program":
        """Разбирает текст программы построчно.

        Пустые строки и строки, начинающиеся с #, пропускаются. Стрелку можно
        писать как «->», так и «→». Регистр состояний и букв L, R, N не важен:
        внутри всё приводится к нижнему регистру для состояний и к верхнему
        для сдвига. При ошибке выбрасывается ProgramSyntaxError с номером
        строки, чтобы интерфейс мог показать точное место.
        """
        rules: list[Rule] = []
        seen: dict[tuple[str, str], Rule] = {}

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue
            line = line.replace("→", ARROW)
            if line.count(ARROW) != 1:
                raise ProgramSyntaxError(
                    line_number,
                    "Не найдена стрелка ->. Пример правила: q0 1 -> q1 0 R.",
                )
            left, right = line.split(ARROW, 1)
            left_parts = left.split()
            right_parts = right.split()
            if len(left_parts) != 2:
                raise ProgramSyntaxError(
                    line_number,
                    "Слева от стрелки нужны состояние и символ, например q0 1.",
                )
            if len(right_parts) != 3:
                raise ProgramSyntaxError(
                    line_number,
                    "Справа от стрелки нужны новое состояние, символ и сдвиг, "
                    "например q1 0 R.",
                )

            state, read_symbol = left_parts
            next_state, write_symbol, move = right_parts
            state = cls._check_state(state, line_number)
            next_state = cls._check_state(next_state, line_number)
            read_symbol = cls._check_cell_symbol(read_symbol, line_number)
            write_symbol = cls._check_cell_symbol(write_symbol, line_number)
            move = move.upper()
            if move not in MOVES:
                raise ProgramSyntaxError(
                    line_number,
                    f"Сдвиг должен быть L, R или N, а записано «{move}».",
                )

            rule = Rule(
                state=state,
                read=read_symbol,
                write=write_symbol,
                move=move,
                next_state=next_state,
                line_number=line_number,
            )
            key = rule.key()
            if key in seen:
                previous = seen[key]
                raise ProgramSyntaxError(
                    line_number,
                    "Правило для пары "
                    f"({state}, {read_symbol}) уже задано в строке "
                    f"{previous.line_number}.",
                )
            seen[key] = rule
            rules.append(rule)

        if not rules:
            raise ProgramSyntaxError(0, "В программе нет ни одного правила.")
        return cls(rules)

    @staticmethod
    def _check_state(value: str, line_number: int) -> str:
        """Проверяет имя состояния и возвращает его в нижнем регистре.

        Имя может содержать буквы, цифры, подчёркивание и восклицательный
        знак. Восклицательный знак оставлен для записи останова q!, которую
        часто встречают в учебниках.
        """
        if not value:
            raise ProgramSyntaxError(line_number, "Имя состояния не может быть пустым.")
        cleaned = value.lower()
        for index, character in enumerate(cleaned):
            allowed = character.isalnum() or character == "_" or character == "!"
            if not allowed:
                raise ProgramSyntaxError(
                    line_number,
                    f"В имени состояния «{value}» есть недопустимый символ "
                    f"«{character}».",
                )
            if index == 0 and not (character.isalpha() or character == "_"):
                raise ProgramSyntaxError(
                    line_number,
                    "Имя состояния должно начинаться с буквы или подчёркивания.",
                )
        return cleaned

    @staticmethod
    def _check_cell_symbol(value: str, line_number: int) -> str:
        """Проверяет, что символ помещается в одну ячейку ленты."""
        if len(value) != 1:
            raise ProgramSyntaxError(
                line_number,
                f"Символ «{value}» должен состоять ровно из одного знака.",
            )
        if value == "|":
            raise ProgramSyntaxError(
                line_number,
                "Символ | зарезервирован для маркера головки в начальной ленте.",
            )
        if value.isspace():
            raise ProgramSyntaxError(
                line_number,
                "Пробел нельзя использовать как символ, для пустой ячейки есть _.",
            )
        return value

    def find(self, state: str, symbol: str) -> Rule | None:
        """Ищет правило для текущей пары «состояние, символ».

        Если правила нет, возвращает None. Исполнитель по этому признаку
        понимает, что машина остановилась из-за отсутствия перехода, и не
        путает такую остановку с достижением состояния qz.
        """
        return self._by_key.get((state.lower(), symbol))

    def is_halt_state(self, state: str) -> bool:
        """Проверяет, является ли состояние остановом.

        Остановом считаются qz, q!, а также имена, начинающиеся с qz.
        Благодаря этому пример сравнения может завершаться в qz_less,
        qz_equal или qz_greater, и результат будет виден прямо в состоянии.
        """
        name = state.lower()
        return name == self.halt_state or name == "q!" or name.startswith("qz")

    def states(self) -> list[str]:
        """Возвращает отсортированный список всех состояний программы."""
        found: set[str] = set()
        for rule in self._rules:
            found.add(rule.state)
            found.add(rule.next_state)
        return sorted(found)

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Возвращает правила в том порядке, в каком они записаны."""
        return tuple(self._rules)

    @property
    def rule_count(self) -> int:
        """Количество правил в программе."""
        return len(self._rules)

    def __len__(self) -> int:
        """Позволяет узнать число правил через len(program)."""
        return len(self._rules)

    def __repr__(self) -> str:
        """Короткое представление программы для отладки."""
        return f"Program(rules={len(self._rules)}, initial={self.initial_state!r})"
