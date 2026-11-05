"""Готовые примеры программ для демонстрации и проверки.

Каждый пример содержит текст программы, начальную ленту и короткое описание
для интерфейса. Примеры подобраны так, чтобы показать разные возможности
интерпретатора: вычисление, копирование, сравнение, стирание и защиту от
зацикливания.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    """Один готовый пример.

    Поле suggested_limit задаёт удобный лимит шагов. Для зацикленной
    программы он маленький, чтобы ограничитель сработал за пару секунд,
    а для остальных примеров оставлен запас.
    """

    key: str
    title: str
    description: str
    program_text: str
    tape_text: str
    suggested_limit: int = 1000


ADDITION_PROGRAM = """# Сложение унарных чисел: 1^n 0 1^m -> 1^(n+m)
# Ноль между блоками заменяется единицей, последняя единица стирается.
q0 1 -> q0 1 R
q0 0 -> q1 1 R
q1 1 -> q1 1 R
q1 _ -> q2 _ L
q2 1 -> qz _ N
"""

COPY_PROGRAM = """# Копирование унарного числа: 111 -> 1110111
# x — служебная метка уже обработанной единицы.
q0 1 -> q1 x R
q1 1 -> q1 1 R
q1 x -> q1 x R
q1 _ -> q2 0 R
q2 _ -> q3 1 N
q1b 1 -> q1b 1 R
q1b x -> q1b x R
q1b 0 -> q1b 0 R
q1b _ -> q3 1 N
q3 1 -> q3 1 L
q3 0 -> q3 0 L
q3 x -> q3 x L
q3 _ -> q4 _ R
q4 1 -> q0b 1 N
q4 x -> q4 x R
q4 0 -> q5 0 L
q0b 1 -> q1b x R
q5 x -> q5 1 L
q5 _ -> qz _ N
"""

COMPARE_PROGRAM = """# Сравнение двух унарных чисел: 1^a 0 1^b
# x и y — метки уже вычеркнутых единиц первого и второго числа.
# Результат виден в состоянии останова: qz_greater, qz_less или qz_equal.
q0 1 -> q1 x R
q0 x -> q0 x R
q0 0 -> q5 0 N
q1 1 -> q1 1 R
q1 x -> q1 x R
q1 0 -> q2 0 R
q2 1 -> q3 y L
q2 y -> q2 y R
q2 _ -> qz_greater _ N
q3 y -> q3 y L
q3 0 -> q4 0 L
q4 1 -> q4 1 L
q4 x -> q4 x L
q4 _ -> q0 _ R
q5 0 -> q5b 0 R
q5b y -> q5b y R
q5b 1 -> qz_less 1 N
q5b _ -> qz_equal _ N
"""

ERASE_PROGRAM = """# Стирание ленты до пустой
q0 1 -> q0 _ R
q0 0 -> q0 _ R
q0 _ -> qz _ N
"""

LOOP_PROGRAM = """# Заведомо зацикленная программа: головка бесконечно идёт вправо
q0 1 -> q0 1 R
q0 _ -> q0 _ R
"""


EXAMPLES: tuple[Example, ...] = (
    Example(
        key="addition",
        title="Сложение унарных чисел",
        description=(
            "На ленте 111|011 — числа 3 и 2. Ноль между блоками заменяется "
            "единицей, последняя единица стирается. Ожидается 11111, то есть 5."
        ),
        program_text=ADDITION_PROGRAM,
        tape_text="|111011",
        suggested_limit=1000,
    ),
    Example(
        key="copy",
        title="Копирование унарного числа",
        description=(
            "На ленте 111| — число 3. Машина дописывает справа через 0 его "
            "копию и возвращает метки x обратно в единицы. Ожидается 1110111."
        ),
        program_text=COPY_PROGRAM,
        tape_text="|111",
        suggested_limit=1000,
    ),
    Example(
        key="compare",
        title="Сравнение двух чисел",
        description=(
            "На ленте 111|011. Машина по одной вычёркивает единицы (метки x и y) "
            "и останавливается в состоянии qz_greater, qz_less или qz_equal."
        ),
        program_text=COMPARE_PROGRAM,
        tape_text="|111011",
        suggested_limit=1000,
    ),
    Example(
        key="erase",
        title="Стирание ленты",
        description=(
            "На ленте 111|011. Каждый символ заменяется на пустую ячейку, "
            "машина останавливается, когда справа больше нет единиц и нулей."
        ),
        program_text=ERASE_PROGRAM,
        tape_text="|111011",
        suggested_limit=1000,
    ),
    Example(
        key="loop",
        title="Зацикленная программа",
        description=(
            "На ленте 1|. Машина бесконечно движется вправо и не приходит "
            "в состояние останова. На 60-м шаге сработает ограничитель."
        ),
        program_text=LOOP_PROGRAM,
        tape_text="|1",
        suggested_limit=60,
    ),
)


def get_example(key: str) -> Example:
    """Находит пример по короткому ключу.

    Если ключа нет, выбрасывается KeyError. Интерфейс берёт ключи только
    из списка EXAMPLES, поэтому такая ситуация считается ошибкой программы,
    а не пользователя.
    """
    for example in EXAMPLES:
        if example.key == key:
            return example
    raise KeyError(f"Неизвестный пример: {key}")


def example_titles() -> list[tuple[str, str]]:
    """Возвращает пары «ключ — название» для выпадающего списка."""
    return [(example.key, example.title) for example in EXAMPLES]
