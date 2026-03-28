from token_types import Token, TokenType


class LexicalError(Exception):
    pass


def parseExpressao(linha: str, tokens: list[Token], line_number: int = 1) -> list[Token]:
    """
    Analisa uma linha e adiciona tokens à lista recebida. Retorna a própria lista.
    """

    i = 0
    n = len(linha)

    def estado_inicial(index: int) -> int:
        if index >= n:
            return index

        ch = linha[index]

        if ch in (" ", "\t", "\r", "\n"):
            return index + 1

        if ch == "(":
            tokens.append(Token(TokenType.LPAREN, ch, line_number, index + 1))
            return index + 1

        if ch == ")":
            tokens.append(Token(TokenType.RPAREN, ch, line_number, index + 1))
            return index + 1

        if ch.isdigit():
            return estado_numero(index)

        if ch in "+-*%^/":
            return estado_operador(index)

        if "A" <= ch <= "Z":
            return estado_identificador(index)

        raise LexicalError(
            f"Linha {line_number}, coluna {index + 1}: caractere inválido '{ch}'"
        )

    def estado_numero(index: int) -> int:
        start = index
        saw_dot = False

        while index < n:
            ch = linha[index]
            if ch.isdigit():
                index += 1
                continue
            if ch == ".":
                if saw_dot:
                    raise LexicalError(
                        f"Linha {line_number}, coluna {index + 1}: número malformado"
                    )
                saw_dot = True
                index += 1
                continue
            break

        lexema = linha[start:index]

        if lexema.endswith("."):
            raise LexicalError(
                f"Linha {line_number}, coluna {index}: número malformado '{lexema}'"
            )

        tokens.append(Token(TokenType.NUMBER, lexema, line_number, start + 1))
        return index

    def estado_operador(index: int) -> int:
        start = index
        ch = linha[index]

        if ch == "/":
            if index + 1 < n and linha[index + 1] == "/":
                tokens.append(Token(TokenType.OPERATOR, "//", line_number, start + 1))
                return index + 2
            tokens.append(Token(TokenType.OPERATOR, "/", line_number, start + 1))
            return index + 1

        if ch in "+-*%^":
            tokens.append(Token(TokenType.OPERATOR, ch, line_number, start + 1))
            return index + 1

        raise LexicalError(
            f"Linha {line_number}, coluna {index + 1}: operador inválido '{ch}'"
        )

    def estado_identificador(index: int) -> int:
        start = index

        while index < n and "A" <= linha[index] <= "Z":
            index += 1

        lexema = linha[start:index]

        if lexema == "RES":
            tokens.append(Token(TokenType.KEYWORD_RES, lexema, line_number, start + 1))
        else:
            tokens.append(Token(TokenType.IDENTIFIER, lexema, line_number, start + 1))

        return index

    while i < n:
        i = estado_inicial(i)

    _validar_parenteses(tokens, line_number)
    return tokens


def _validar_parenteses(tokens: list[Token], line_number: int) -> None:
    saldo = 0
    for token in tokens:
        if token.line != line_number:
            continue
        if token.type == TokenType.LPAREN:
            saldo += 1
        elif token.type == TokenType.RPAREN:
            saldo -= 1
            if saldo < 0:
                raise LexicalError(
                    f"Linha {line_number}: parênteses desbalanceados"
                )

    if saldo != 0:
        raise LexicalError(f"Linha {line_number}: parênteses desbalanceados")