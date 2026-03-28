from token_types import Token


def gerarAssembly(tokens: list[Token], output_path: str) -> str:
    """
    Gera um arquivo Assembly ARMv7 básico.
    Nesta base inicial, os tokens são emitidos como comentários para inspeção.
    """

    lines: list[str] = []
    lines.append(".global _start")
    lines.append(".text")
    lines.append("_start:")

    lines.append("    @ Tokens da última execução")
    for token in tokens:
        lines.append(
            f"    @ line={token.line} col={token.column} type={token.type.name} value={token.value}"
        )

    lines.append("")
    lines.append("    @ Encerramento simples")
    lines.append("    MOV R7, #1")
    lines.append("    MOV R0, #0")
    lines.append("    SWI 0")

    assembly = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(assembly)

    return assembly