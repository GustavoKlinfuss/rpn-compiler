import unittest

from lexical_analyzer import parseExpressao, LexicalError


class Tester(unittest.TestCase):
    def test_expressao_valida_simples(self):
        tokens = []
        parseExpressao("(3.14 2.0 +)", tokens)

        self.assertEqual(tokens, ["(", "3.14", "2.0", "+", ")"])

    def test_keyword_res(self):
        tokens = []
        parseExpressao("(5 RES)", tokens)

        self.assertEqual(tokens, ["(", "5", "RES", ")"])

    def test_identificador_memoria(self):
        tokens = []
        parseExpressao("(10.5 CONTADOR)", tokens)

        self.assertEqual(tokens, ["(", "10.5", "CONTADOR", ")"])

    def test_operador_divisao_inteira(self):
        tokens = []
        parseExpressao("(10 3 //)", tokens)

        self.assertEqual(tokens, ["(", "10", "3", "//", ")"])

    def test_expressao_aninhada(self):
        tokens = []
        parseExpressao("((3 4 +) (2 5 *) /)", tokens)

        self.assertEqual(
            tokens,
            ["(", "(", "3", "4", "+", ")", "(", "2", "5", "*", ")", "/", ")"]
        )

    def test_carregar_memoria(self):
        tokens = []
        parseExpressao("(MEM)", tokens)

        self.assertEqual(tokens, ["(", "MEM", ")"])

    def test_salvar_memoria(self):
        tokens = []
        parseExpressao("(10 MEM)", tokens)

        self.assertEqual(tokens, ["(", "10", "MEM", ")"])

    def test_numero_malformado_dois_pontos(self):
        with self.assertRaises(LexicalError):
            parseExpressao("(3.14.5 2.0 +)", [])

    def test_numero_malformado_terminando_com_ponto(self):
        with self.assertRaises(LexicalError):
            parseExpressao("(3. 2 +)", [])

    def test_caractere_invalido(self):
        with self.assertRaises(LexicalError):
            parseExpressao("(3.14 2.0 &)", [])

    def test_parenteses_desbalanceados_faltando_fechamento(self):
        with self.assertRaises(LexicalError):
            parseExpressao("(3.14 2.0 +", [])

    def test_parenteses_desbalanceados_fechamento_extra(self):
        with self.assertRaises(LexicalError):
            parseExpressao("(3 4 +))", [])

    def test_multiplas_linhas_com_mesma_lista(self):
        tokens = []
        parseExpressao("(3 4 +)", tokens)
        parseExpressao("(10 2 //)", tokens)

        self.assertEqual(
            tokens,
            ["(", "3", "4", "+", ")", "(", "10", "2", "//", ")"]
        )

    def test_linha_vazia(self):
        tokens = []
        parseExpressao("", tokens)

        self.assertEqual(tokens, [])

    def test_espacos_em_excesso(self):
        tokens = []
        parseExpressao(" (  10   3   //  ) ", tokens)

        self.assertEqual(tokens, ["(", "10", "3", "//", ")"])


if __name__ == "__main__":
    unittest.main()