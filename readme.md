# PANDAQ #
Aquest treball consisteix en un intèrpret de sentències SQL anomenat PandaQ per a l'assignatura de llenguatge de programació de la Universitat Politècnica de Catalunya.

## Característiques principals:
A continuació es mencionaran les eines més importants d'aquest treball.

#### ENTRADA DE DADES ####
PandaQ treballa amb un subconjunt de consultes SQL. Cal destacar que no estan implementades totes les funcionalitats principals de les consultes. Es permet l'entrada de dades via fitxers .txt o escrivint la sentència.  

#### DADES ####
PandaQ utilitza taules de dades amb extensió .csv. Per al seu bon funcionament, aquestes taules s'han de situar dins la carpeta Dades. Es recomana que, per tenir una experiència satisfactòria, aquestes taules no tinguin columnes amb els mateixos identificadors.

#### TRACTAMENT ####
A nivell intern, PandaQ utilitza Python com a llenguatge per analitzar els inputs del usuari. Per això, s'utilitza la llibreria Pandas que ofereix Python. Aquesta llibreria permet el tractament de taules de dades.

#### INTERFÍCIE ####
Per generar la interfície d'usuari, Python ofereix una eina anomenada Streamlit, amb la qual s'ha generat l'interfície d'aquest per fer ús de l'interpret de manera més amigable per l'usuari.

## Compilació/Execució ##
Primer de tot, s'ha de compilar la gramàtica que es troba dins l'arxiu pandaQ.g4. Això generarà els fitxers necessaris per poder executar PandaQ:

```
$ antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4
```
Finalment, per executar pandaQ, utilitzarem aquesta comanda:
```
$ streamlit run pandaQ.py
```
Tot i això, per més comoditat per l'usuari, es proporciona un Makefile que permet fer les dues regles anteriors amb una sola comanda:
```
$ make -f makefile
```
## Requeriments ##
IMPORTANT! Per fer ús de pandaQ cal tenir instal·lat en el vostre dispositiu:
  - Python3.17 o posterior
  - Streamlit
  - Antlr4

## Links d'interés ##
  - Sentències que permet pandaQ: https://github.com/gebakx/lp-pandaQ-23/blob/main/readme.md?plain=1
  - Instal·lació de Python: https://www.python.org/downloads/
  - Instal·lació de Antlr4: https://gebakx.github.io/Python3/compiladors.html#2
 
