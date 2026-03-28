import re
from dataclasses import dataclass
from typing import Any


class AssemblyGeneratorError(Exception):
    pass


OPERADORES_BINARIOS = {"+", "-", "*", "/", "//", "%", "^"}
OPERADORES_UNARIOS = {"RES"}
TODOS_OPERADORES = OPERADORES_BINARIOS | OPERADORES_UNARIOS


@dataclass
class ContextoAssembly:
    constantes: dict[str, str]
    variaveis: set[str]
    contador_constantes: int = 0
    contador_rotulos: int = 0


def gerarAssembly(tokens: list[str], caminho_saida: str) -> None:
    """
    Gera assembly ARMv7 compatível com CPUlator (bare-metal).

    Regras assumidas:
    - expressões sempre entre parênteses
    - conteúdo interno em RPN / pós-fixa
      Ex.: ( 2 3 + )
    - atribuição:
      ( 10.5 CONTADOR )
      ( ( 2 3 + ) TOTAL )
    - leitura:
      ( CONTADOR )
    - unário:
      ( 5 RES ) => -5

    Observações:
    - +, -, *, / operam em double
    - // e % usam floor(a / b) implementado inline
    - ^ usa expoente inteiro por truncamento
    """

    if not isinstance(tokens, list) or len(tokens) == 0:
        raise AssemblyGeneratorError("A lista de tokens está vazia.")

    expressoes = _agrupar_programa(tokens)
    contexto = ContextoAssembly(constantes={}, variaveis=set())

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
    linhas: list[str] = []

    linhas.append(".syntax unified")
    linhas.append(".arch armv7-a")
    linhas.append(".fpu neon-fp16")
    linhas.append("")
    linhas.append(".text")
    linhas.append(".align 2")
    linhas.append(".global _start")
    linhas.append("")

    linhas.append(".data")
    linhas.append(".align 3")
    linhas.append("__const_one:")
    linhas.append("    .double 1.0")
    linhas.append("")
    if contexto.constantes:
        for literal, label in contexto.constantes.items():
            linhas.append(f"{label}:")
            linhas.append(f"    .double {literal}")
    else:
        linhas.append("__dummy_const:")
        linhas.append("    .double 0.0")
    linhas.append("")

    linhas.append(".bss")
    linhas.append(".align 3")
    if contexto.variaveis:
        for nome in sorted(contexto.variaveis):
            linhas.append(f"{_label_variavel(nome)}:")
            linhas.append("    .space 8")
    linhas.append("__result:")
    linhas.append("    .space 8")
    linhas.append("")

    linhas.append(".text")
    linhas.append(".align 2")
    linhas.append("_start:")
    linhas.append("")

    return linhas


def _gerar_codigo_principal(
    expressoes: list[Any],
    contexto: ContextoAssembly
) -> list[str]:
    linhas: list[str] = []

    for i, expr in enumerate(expressoes, start=1):
        linhas.append(f"    @ expressão {i}")
        linhas.extend(_compilar_expressao(expr, contexto, indent="    "))
        linhas.append("    ldr r0, =__result")
        linhas.append("    vstr d0, [r0]")
        linhas.append("")

    linhas.append("_halt:")
    linhas.append("    b _halt")

    return linhas


