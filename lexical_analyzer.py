from token_types import Token, TokenType


class LexicalError(Exception):
    pass

def parseExpressao(linha: str, tokens: list[str]) -> list[str]:
    i = 0
    n = len(linha)
    inicio = len(tokens)

    def estado_inicial(index: int) -> int:
        if index >= n:
            return index

        ch = linha[index]

        if ch in (" ", "\t", "\n", "\r"):
            return index + 1

        if ch == "(" or ch == ")":
            tokens.append(ch)
            return index + 1

        if ch.isdigit():
            return estado_numero(index)

        if ch in "+-*%^/":
            return estado_operador(index)

        if "A" <= ch <= "Z":
            return estado_identificador(index)

        raise LexicalError(f"Caractere inválido: {ch}")

    def estado_numero(index: int) -> int:
        start = index
        saw_dot = False

        while index < n:
            ch = linha[index]
            if ch.isdigit():
                index += 1
            elif ch == ".":
                if saw_dot:
                    raise LexicalError("Número malformado")
                saw_dot = True
                index += 1
            else:
                break

        lexema = linha[start:index]

        if lexema.endswith("."):
            raise LexicalError(f"Número malformado: {lexema}")

        tokens.append(lexema)
        return index

    def estado_operador(index: int) -> int:
        if linha[index] == "/" and index + 1 < n and linha[index + 1] == "/":
            tokens.append("//")
            return index + 2

        tokens.append(linha[index])
        return index + 1

    def estado_identificador(index: int) -> int:
        start = index

        while index < n and "A" <= linha[index] <= "Z":
            index += 1

        tokens.append(linha[start:index])
        return index

    while i < n:
        i = estado_inicial(i)

    validar_parenteses(tokens[inicio:])
    return tokens

def validar_parenteses(tokens: list[str]) -> None:
    saldo = 0

    for token in tokens:
        if token == "(":
            saldo += 1
        elif token == ")":
            saldo -= 1

            if saldo < 0:
                raise LexicalError("Parênteses desbalanceados")
    if saldo != 0:
        raise LexicalError("Parênteses desbalanceados")