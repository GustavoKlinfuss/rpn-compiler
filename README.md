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
- Python 3.11+

**Como executar:**
```
python main.py samples/teste1.txt
```

**Arquivos gerados:**
- `output/tokens_last.txt`
- `output/program.s`

**Como todar todos os testes:**
```
python -m unittest discover -s tests
```