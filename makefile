# Define el objetivo por defecto (all)
all: gramatica test

# Regla para generar la gramática con ANTLR4
gramatica: pandaQ.g4
	antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4

# Regla para ejecutar la aplicación con Streamlit
test: gramatica
	streamlit run pandaQ.py
