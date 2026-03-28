"""
Integrantes do grupo: Gustavo Klinfuss da Silva
Nome do grupo no Canvas: RA1 31
"""

import re
from dataclasses import dataclass
from typing import Any


class AssemblyGeneratorError(Exception):
    pass


OPERADORES_BINARIOS = {"+", "-", "*", "/", "//", "%", "^"}
KEY_RES = "RES"
TODOS_OPERADORES = OPERADORES_BINARIOS | {KEY_RES}


@dataclass
class ContextoAssembly:
    constantes: dict[str, str]
    variaveis: set[str]
    total_expressoes: int
    contador_constantes: int = 0
    contador_rotulos: int = 0


def gerarAssembly(tokens: list[str], caminho_saida: str) -> None:
    if not isinstance(tokens, list) or len(tokens) == 0:
        raise AssemblyGeneratorError("A lista de tokens está vazia.")

    expressoes = _agrupar_programa(tokens)
    contexto = ContextoAssembly(
        constantes={},
        variaveis=set(),
        total_expressoes=len(expressoes),
    )

    for expr in expressoes:
        _coletar_recursos(expr, contexto)

    linhas: list[str] = []
    linhas.extend(_gerar_cabecalho(contexto))
    linhas.extend(_gerar_codigo_principal(expressoes, contexto))

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def _agrupar_programa(tokens: list[str]) -> list[Any]:
    expressoes = []
    index = 0

    while index < len(tokens):
        expr, index = _ler_expressao(tokens, index)
        expressoes.append(expr)

    return expressoes


def _ler_expressao(tokens: list[str], index: int) -> tuple[list[Any], int]:
    if index >= len(tokens):
        raise AssemblyGeneratorError("Fim inesperado da entrada.")

    if tokens[index] != "(":
        raise AssemblyGeneratorError(
            f"Esperado '(', encontrado: {tokens[index]}"
        )

    index += 1
    atual: list[Any] = []

    while index < len(tokens):
        token = tokens[index]

        if token == "(":
            subexpr, index = _ler_expressao(tokens, index)
            atual.append(subexpr)
        elif token == ")":
            index += 1
            return atual, index
        else:
            atual.append(token)
            index += 1

    raise AssemblyGeneratorError("Esperado ')' para fechar expressão.")


def _coletar_recursos(expr: Any, contexto: ContextoAssembly) -> None:
    if isinstance(expr, list):
        for item in expr:
            _coletar_recursos(item, contexto)
        return

    if _eh_numero(expr):
        _obter_label_constante(expr, contexto)
        return

    if _eh_identificador(expr) and expr not in TODOS_OPERADORES:
        contexto.variaveis.add(expr)
        return

    if expr in TODOS_OPERADORES:
        return

    raise AssemblyGeneratorError(f"Token inválido encontrado: {expr}")


def _gerar_cabecalho(contexto: ContextoAssembly) -> list[str]:
    linhas: list[str] = [
        ".syntax unified",
        ".arch armv7-a",
        ".fpu neon-fp16",
        "",
        ".text",
        ".align 2",
        ".global _start",
        "",
        ".data",
        ".align 3",
        "__const_one:",
        "    .double 1.0",
        "",
    ]

    if contexto.constantes:
        for literal, label in contexto.constantes.items():
            linhas.append(f"{label}:")
            linhas.append(f"    .double {literal}")
    else:
        linhas.append("__dummy_const:")
        linhas.append("    .double 0.0")

    linhas.extend([
        "",
        ".bss",
        ".align 3",
    ])

    if contexto.variaveis:
        for nome in sorted(contexto.variaveis):
            linhas.append(f"{_label_variavel(nome)}:")
            linhas.append("    .space 8")

    linhas.append("__resultados:")
    linhas.append(f"    .space {max(contexto.total_expressoes, 1) * 8}")
    linhas.append("__result:")
    linhas.append("    .space 8")
    linhas.extend([
        "",
        ".text",
        ".align 2",
        "_start:",
        "",
    ])

    return linhas


def _gerar_codigo_principal(
    expressoes: list[Any],
    contexto: ContextoAssembly
) -> list[str]:
    linhas: list[str] = []

    for i, expr in enumerate(expressoes, start=1):
        linhas.append(f"    @ expressão {i}")
        linhas.extend(
            _compilar_expressao(expr, contexto, indice_expressao=i - 1, indent="    ")
        )
        linhas.append("    ldr r0, =__result")
        linhas.append("    vstr d0, [r0]")
        linhas.extend(_gerar_armazenamento_resultado(i - 1, "    "))
        linhas.append("")

    linhas.extend([
        "_halt:",
        "    b _halt",
    ])
    return linhas


