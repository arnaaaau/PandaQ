grammar pandaQ;

root: query|query_with_simbol|plot;

query_with_simbol : alias ':=' query;

query : 'select' select_list 'from' table orderby';'                                      #query_senseClausules_orderby
      | 'select' select_list 'from' table ';'                                             #query_senseClausules
      | 'select' select_list 'from' table (clausules|subquery)* ';'                       #query_ambClausules
      | 'select' select_list 'from' table (clausules|subquery)* orderby';'                #query_ambClausules_i_orderby
      ;

clausules : where                                            #select_where
          | join_clauses                                     #select_innerjoin
          ;

subquery : subquery_sintaxis+ ;

subquery_sintaxis : 'where' alias 'in' '(' subquery_consulta ')';

subquery_consulta : 'select' select_list 'from' table                #subquery_senseClausules
                  | 'select' select_list 'from' table (clausules|subquery)*     #subquery_ambClausules
                  ;

plot : 'plot' alias ';' ;

select_list : '*'                                           #selectAll
            | select_item (',' select_item)*                #selectPersonalitzat
            ;


select_item : column_name                                   #columna_simple
            | expression 'as' alias                         #columna_amb_expressio
            ;

expression : '(' expression ')'                             #parentesis
           | expression ('*' | '/') expression              #binari
           | expression ('+' | '-') expression              #binari
           | NUM                                            #numero
           | ID                                             #columna
           ;

orderby    : 'order by' columnes_dordenacio;

columnes_dordenacio : columnes_dordenaciosintaxis (',' columnes_dordenaciosintaxis)*;

columnes_dordenaciosintaxis : column_name                   #col_asc
                            | column_name 'asc'             #col_asc_especificat
                            | column_name 'desc'            #col_desc
                            ;

where      : 'where' condition;

condition        : 'not' '(' condition ')'                  #not_parentesis_where
                 | '(' condition ')'                        #parentesis_where
                 | condition 'and' condition                #and
                 | comparison_condition                     #arimetriques
                 ;

comparison_condition : 'not' column_name '<' NUM            #not_menor
                     | 'not' column_name '=' NUM            #not_igual
                     | 'not' column_name '=' column_name    #not_igual_string
                     | 'not' column_name '=' 'null'         #not_columna_amb_buits
                     | column_name '<' NUM                  #menor
                     | column_name '=' NUM                  #igual
                     | column_name '=' 'null'               #columna_amb_buits
                     | column_name '=' column_name          #igual_string
                     ;

join_clauses   : innerjoin+;

innerjoin: 'inner join' table 'on' column_name '=' column_name ;

column_name : ID;

alias : ID;

table : ID;

NUM : [0-9]+ ('.' [0-9]+)?;

ID : [a-zA-Z_]+;

WS : [ \t\r\n]+ -> skip;