def _compilar_expressao(
    expr: Any,
    contexto: ContextoAssembly,
    indent: str = ""
) -> list[str]:
    """
    Ao final da expressão, o resultado fica em d0.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        raise AssemblyGeneratorError("Expressão inválida ou vazia.")

    # ( CONTADOR ) ou ( 10.5 ) ou ( ( 2 3 + ) )
    if len(expr) == 1:
        return _compilar_item(expr[0], contexto, indent)

    # atribuição implícita: ( valor NOME )
    if (
        len(expr) == 2
        and _eh_identificador(expr[1])
        and expr[1] not in TODOS_OPERADORES
    ):
        codigo = []
        codigo.extend(_compilar_item(expr[0], contexto, indent))
        codigo.append(f"{indent}ldr r0, ={_label_variavel(expr[1])}")
        codigo.append(f"{indent}vstr d0, [r0]")
        return codigo

    # expressão RPN
    return _compilar_rpn(expr, contexto, indent)


def _compilar_item(
    item: Any,
    contexto: ContextoAssembly,
    indent: str = ""
) -> list[str]:
    if isinstance(item, list):
        return _compilar_expressao(item, contexto, indent)

    if _eh_numero(item):
        label = _obter_label_constante(item, contexto)
        return [
            f"{indent}ldr r0, ={label}",
            f"{indent}vldr d0, [r0]",
        ]

    if _eh_identificador(item) and item not in TODOS_OPERADORES:
        return [
            f"{indent}ldr r0, ={_label_variavel(item)}",
            f"{indent}vldr d0, [r0]",
        ]

    raise AssemblyGeneratorError(f"Item inválido na expressão: {item}")


def _compilar_rpn(
    expr: list[Any],
    contexto: ContextoAssembly,
    indent: str = ""
) -> list[str]:
    """
    Convenção:
    - ao ler valor/subexpressão: coloca em d0 e faz vpush {d0}
    - operador binário: desempilha direita e esquerda, calcula, faz vpush {d0}
    - ao final: faz vpop {d0}
    """
    profundidade = 0
    codigo: list[str] = []

    for item in expr:
        if isinstance(item, list):
            codigo.extend(_compilar_expressao(item, contexto, indent))
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

        if _eh_identificador(item) and item not in TODOS_OPERADORES:
            codigo.append(f"{indent}ldr r0, ={_label_variavel(item)}")
            codigo.append(f"{indent}vldr d0, [r0]")
            codigo.append(f"{indent}vpush {{d0}}")
            profundidade += 1
            continue

        if item in OPERADORES_UNARIOS:
            if profundidade < 1:
                raise AssemblyGeneratorError(
                    f"Operando insuficiente para operador unário '{item}'."
                )

            codigo.append(f"{indent}vpop {{d0}}")

            if item == "RES":
                codigo.append(f"{indent}vneg.f64 d0, d0")
            else:
                raise AssemblyGeneratorError(
                    f"Operador unário não suportado: {item}"
                )

            codigo.append(f"{indent}vpush {{d0}}")
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
    """
    Antes:
    - topo da pilha = operando da direita
    - abaixo = operando da esquerda

    Depois:
    - resultado é empilhado novamente
    """
    codigo: list[str] = []

    if op in {"+", "-", "*", "/"}:
        codigo.append(f"{indent}vpop {{d1}}")  # direita
        codigo.append(f"{indent}vpop {{d0}}")  # esquerda

        if op == "+":
            codigo.append(f"{indent}vadd.f64 d0, d0, d1")
        elif op == "-":
            codigo.append(f"{indent}vsub.f64 d0, d0, d1")
        elif op == "*":
            codigo.append(f"{indent}vmul.f64 d0, d0, d1")
        elif op == "/":
            codigo.append(f"{indent}vdiv.f64 d0, d0, d1")

        codigo.append(f"{indent}vpush {{d0}}")
        return codigo

    if op == "//":
        lbl_done = _novo_rotulo(contexto, "floor_done")

        codigo.extend([
            f"{indent}@ floor(left / right)",
            f"{indent}vpop {{d1}}",                  # right
            f"{indent}vpop {{d0}}",                  # left
            f"{indent}vdiv.f64 d2, d0, d1",          # q = left / right
            f"{indent}vcvt.s32.f64 s0, d2",          # trunc(q)
            f"{indent}vcvt.f64.s32 d3, s0",          # d3 = trunc(q) como double
            f"{indent}vcmp.f64 d2, d3",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}beq {lbl_done}",
            f"{indent}vcmp.f64 d2, #0.0",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}bge {lbl_done}",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d4, [r0]",
            f"{indent}vsub.f64 d3, d3, d4",          # ajusta para floor em negativos
            f"{lbl_done}:",
            f"{indent}vmov d0, d3",
            f"{indent}vpush {{d0}}",
        ])
        return codigo

    if op == "%":
        lbl_done = _novo_rotulo(contexto, "mod_floor_done")

        codigo.extend([
            f"{indent}@ left % right = left - floor(left/right) * right",
            f"{indent}vpop {{d1}}",                  # right
            f"{indent}vpop {{d0}}",                  # left
            f"{indent}vmov d5, d0",                  # guarda left
            f"{indent}vmov d6, d1",                  # guarda right
            f"{indent}vdiv.f64 d2, d0, d1",          # q = left / right
            f"{indent}vcvt.s32.f64 s0, d2",          # trunc(q)
            f"{indent}vcvt.f64.s32 d3, s0",          # d3 = trunc(q)
            f"{indent}vcmp.f64 d2, d3",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}beq {lbl_done}",
            f"{indent}vcmp.f64 d2, #0.0",
            f"{indent}vmrs APSR_nzcv, fpscr",
            f"{indent}bge {lbl_done}",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d4, [r0]",
            f"{indent}vsub.f64 d3, d3, d4",          # floor(q)
            f"{lbl_done}:",
            f"{indent}vmul.f64 d3, d3, d6",          # floor(q) * right
            f"{indent}vsub.f64 d0, d5, d3",          # left - ...
            f"{indent}vpush {{d0}}",
        ])
        return codigo

    if op == "^":
        lbl_loop = _novo_rotulo(contexto, "pow_loop")
        lbl_after_loop = _novo_rotulo(contexto, "pow_after_loop")
        lbl_positive = _novo_rotulo(contexto, "pow_positive")
        lbl_done = _novo_rotulo(contexto, "pow_done")

        codigo.extend([
            f"{indent}@ potência com expoente inteiro por truncamento",
            f"{indent}vpop {{d1}}",                  # expoente
            f"{indent}vpop {{d0}}",                  # base
            f"{indent}vmov d2, d0",                  # d2 = base
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d0, [r0]",                # d0 = resultado = 1.0
            f"{indent}vcvt.s32.f64 s0, d1",          # expoente inteiro truncado
            f"{indent}vmov r1, s0",                  # r1 = exp
            f"{indent}mov r2, #0",                   # flag negativo = 0
            f"{indent}cmp r1, #0",
            f"{indent}bge {lbl_positive}",
            f"{indent}rsb r1, r1, #0",               # r1 = -r1
            f"{indent}mov r2, #1",                   # flag negativo = 1
            f"{lbl_positive}:",
            f"{indent}cmp r1, #0",
            f"{indent}beq {lbl_after_loop}",
            f"{lbl_loop}:",
            f"{indent}vmul.f64 d0, d0, d2",
            f"{indent}subs r1, r1, #1",
            f"{indent}bne {lbl_loop}",
            f"{lbl_after_loop}:",
            f"{indent}cmp r2, #0",
            f"{indent}beq {lbl_done}",
            f"{indent}ldr r0, =__const_one",
            f"{indent}vldr d3, [r0]",
            f"{indent}vdiv.f64 d0, d3, d0",          # 1 / resultado
            f"{lbl_done}:",
            f"{indent}vpush {{d0}}",
        ])
        return codigo

    raise AssemblyGeneratorError(f"Operador binário não suportado: {op}")


def _novo_rotulo(contexto: ContextoAssembly, prefixo: str) -> str:
    rotulo = f"__{prefixo}_{contexto.contador_rotulos}"
    contexto.contador_rotulos += 1
    return rotulo


def _obter_label_constante(
    literal: str,
    contexto: ContextoAssembly
) -> str:
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
        raise AssemblyGeneratorError(
            f"Nome de variável inválido: {nome}"
        )
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