def _compilar_expressao(
    expr: Any,
    contexto: ContextoAssembly,
    indice_expressao: int,
    indent: str = ""
) -> list[str]:
    if not isinstance(expr, list) or len(expr) == 0:
        raise AssemblyGeneratorError("Expressão inválida ou vazia.")

    if len(expr) == 1:
        return _compilar_item(expr[0], contexto, indice_expressao, indent)

    if len(expr) == 2 and expr[1] == KEY_RES:
        return _compilar_res(expr[0], indice_expressao, indent)

    if len(expr) == 2 and _eh_identificador(expr[1]) and expr[1] != KEY_RES:
        codigo = _compilar_item(expr[0], contexto, indice_expressao, indent)
        codigo.append(f"{indent}ldr r0, ={_label_variavel(expr[1])}")
        codigo.append(f"{indent}vstr d0, [r0]")
        return codigo

    return _compilar_rpn(expr, contexto, indice_expressao, indent)


def _compilar_item(
    item: Any,
    contexto: ContextoAssembly,
    indice_expressao: int,
    indent: str = ""
) -> list[str]:
    if isinstance(item, list):
        return _compilar_expressao(item, contexto, indice_expressao, indent)

    if _eh_numero(item):
        label = _obter_label_constante(item, contexto)
        return [
            f"{indent}ldr r0, ={label}",
            f"{indent}vldr d0, [r0]",
        ]

    if _eh_identificador(item) and item != KEY_RES:
        return [
            f"{indent}ldr r0, ={_label_variavel(item)}",
            f"{indent}vldr d0, [r0]",
        ]

    raise AssemblyGeneratorError(f"Item inválido na expressão: {item}")


def _compilar_res(
    deslocamento_literal: Any,
    indice_expressao: int,
    indent: str
) -> list[str]:
    deslocamento = _validar_res_literal(deslocamento_literal)
    indice_resultado = _indice_resultado_res(indice_expressao, deslocamento)
    deslocamento_bytes = indice_resultado * 8

    codigo = [f"{indent}ldr r0, =__resultados"]
    if deslocamento_bytes > 0:
        codigo.append(f"{indent}add r0, r0, #{deslocamento_bytes}")
    codigo.append(f"{indent}vldr d0, [r0]")
    return codigo


def _compilar_rpn(
    expr: list[Any],
    contexto: ContextoAssembly,
    indice_expressao: int,
    indent: str = ""
) -> list[str]:
    profundidade = 0
    codigo: list[str] = []

    for item in expr:
        if isinstance(item, list):
            codigo.extend(
                _compilar_expressao(item, contexto, indice_expressao, indent)
            )
            codigo.append(f"{indent}vpush {{d0}}")
            profundidade += 1
            continue

        if _eh_numero(item):
            label = _obter_label_constante(item, contexto)
            codigo.append(f"{indent}ldr r0, ={label}")
            codigo.append(f"{indent}vldr d0, [r0]")
            codigo.append(f"{indent}vpush {{d0}}")
            profundidade += 1
            continue

        if _eh_identificador(item) and item != KEY_RES:
            codigo.append(f"{indent}ldr r0, ={_label_variavel(item)}")
            codigo.append(f"{indent}vldr d0, [r0]")
            codigo.append(f"{indent}vpush {{d0}}")
            profundidade += 1
            continue

        if item in OPERADORES_BINARIOS:
            if profundidade < 2:
                raise AssemblyGeneratorError(
                    f"Operandos insuficientes para operador binário '{item}'."
                )

            codigo.extend(_compilar_operador_binario(item, contexto, indent))
            profundidade -= 1
            continue

        raise AssemblyGeneratorError(
            f"Token inválido durante a compilação: {item}"
        )

    if profundidade != 1:
        raise AssemblyGeneratorError(
            f"Expressão inválida. Profundidade final da pilha: {profundidade}"
        )

    codigo.append(f"{indent}vpop {{d0}}")
    return codigo


