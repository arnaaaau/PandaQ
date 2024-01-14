all:	gramatica test

gramatica:	pandaQ.g4
	antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4

test:	gramatica
	streamlit run pandaQ.py
