"""
Integrantes do grupo: Gustavo Klinfuss da Silva - Github: GustavoKlinfuss
Nome do grupo no Canvas: RA1 31
"""

import math
from typing import Any


class ExecutionError(Exception):
    pass


OPERADORES_BINARIOS = {"+", "-", "*", "/", "//", "%", "^"}
KEYWORD_RES = "RES"


def executarExpressao(tokens: list[str]) -> list[float]:
    expressoes = _agrupar_programa(tokens)
    memoria: dict[str, float] = {}
    resultados: list[float] = []

    for expr in expressoes:
        resultado = _avaliar_expressao(expr, memoria, resultados)
        resultados.append(resultado)

    return resultados


def _agrupar_programa(tokens: list[str]) -> list[Any]:
    expressoes = []
    indice = 0

    while indice < len(tokens):
        expr, indice = _ler_expressao(tokens, indice)
        expressoes.append(expr)

    return expressoes


def _ler_expressao(tokens: list[str], indice: int) -> tuple[list[Any], int]:
    if indice >= len(tokens):
        raise ExecutionError("Fim inesperado da entrada.")

    if tokens[indice] != "(":
        raise ExecutionError(f"Esperado '(', encontrado: {tokens[indice]}")

    indice += 1
    atual: list[Any] = []

    while indice < len(tokens):
        token = tokens[indice]

        if token == "(":
            subexpr, indice = _ler_expressao(tokens, indice)
            atual.append(subexpr)
        elif token == ")":
            indice += 1
            return atual, indice
        else:
            atual.append(token)
            indice += 1

    raise ExecutionError("Esperado ')' para fechar expressao.")


def _avaliar_expressao(
    expr: Any,
    memoria: dict[str, float],
    resultados: list[float]
) -> float:
    if not isinstance(expr, list) or len(expr) == 0:
        raise ExecutionError("Expressao invalida ou vazia.")

    if len(expr) == 1:
        return _avaliar_item(expr[0], memoria, resultados)

    if len(expr) == 2 and expr[1] == KEYWORD_RES:
        deslocamento = _validar_inteiro_nao_negativo(expr[0], "RES")
        return _obter_resultado_anterior(deslocamento, resultados)

    if len(expr) == 2 and _eh_identificador(expr[1]) and expr[1] != KEYWORD_RES:
        valor = _avaliar_item(expr[0], memoria, resultados)
        memoria[expr[1]] = valor
        return valor

    pilha: list[float] = []

    for item in expr:
        if isinstance(item, list):
            pilha.append(_avaliar_expressao(item, memoria, resultados))
            continue

        if _eh_numero(item):
            pilha.append(float(item))
            continue

        if _eh_identificador(item) and item != KEYWORD_RES:
            pilha.append(memoria.get(item, 0.0))
            continue

        if item in OPERADORES_BINARIOS:
            if len(pilha) < 2:
                raise ExecutionError(
                    f"Operandos insuficientes para operador '{item}'."
                )

            direita = pilha.pop()
            esquerda = pilha.pop()
            pilha.append(_aplicar_operador(item, esquerda, direita))
            continue

        raise ExecutionError(f"Token invalido durante a execucao: {item}")

    if len(pilha) != 1:
        raise ExecutionError(
            f"Expressao invalida. Profundidade final da pilha: {len(pilha)}"
        )

    return pilha[0]


def _avaliar_item(
    item: Any,
    memoria: dict[str, float],
    resultados: list[float]
) -> float:
    if isinstance(item, list):
        return _avaliar_expressao(item, memoria, resultados)

    if _eh_numero(item):
        return float(item)

    if _eh_identificador(item) and item != KEYWORD_RES:
        return memoria.get(item, 0.0)

    raise ExecutionError(f"Item invalido na expressao: {item}")


def _aplicar_operador(op: str, esquerda: float, direita: float) -> float:
    if op == "+":
        return esquerda + direita
    if op == "-":
        return esquerda - direita
    if op == "*":
        return esquerda * direita
    if op == "/":
        return esquerda / direita
    if op == "//":
        return float(math.floor(esquerda / direita))
    if op == "%":
        quociente = math.floor(esquerda / direita)
        return esquerda - (quociente * direita)
    if op == "^":
        expoente = _validar_inteiro_positivo(direita, "^")
        return esquerda ** expoente

    raise ExecutionError(f"Operador nao suportado: {op}")


def _obter_resultado_anterior(
    deslocamento: int,
    resultados: list[float]
) -> float:
    if not resultados:
        raise ExecutionError("RES requer pelo menos um resultado anterior.")

    indice = len(resultados) - deslocamento
    if deslocamento == 0:
        indice = len(resultados) - 1

    if indice < 0 or indice >= len(resultados):
        raise ExecutionError(
            f"RES referencia uma linha inexistente: {deslocamento}"
        )

    return resultados[indice]


def _validar_inteiro_nao_negativo(valor: Any, contexto: str) -> int:
    if isinstance(valor, list):
        raise ExecutionError(f"{contexto} requer um literal inteiro.")

    if not _eh_numero(valor):
        raise ExecutionError(f"{contexto} requer um literal numerico.")

    numero = float(valor)
    if not numero.is_integer() or numero < 0:
        raise ExecutionError(
            f"{contexto} requer um inteiro nao negativo: {valor}"
        )

    return int(numero)


def _validar_inteiro_positivo(valor: float, contexto: str) -> int:
    if not float(valor).is_integer() or valor <= 0:
        raise ExecutionError(
            f"{contexto} requer um expoente inteiro positivo: {valor}"
        )

    return int(valor)


def _eh_numero(valor: Any) -> bool:
    if not isinstance(valor, str):
        return False

    try:
        float(valor)
        return True
    except ValueError:
        return False


def _eh_identificador(valor: Any) -> bool:
    return isinstance(valor, str) and valor.isidentifier()
