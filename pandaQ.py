import sys
import streamlit as st
from antlr4 import *
from pandaQLexer import pandaQLexer
from pandaQParser import pandaQParser
from pandaQVisitor import pandaQVisitor
import pandas as pd
import matplotlib.pyplot as plt
from antlr4.tree.Tree import TerminalNodeImpl


# Clase para visitar el árbol generado por ANTLR y ejecutar la lógica asociada a cada nodo
class EvalVisitor(pandaQVisitor):
    def __init__(self):
        # Inicialización de variables de la clase
        self.columnes = []
        self.columnes_dordenacio = [[], []]
        self.pd = []
        self.error = None
        self.i = 0

    # Método para visitar el nodo Root
    def visitRoot(self, ctx):
        [query] = list(ctx.getChildren())
        return self.visit(query)

    # Método para visitar el nodo Query_with_simbol
    def visitQuery_with_simbol(self, ctx):
        [alias, _, query] = list(ctx.getChildren())
        self.columnes = []
        result = self.visit(query)
        st.session_state[alias.getText()] = result
        return result

    # Método para generar el gráfico de la variable contenida en el token "variable"
    def visitPlot(self, ctx):
        [_, variable, _] = list(ctx.getChildren())
        identificador = variable.getText()
        try:
            if identificador in st.session_state:
                st.set_option('deprecation.showPyplotGlobalUse', False)
                st.session_state[identificador].plot()
                st.pyplot()
                return
            else:
                self.controladorDerrores(f"No existe el identificador con nombre {identificador}.")
        except Exception as e:
            self.controladorDerrores(f"El identificador {identificador} seleccionado no es compatible para generar un gráfico.")

    # Método para visitar el nodo Query_senseClausules
    def visitQuery_senseClausules(self, ctx):
        [_, columnes, _, table, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.visit(columnes)
        return self.pd[self.i]

    # Método para visitar el nodo Query_senseClausules_orderby
    def visitQuery_senseClausules_orderby(self, ctx):
        [_, columnes, _, table, orderby, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.visit(columnes)
        self.columnes_dordenacio = [[], []]
        self.visit(orderby)
        return self.controlOrderBy()

    # Método para visitar el nodo Query_ambClausules
    def visitQuery_ambClausules(self, ctx):
        [_, columnes, _, table, clausules, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.pd[self.i] = self.visit(clausules)
        self.columnes = []
        self.visit(columnes)
        return self.pd[self.i]

    # Método para visitar el nodo Query_ambClausules_i_orderby
    def visitQuery_ambClausules_i_orderby(self, ctx):
        [_, columnes, _, table, clausules, orderby, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.pd[self.i] = self.visit(clausules)
        self.columnes = []
        self.visit(columnes)
        self.columnes_dordenacio = [[], []]
        self.visit(orderby)
        return self.controlOrderBy()

    # Método para visitar el nodo Select_where
    def visitSelect_where(self, ctx):
        [where] = list(ctx.getChildren())
        self.visit(where)
        return self.pd[self.i]

    # Métodos para visitar nodos relacionados con subconsultas
    def visitSubquery(self, ctx):
        llista = list(ctx.getChildren())
        for i in llista:
            taula = self.visit(i)
        return taula

    # Método para visitar el nodo Subquery_sintaxis
    def visitSubquery_sintaxis(self, ctx):
        [_, alias, _, _, subquery, _] = list(ctx.getChildren())
        table = self.visit(subquery)
        if alias.getText() not in table.columns:
            self.controladorDerrores(f"La columna con nombre {alias.getText()} no existe.")
        self.pd[self.i] = pd.merge(self.pd[self.i], table, left_on=alias.getText(), right_on=alias.getText())
        self.pd[self.i] = self.pd[self.i].drop_duplicates()
        return self.pd[self.i]

    # Método para visitar el nodo Subquery_senseClausules
    def visitSubquery_senseClausules(self, ctx):
        [_, columnes, _, table] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.i += 1
        self.pd.append(result)
        self.visit(columnes)
        taula = self.pd[self.i]
        self.i -= 1
        return taula

    # Método para visitar el nodo Subquery_ambClausules
    def visitSubquery_ambClausules(self, ctx):
        [_, columnes, _, table, clausules] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.i += 1
        self.pd.append(result)
        self.pd[self.i] = self.visit(clausules)
        self.columnes = []
        self.visit(columnes)
        taula = self.pd[self.i]
        self.i -= 1
        return taula

    # Métodos para visitar nodos relacionados con INNER JOIN
    def visitSelect_innerjoin(self, ctx):
        [joinclauses] = list(ctx.getChildren())
        self.visit(joinclauses)
        return self.pd[self.i]

    # Método para visitar el nodo Join_clauses
    def visitJoin_clauses(self, ctx):
        innerjoins_encadenats = list(ctx.getChildren())
        for item in innerjoins_encadenats:
            self.visit(item)

    # Método para visitar el nodo Innerjoin
    def visitInnerjoin(self, ctx):
        [_, table, _, column1, _, column2] = list(ctx.getChildren())
        innerjoin_table = self.encontrarTabla(table.getText())
        column1 = column1.getText()
        column2 = column2.getText()
        if column1 not in self.pd[self.i].columns:
            self.controladorDerrores(f"No existe la columna con nombre {column1}.")
        if column2 not in innerjoin_table.columns:
            columna_erronea = column2
            self.controladorDerrores(f"No existe la columna con nombre {column2}.")
        self.pd[self.i] = pd.merge(self.pd[self.i], innerjoin_table, left_on=column1, right_on=column2)

    # Métodos para visitar nodos relacionados con la selección de columnas
    def visitSelectAll(self, ctx):
        return

    # Método para visitar el nodo SelectPersonalitzat
    def visitSelectPersonalitzat(self, ctx):
        selected_columns = [self.visit(item) for item in ctx.getChildren() if item.getText() != ',']
        try:
            self.pd[self.i] = self.pd[self.i][self.columnes]
        except Exception as e:
            columna_erronea = self.detectorColumnaErronea()
            self.controladorDerrores(f"La columna con nombre {columna_erronea} no existe.")

    # Método para visitar el nodo Columna_simple
    def visitColumna_simple(self, ctx):
        self.columnes.append(ctx.getText())

    # Método para visitar el nodo Columna_amb_expressio
    def visitColumna_amb_expressio(self, ctx):
        [expressio, _, new_name] = list(ctx.getChildren())
        try:
            columna_nova = self.visit(expressio)
        except Exception as e:
            columna_erronea = self.detectorColumnaErronea()
            self.controladorDerrores(f"La columna con nombre {columna_erronea} no existe.")
        else:
            self.pd[self.i][new_name.getText()] = columna_nova
            self.columnes.append(new_name.getText())

    # Método para visitar el nodo Binari
    def visitBinari(self, ctx):
        [expressio1, operador, expressio2] = list(ctx.getChildren())
        columna = self.visit(expressio1)
        op = operador.getText()
        valor = self.visit(expressio2)
        if op == '+':
            return columna + valor
        elif op == '-':
            return columna - valor
        elif op == '*':
            return columna * valor
        else:
            return columna / valor

    # Método para visitar el nodo Where
    def visitWhere(self, ctx):
        [_, expr] = list(ctx.getChildren())
        try:
            condicion = self.visit(expr)
        except Exception as e:
            self.controladorDerrores(f"No existe alguna columna")
        self.pd[self.i] = self.pd[self.i][condicion]

    # Método para visitar el nodo Arimetriques
    def visitArimetriques(self, ctx):
        [condicio] = list(ctx.getChildren())
        return (self.visit(condicio))

    # Método para visitar el nodo Not_parentesis_where
    def visitNot_parentesis_where(self, ctx):
        [_, _, expressio, _] = list(ctx.getChildren())
        condicio = self.visit(expressio)
        return ~condicio

    # Método para visitar el nodo Parentesis_where
    def visitParentesis_where(self, ctx):
        [_, expressio, _] = list(ctx.getChildren())
        condicio = self.visit(expressio)
        return condicio

    # Método para visitar el nodo And
    def visitAnd(self, ctx):
        [expr1, _, expr2] = list(ctx.getChildren())
        condicio1 = self.visit(expr1)
        condicio2 = self.visit(expr2)
        return (condicio1 & condicio2)

    # Método para visitar el nodo Not_menor
    def visitNot_menor(self, ctx):
        [_, columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] >= numero)

    # Método para visitar el nodo Not_igual
    def visitNot_igual(self, ctx):
        [_, columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] != numero)

    # Método para visitar el nodo Not_igual_string
    def visitNot_igual_string(self, ctx):
        [_, columna, _, string] = list(ctx.getChildren())
        string = string.getText()
        df = self.pd[self.i]
        return (df[columna.getText()] != string)

    # Método para visitar el nodo Menor
    def visitMenor(self, ctx):
        [columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] < numero)

    # Método para visitar el nodo Igual
    def visitIgual(self, ctx):
        [columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] == numero)

    def visitColumna_amb_buits(self, ctx):
        [columna, _, _] = list(ctx.getChildren())
        df = self.pd[self.i]
        return (df[columna.getText()].isnull())

    def visitNot_columna_amb_buits(self, ctx):
        [_,columna, _, _] = list(ctx.getChildren())
        df = self.pd[self.i]
        return (df[columna.getText()].notnull())

    # Método para visitar el nodo Igual_string
    def visitIgual_string(self, ctx):
        [columna, _, string] = list(ctx.getChildren())
        string = string.getText()
        df = self.pd[self.i]
        return (df[columna.getText()] == string)

    # Método para visitar el nodo Orderby
    def visitOrderby(self, ctx):
        [_, columnes] = list(ctx.getChildren())
        self.visit(columnes)
        return

    # Método para visitar el nodo Columnes_dordenacio
    def visitColumnes_dordenacio(self, ctx):
        for item in ctx.getChildren():
            if item.getText() != ',':
                self.visit(item)
        return

    # Método para visitar el nodo Col_asc
    def visitCol_asc(self, ctx):
        [col] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(True)
        return

    # Método para visitar el nodo Col_asc_especificat
    def visitCol_asc_especificat(self, ctx):
        [col, _] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(True)
        return

    # Método para visitar el nodo Col_desc
    def visitCol_desc(self, ctx):
        [col, _] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(False)
        return

    # Método para visitar el nodo Parentesis
    def visitParentesis(self, ctx):
        [_, expressio, _] = list(ctx.getChildren())
        return self.visit(expressio)

    # Método para visitar el nodo Numero
    def visitNumero(self, ctx):
        [numero] = list(ctx.getChildren())
        return float(numero.getText())

    # Método para visitar el nodo Columna
    def visitColumna(self, ctx):
        [nom] = list(ctx.getChildren())
        return self.pd[self.i][nom.getText()]

    # Método para visitar el nodo Alias
    def visitAlias(self, ctx):
        return ctx.getText()

    # Método para visitar el nodo Table
    def visitTable(self, ctx):
        return ctx.getText()

    # Verificar si las columnas introducidas por el usuario son correctas
    def detectorColumnaErronea(self):
        for columna_erronea in self.columnes:
            if columna_erronea not in self.pd[self.i].columns:
                return columna_erronea

    # Verificar si la tabla con nombre "nom" existe
    def encontrarTabla(self, nom):
        if nom in st.session_state:
            return st.session_state[nom]
        else:
            try:
                result = pd.read_csv(f'./Data/{nom}.csv', sep=',', header=0, na_values="NaN", decimal='.')
            except Exception as e:
                self.controladorDerrores(f"La tabla con nombre {nom} no existe.")
            else:
                return result

    # Verificar si las columnas usadas para ordenar son correctas
    def controlOrderBy(self):
        try:
            self.pd[self.i] = self.pd[self.i].sort_values(by=self.columnes_dordenacio[0], ascending=self.columnes_dordenacio[1])
        except Exception as e:
            self.controladorDerrores("Las columnas de ordenación no són correctas")
        else:
            return self.pd[self.i]

    # Recogue el error generado y lanza una excepcion de RuntimeError
    def controladorDerrores(self, mensaje):
        if self.error is None:
            self.error = f"ERROR: {mensaje}"
        raise RuntimeError(f"{self.error}")


# Función para analizar la sentencia sql
def analizar_codigo(codigo):
    input_stream = InputStream(codigo)
    lexer = pandaQLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = pandaQParser(token_stream)
    tree = parser.root()

    try:
        if parser.getNumberOfSyntaxErrors() == 0:
            visitor = EvalVisitor()
            result = visitor.visit(tree)
            st.write("Resultado después de analizar:", result)
        else:
            st.error(f"{parser.getNumberOfSyntaxErrors()} errores de sintaxis.")
            st.text(tree.toStringTree(recog=parser))
    except Exception as e:
        st.error(f"{e}")


def main():
    st.title("PANDAQ")
    # Interfaz para cargar archivos de extension .csv
    uploaded_file = st.file_uploader("Cargar archivo de consultas SQL", type=["txt"])

    if uploaded_file is not None:
        # Leer el contenido del archivo cargado
        codigo = uploaded_file.getvalue().decode("utf-8")
        st.write(codigo)
        # Analizar el código del archivo
        analizar_codigo(codigo)
    else:
        # Interfaz para ingresar código manualmente
        codigo = st.text_area("Ingresa tu código aquí")

        if st.button("Analizar"):
            analizar_codigo(codigo)


# Punto de entrada principal
if __name__ == "__main__":
    main()
