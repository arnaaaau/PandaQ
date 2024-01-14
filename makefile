# Define el objetivo por defecto (all)
all: gramatica test

# Regla para generar la gramática con ANTLR4
gramatica: pandaQ.g4
	antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4

# Regla para ejecutar la aplicación con Streamlit
test: gramatica
	streamlit run pandaQ.py

clean:	cleandir
	rm -f pandaQ.interp pandaQ.tokens pandaQLexer.interp pandaQLexer.py pandaQLexer.tokens pandaQParser.py pandaQVisitor.py

cleandir:
	rm -f ./__pycache__/*
	rmdir  ./__pycache__
