# rpn-to-arm-compiler
**Descrição**: Analisador léxico com AFD e gerador de Assembly ARMv7.

## Geral
**Instituição:** Pontifícia Universidade Católica do Paraná

**Disciplina**: Construção de Interpretadores

**Professor:** Frank Coelho de Alcantara

**Integrantes:**
- Gustavo Klinfuss da Silva - **Github:** GustavoKlinfuss

## Execução
**Requisitos**:
- Python 3.14
- Linha de comando configurada com python

**Como executar:**
Entrar na pasta raiz do projeto e executar:
```
python main.py samples/teste1.txt
python main.py samples/teste2.txt
python main.py samples/teste3.txt
```

**Arquivos gerados:**
- `output/tokens_last.txt` (Arquivo com tokens)
- `output/program.s` (arquivo Assembly)

**Como todar todos os testes:**
```
python -m unittest discover -s tests
```