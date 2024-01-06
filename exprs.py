import sys
import streamlit as st
from antlr4 import *
from exprsLexer import exprsLexer
from exprsParser import exprsParser
from exprsVisitor import exprsVisitor
import pandas as pd
import matplotlib.pyplot as plt
from antlr4.tree.Tree import TerminalNodeImpl


class EvalVisitor(exprsVisitor):
    def __init__(self):
        self.columnes = []
        self.columnes_dordenacio = [[], []]
        self.pd = []
        self.error = None
        self.i = 0

    def visitRoot(self, ctx):
        [query] = list(ctx.getChildren())
        return self.visit(query)

    def visitQuery_with_simbol(self, ctx):
        [alias, _, query] = list(ctx.getChildren())
        self.columnes = []
        result = self.visit(query)
        st.session_state[alias.getText()] = result
        return result

    def visitPlot(self, ctx):
        [_, variable, _] = list(ctx.getChildren())
        identificador = variable.getText()
        try:
            if identificador in st.session_state:
                st.set_option('deprecation.showPyplotGlobalUse', False)
                st.session_state[identificador].plot()
                st.pyplot()
            else:
                self.controlError(5)
        except Exception as e:
            self.controlError(7)

    def visitQuery_senseClausules(self, ctx):
        [_, columnes, _, table, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.visit(columnes)
        return self.pd[self.i]

    def visitQuery_senseClausules_orderby(self, ctx):
        [_, columnes, _, table, orderby, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.visit(columnes)
        self.columnes_dordenacio = [[], []]
        self.visit(orderby)
        return self.controlOrderBy()

    def visitQuery_ambClausules(self, ctx):
        [_, columnes, _, table, clausules, _] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.pd.append(result)
        self.pd[self.i] = self.visit(clausules)
        self.columnes = []
        self.visit(columnes)
        return self.pd[self.i]

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

    def visitSelect_where(self, ctx):
        [where] = list(ctx.getChildren())
        self.visit(where)
        return self.pd[self.i]

    def visitSubquery_sintaxis(self, ctx):
        [_, alias, _, _, subquery, _] = list(ctx.getChildren())
        table = self.visit(subquery)
        if alias.getText() not in table.columns:
            self.controlError(6)
        self.pd[self.i] = pd.merge(self.pd[self.i], table, left_on=alias.getText(), right_on=alias.getText(), how='inner')
        return self.pd[self.i]

    def visitSubquery_senseClausules(self, ctx):
        [_, columnes, _, table] = list(ctx.getChildren())
        result = self.encontrarTabla(table.getText())
        self.i += 1
        self.pd.append(result)
        self.visit(columnes)
        taula = self.pd[self.i]
        self.i -= 1
        return taula

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

    def visitSelect_innerjoin(self, ctx):
        [joinclauses] = list(ctx.getChildren())
        self.visit(joinclauses)
        return self.pd[self.i]

    def visitJoin_clauses(self, ctx):
        innerjoins_encadenats = list(ctx.getChildren())
        for item in innerjoins_encadenats:
            self.visit(item)

    def visitInnerjoin(self, ctx):
        [_, table, _, column1, _, column2] = list(ctx.getChildren())
        innerjoin_table = self.encontrarTabla(table.getText())
        column1 = column1.getText()
        column2 = column2.getText()
        if column1 not in self.pd[self.i].columns or column2 not in innerjoin_table.columns:
            self.controlError(1)
        self.pd[self.i] = pd.merge(self.pd[self.i], innerjoin_table, left_on=column1, right_on=column2)

    def visitSelectAll(self, ctx):
        return

    def visitSelectPersonalitzat(self, ctx):
        selected_columns = [self.visit(item) for item in ctx.getChildren() if item.getText() != ',']
        try:
            self.pd[self.i] = self.pd[self.i][self.columnes]
        except Exception as e:
            self.controlError(1)

    def visitColumna_simple(self, ctx):
        self.columnes.append(ctx.getText())

    def visitColumna_amb_expressio(self, ctx):
        [expressio, _, new_name] = list(ctx.getChildren())
        try:
            columna_nova = self.visit(expressio)
        except Exception as e:
            self.controlError(4)
        else:
            self.pd[self.i][new_name.getText()] = columna_nova
            self.columnes.append(new_name.getText())

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
        elif op == '/':
            return columna / valor

    def visitWhere(self, ctx):
        [_, expr] = list(ctx.getChildren())
        condicion = self.visit(expr)
        self.pd[self.i] = self.pd[self.i][condicion]

    def visitArimetriques(self, ctx):
        [condicio] = list(ctx.getChildren())
        return (self.visit(condicio))

    def visitNot_parentesis_where(self, ctx):
        [_, _, expressio, _] = list(ctx.getChildren())
        condicio = self.visit(expressio)
        return ~condicio

    def visitParentesis_where(self, ctx):
        [_, expressio, _] = list(ctx.getChildren())
        condicio = self.visit(expressio)
        return condicio

    def visitAnd(self, ctx):
        [expr1, _, expr2] = list(ctx.getChildren())
        condicio1 = self.visit(expr1)
        condicio2 = self.visit(expr2)
        return (condicio1 & condicio2)

    def visitNot_menor(self, ctx):
        [_, columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] >= numero)

    def visitNot_igual(self, ctx):
        [_, columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] != numero)

    def visitNot_igual_string(self, ctx):
        [_, columna, _, string] = list(ctx.getChildren())
        string = string.getText()
        df = self.pd[self.i]
        return (df[columna.getText()] != string)

    def visitMenor(self, ctx):
        [columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] < numero)

    def visitIgual(self, ctx):
        [columna, _, numero] = list(ctx.getChildren())
        numero = float(numero.getText())
        df = self.pd[self.i]
        return (df[columna.getText()] == numero)

    def visitIgual_string(self, ctx):
        [columna, _, string] = list(ctx.getChildren())
        string = string.getText()
        df = self.pd[self.i]
        return (df[columna.getText()] == string)

    def visitOrderby(self, ctx):
        [_, columnes] = list(ctx.getChildren())
        self.visit(columnes)

    def visitColumnes_dordenacio(self, ctx):
        for item in ctx.getChildren():
            if item.getText() != ',':
                self.visit(item)

    def visitCol_asc(self, ctx):
        [col] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(True)

    def visitCol_asc_especificat(self, ctx):
        [col, _] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(True)

    def visitCol_desc(self, ctx):
        [col, _] = list(ctx.getChildren())
        self.columnes_dordenacio[0].append(col.getText())
        self.columnes_dordenacio[1].append(False)

    def visitParentesis(self, ctx):
        [_, expressio, _] = list(ctx.getChildren())
        return self.visit(expressio)

    def visitNumero(self, ctx):
        [numero] = list(ctx.getChildren())
        return float(numero.getText())

    def visitColumna(self, ctx):
        [nom] = list(ctx.getChildren())
        return self.pd[self.i][nom.getText()]

    def visitAlias(self, ctx):
        return ctx.getText()

    def visitTable(self, ctx):
        return ctx.getText()

    def encontrarTabla(self, nom):
        if nom in st.session_state:
            return st.session_state[nom]
        else:
            try:
                result = pd.read_csv(f'./Data/{nom}.csv', sep=',', header=0, na_values="NaN", decimal='.')
            except Exception as e:
                self.controlError(3)
            else:
                return result

    def controlOrderBy(self):
        try:
            self.pd[self.i] = self.pd[self.i].sort_values(by=self.columnes_dordenacio[0], ascending=self.columnes_dordenacio[1])
        except Exception as e:
            self.controlError(2)
        else:
            return self.pd[self.i]

    def controlError(self, codi):
        if codi == 1 and self.error is None:
            self.error = "ERROR: Las columnas no se corresponden con las que tiene la tabla"
        elif codi == 2 and self.error is None:
            self.error = "ERROR: La columnas de ordenación no són correctas"
        elif codi == 3 and self.error is None:
            self.error = "ERROR: La tabla indicada no existe"
        elif codi == 4 and self.error is None:
            self.error = "ERROR: La columna o columnas indicadas no existen"
        elif codi == 5 and self.error is None:
            self.error = "ERROR: El identificador no existe"
        elif codi == 6 and self.error is None:
            self.error = "ERROR: Identificador de la columna dentro de la subquery es incorrecta."
        elif codi == 7 and self.error is None:
            self.error = "ERROR: La tabla/identificador no contienen valores numericos."
        st.error(self.error)
        sys.exit()


def analizar_codigo(codigo):
    input_stream = InputStream(codigo)
    lexer = exprsLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = exprsParser(token_stream)
    tree = parser.root()

    if parser.getNumberOfSyntaxErrors() == 0:
        visitor = EvalVisitor()
        result = visitor.visit(tree)
        if result is not None:
            st.text(tree.toStringTree(recog=parser))
            st.write("Resultado después de analizar:", result)
    else:
        st.error(f"{parser.getNumberOfSyntaxErrors()} errores de sintaxis.")
        st.text(tree.toStringTree(recog=parser))


def main():
    st.title("Compilador SQL")

    # Interfaz para cargar archivos
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


if __name__ == "__main__":
    main()
