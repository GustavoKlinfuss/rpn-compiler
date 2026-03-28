.global _start
.text
_start:
    @ Tokens da última execução

    @ Encerramento simples
    MOV R7, #1
    MOV R0, #0
    SWI 0
