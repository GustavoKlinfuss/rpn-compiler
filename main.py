"""
Integrantes do grupo: Gustavo Klinfuss da Silva
Nome do grupo no Canvas: RA1 31
"""

import os
import sys

from lexical_analyzer import parseExpressao, LexicalError
from assembly_generator import gerarAssembly, AssemblyGeneratorError
from expression_executor import executarExpressao, ExecutionError

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python main.py samples/teste1.txt")
        return 1

    arquivo_entrada = sys.argv[1]

    if not os.path.exists(arquivo_entrada):
        print(f"Arquivo não encontrado: {arquivo_entrada}")
        return 1

    try:
        linhas = lerArquivo(arquivo_entrada)
    except OSError as e:
        print(f"Erro ao ler arquivo: {e}")
        return 1

    tokens: list[str] = []

    try:
        for linha in linhas:
            if linha.strip():
                parseExpressao(linha, tokens)
    except LexicalError as e:
        print(f"Erro léxico: {e}")
        return 1

    os.makedirs("output", exist_ok=True)
    caminho_tokens = os.path.join("output", "tokens_last.txt")
    salvarTokens(tokens, caminho_tokens)

    try:
        resultados = executarExpressao(tokens)
        caminho_assembly = os.path.join("output", "program.s")
        gerarAssembly(tokens, caminho_assembly)
    except (ExecutionError, AssemblyGeneratorError) as e:
        print(f"Erro de processamento: {e}")
        return 1

    exibirResultados(resultados, caminho_assembly, caminho_tokens)
    return 0


def lerArquivo(nome_arquivo: str) -> list[str]:
    with open(nome_arquivo, "r", encoding="utf-8") as f:
        return [linha.rstrip("\n") for linha in f]


def salvarTokens(tokens: list[str], caminho_tokens: str) -> None:
    with open(caminho_tokens, "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(f"{token}\n")


def exibirResultados(resultados: list[float], assembly_path: str, tokens_path: str):
    print("Análise concluída com sucesso.")
    for indice, resultado in enumerate(resultados, start=1):
        print(f"Linha {indice}: {formatarResultado(resultado)}")
    print(f"Tokens salvos em: {tokens_path}")
    print(f"Assembly salvo em: {assembly_path}")

def formatarResultado(valor: float) -> str:
    texto = f"{valor:.6f}".rstrip("0").rstrip(".")
    if "." not in texto:
        texto += ".0"
    return texto

if __name__ == "__main__":
    raise SystemExit(main())
