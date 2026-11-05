"""Ядро интерпретатора машины Тьюринга.

Пакет не зависит от Tkinter: его можно использовать в тестах и в консольных
сценариях. Интерфейс обращается только к классам Tape, Program и Machine.
"""

from .errors import ProgramSyntaxError, TapeParseError, TuringError
from .machine import Machine, TraceEntry
from .program import Program, Rule
from .tape import Tape

__all__ = [
    "Machine",
    "Program",
    "ProgramSyntaxError",
    "Rule",
    "Tape",
    "TapeParseError",
    "TraceEntry",
    "TuringError",
]
