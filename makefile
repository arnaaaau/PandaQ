all:	gramatica test

gramatica:	exprs.g4
	antlr4 -Dlanguage=Python3 -no-listener -visitor exprs.g4

test:	gramatica
	streamlit run exprs.py
