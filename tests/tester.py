import tempfile
import unittest
from pathlib import Path

from assembly_generator import gerarAssembly
from expression_executor import ExecutionError, executarExpressao
from lexical_analyzer import LexicalError, parseExpressao
from main import formatarResultado, lerArquivo, salvarTokens


class Tester(unittest.TestCase):
    def tokenizar(self, *linhas: str) -> list[str]:
        tokens: list[str] = []
        for linha in linhas:
            parseExpressao(linha, tokens)
        return tokens

    def test_expressao_valida_simples(self):
        self.assertEqual(
            self.tokenizar("(3.14 2.0 +)"),
            ["(", "3.14", "2.0", "+", ")"],
        )

    def test_keyword_res(self):
        self.assertEqual(
            self.tokenizar("(5 RES)"),
            ["(", "5", "RES", ")"],
        )

    def test_identificador_memoria(self):
        self.assertEqual(
            self.tokenizar("(10.5 CONTADOR)"),
            ["(", "10.5", "CONTADOR", ")"],
        )

    def test_operador_divisao_inteira(self):
        self.assertEqual(
            self.tokenizar("(10 3 //)"),
            ["(", "10", "3", "//", ")"],
        )

    def test_expressao_aninhada(self):
        self.assertEqual(
            self.tokenizar("((3 4 +) (2 5 *) /)"),
            ["(", "(", "3", "4", "+", ")", "(", "2", "5", "*", ")", "/", ")"],
        )

    def test_numero_malformado_dois_pontos(self):
        with self.assertRaises(LexicalError):
            self.tokenizar("(3.14.5 2.0 +)")

    def test_numero_malformado_terminando_com_ponto(self):
        with self.assertRaises(LexicalError):
            self.tokenizar("(3. 2 +)")

    def test_caractere_invalido(self):
        with self.assertRaises(LexicalError):
            self.tokenizar("(3.14 2.0 &)")

    def test_parenteses_desbalanceados(self):
        with self.assertRaises(LexicalError):
            self.tokenizar("(3 4 +))")

    def test_espacos_em_excesso(self):
        self.assertEqual(
            self.tokenizar(" (  10   3   //  ) "),
            ["(", "10", "3", "//", ")"],
        )

    def test_executar_expressao_com_memoria(self):
        tokens = self.tokenizar(
            "(((2 3 +) 4 /) MEM)",
            "((MEM) 2 +)",
        )

        self.assertEqual(executarExpressao(tokens), [1.25, 3.25])

    def test_executar_expressao_com_res(self):
        tokens = self.tokenizar(
            "(3 4 +)",
            "(10 2 /)",
            "((1 RES) (2 RES) +)",
        )

        self.assertEqual(executarExpressao(tokens), [7.0, 5.0, 12.0])

    def test_res_sem_resultado_anterior_falha(self):
        with self.assertRaises(ExecutionError):
            executarExpressao(self.tokenizar("(1 RES)"))

    def test_salvar_tokens_em_txt(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "tokens_last.txt"
            salvarTokens(["(", "3", "4", "+", ")"], str(caminho))

            self.assertEqual(
                caminho.read_text(encoding="utf-8"),
                "(\n3\n4\n+\n)\n",
            )

    def test_ler_arquivo(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "entrada.txt"
            caminho.write_text("(1 2 +)\n(3 4 *)\n", encoding="utf-8")

            self.assertEqual(lerArquivo(str(caminho)), ["(1 2 +)", "(3 4 *)"])

    def test_formatar_resultado(self):
        self.assertEqual(formatarResultado(7.0), "7.0")
        self.assertEqual(formatarResultado(3.125), "3.125")

    def test_gerar_assembly_com_historico_de_resultados(self):
        tokens = self.tokenizar(
            "(3 4 +)",
            "(5 6 +)",
            "(1 RES)",
        )

        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "program.s"
            gerarAssembly(tokens, str(caminho))
            assembly = caminho.read_text(encoding="utf-8")

        self.assertIn("__resultados:", assembly)
        self.assertIn("add r0, r0, #8", assembly)


if __name__ == "__main__":
    unittest.main()