def _compilar_operador_binario(
    op: str,
    contexto: ContextoAssembly,
    indent: str = ""
) -> list[str]:
    codigo: list[str] = []

    if op in {"+", "-", "*", "/"}:
        codigo.append(f"{indent}vpop {{d1}}")
        codigo.append(f"{indent}vpop {{d0}}")

        if op == "+":
            codigo.append(f"{indent}vadd.f64 d0, d0, d1")
        elif op == "-":
            codigo.append(f"{indent}vsub.f64 d0, d0, d1")
        elif op == "*":
            codigo.append(f"{indent}vmul.f64 d0, d0, d1")
        else:
            codigo.append(f"{indent}vdiv.f64 d0, d0, d1")

        codigo.append(f"{indent}vpush {{d0}}")
        return codigo

    if op == "//":
        lbl_done = _novo_rotulo(contexto, "floor_done")
        codigo.extend([
            f"{indent}@ floor(left / right)",
            f"{indent}vpop {{d1}}",
            f"{indent}vpop {{d0}}",
            f"{indent}vdiv.f64 d2, d0, d1",
            f"{indent}vcvt.s32.f64 s0, d2",
            f"{indent}vcvt.f64.s32 d3, s0",
            f"{indent}vcmp.f64 d2, d3",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}beq {lbl_done}",
            f"{indent}vcmp.f64 d2, #0.0",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}bge {lbl_done}",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d4, [r0]",
            f"{indent}vsub.f64 d3, d3, d4",
            f"{lbl_done}:",
            f"{indent}vmov d0, d3",
            f"{indent}vpush {{d0}}",
        ])
        return codigo

    if op == "%":
        lbl_done = _novo_rotulo(contexto, "mod_floor_done")
        codigo.extend([
            f"{indent}@ left % right = left - floor(left/right) * right",
            f"{indent}vpop {{d1}}",
            f"{indent}vpop {{d0}}",
            f"{indent}vmov d5, d0",
            f"{indent}vmov d6, d1",
            f"{indent}vdiv.f64 d2, d0, d1",
            f"{indent}vcvt.s32.f64 s0, d2",
            f"{indent}vcvt.f64.s32 d3, s0",
            f"{indent}vcmp.f64 d2, d3",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}beq {lbl_done}",
            f"{indent}vcmp.f64 d2, #0.0",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}bge {lbl_done}",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d4, [r0]",
            f"{indent}vsub.f64 d3, d3, d4",
            f"{lbl_done}:",
            f"{indent}vmul.f64 d3, d3, d6",
            f"{indent}vsub.f64 d0, d5, d3",
            f"{indent}vpush {{d0}}",
        ])
        return codigo

    if op == "^":
        lbl_loop = _novo_rotulo(contexto, "pow_loop")
        lbl_done = _novo_rotulo(contexto, "pow_done")
        lbl_after_loop = _novo_rotulo(contexto, "pow_after_loop")

        codigo.extend([
            f"{indent}@ potência com expoente inteiro positivo",
            f"{indent}vpop {{d1}}",
            f"{indent}vpop {{d0}}",
            f"{indent}vmov d2, d0",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d0, [r0]",
            f"{indent}vcvt.s32.f64 s0, d1",
            f"{indent}vmov r1, s0",
            f"{indent}cmp r1, #1",
            f"{indent}blt {lbl_done}",
            f"{lbl_loop}:",
            f"{indent}vmul.f64 d0, d0, d2",
            f"{indent}subs r1, r1, #1",
            f"{indent}bne {lbl_loop}",
            f"{lbl_after_loop}:",
            f"{indent}vpush {{d0}}",
            f"{indent}b {lbl_after_loop}_end",
            f"{lbl_done}:",
            f"{indent}vpush {{d0}}",
            f"{lbl_after_loop}_end:",
        ])
        return codigo

    raise AssemblyGeneratorError(f"Operador binário não suportado: {op}")


def _gerar_armazenamento_resultado(indice_expressao: int, indent: str) -> list[str]:
    offset = indice_expressao * 8
    codigo = [f"{indent}ldr r0, =__resultados"]
    if offset > 0:
        codigo.append(f"{indent}add r0, r0, #{offset}")
    codigo.append(f"{indent}vstr d0, [r0]")
    return codigo


def _indice_resultado_res(indice_expressao: int, deslocamento: int) -> int:
    if indice_expressao == 0:
        raise AssemblyGeneratorError("RES requer pelo menos um resultado anterior.")

    # Mantemos a mesma convenção do executor para evitar autorreferência
    # da linha atual: 0 RES aponta para o último resultado disponível.
    if deslocamento == 0:
        return indice_expressao - 1

    indice_resultado = indice_expressao - deslocamento
    if indice_resultado < 0:
        raise AssemblyGeneratorError(
            f"RES referencia uma linha inexistente: {deslocamento}"
        )

    return indice_resultado


def _validar_res_literal(valor: Any) -> int:
    if isinstance(valor, list):
        raise AssemblyGeneratorError("RES requer um literal inteiro.")

    if not _eh_numero(valor):
        raise AssemblyGeneratorError("RES requer um literal numérico.")

    numero = float(valor)
    if not numero.is_integer() or numero < 0:
        raise AssemblyGeneratorError(
            f"RES requer um inteiro não negativo: {valor}"
        )

    return int(numero)


def _novo_rotulo(contexto: ContextoAssembly, prefixo: str) -> str:
    rotulo = f"__{prefixo}_{contexto.contador_rotulos}"
    contexto.contador_rotulos += 1
    return rotulo


def _obter_label_constante(literal: str, contexto: ContextoAssembly) -> str:
    literal_normalizado = _normalizar_literal(literal)

    if literal_normalizado not in contexto.constantes:
        label = f"__const_{contexto.contador_constantes}"
        contexto.constantes[literal_normalizado] = label
        contexto.contador_constantes += 1

    return contexto.constantes[literal_normalizado]


def _normalizar_literal(literal: str) -> str:
    valor = float(literal)
    return repr(valor)


def _label_variavel(nome: str) -> str:
    seguro = re.sub(r"[^a-zA-Z0-9_]", "_", nome)
    if not seguro:
        raise AssemblyGeneratorError(f"Nome de variável inválido: {nome}")
    if seguro[0].isdigit():
        seguro = "_" + seguro
    return f"var_{seguro}"


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
