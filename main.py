"""
Integrantes do grupo: Gustavo Klinfuss da Silva
Nome do grupo no Canvas: RA1 31
"""

import os
import sys
import json

from lexical_analyzer import parseExpressao, LexicalError
from assembly_generator import gerarAssembly
from token_types import Token

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python main.py samples/teste1.txt")
        return 1

    arquivo_entrada = sys.argv[1]

    if not os.path.exists(arquivo_entrada):
        print(f"Arquivo não encontrado: {arquivo_entrada}")
        return 1

    linhas = lerArquivo(arquivo_entrada)
    tokens = []

    try:
        for linha in linhas:
            if linha.strip() == "":
                continue
            parseExpressao(linha, tokens)
    except LexicalError as e:
        print(f"Erro léxico: {e}")
        return 1

    os.makedirs("output", exist_ok=True)

    salvarTokens(tokens)

    caminho_assembly = os.path.join("output", "program.s")
    #gerarAssembly(trees, caminho_assembly)
    #exibirResultados(tokens, caminho_assembly, caminho_tokens)

    return 0

def lerArquivo(nome_arquivo: str) -> list[str]:
    with open(nome_arquivo, "r", encoding="utf-8") as f:
        return [linha.rstrip("\n") for linha in f]

def salvarTokens(dados: list[str]) -> None:
    caminho = os.path.join("output", "tokens_last.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def salvarAst(dados: dict) -> None:
    caminho = os.path.join("output", "ast_last.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def exibirResultados(tokens: list[Token], assembly_path: str, tokens_path: str) -> None:
    print("Análise léxica concluída com sucesso.")
    print(f"Quantidade de tokens: {len(tokens)}")
    print(f"Tokens salvos em: {tokens_path}")
    print(f"Assembly salvo em: {assembly_path}")

if __name__ == "__main__":
    raise SystemExit(main())