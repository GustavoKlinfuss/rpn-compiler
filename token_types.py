from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    LPAREN = 1
    RPAREN = 2
    NUMBER = 3
    OPERATOR = 4
    IDENTIFIER = 5
    KEYWORD_RES = 6


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int