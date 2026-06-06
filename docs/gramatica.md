# Gramática del lenguaje **Mate Cocido**

Mate Cocido es un lenguaje imperativo de juguete, parodia argentina de Java,
diseñado para el Trabajo Práctico Integrador de Teoría de la Computación.

La gramática se especifica en **EBNF** (Extended Backus–Naur Form) y es
**LL(1)**: puede reconocerse con un parser descendente recursivo de un solo
token de anticipación (*lookahead*), sin retroceso (*backtracking*).

---

## 1. Convenciones de notación EBNF

| Símbolo | Significado |
|---|---|
| `=` | definición de una regla |
| `;` | fin de una regla |
| `|` | alternativa |
| `[ ... ]` | opcional (0 o 1 vez) |
| `{ ... }` | repetición (0 o más veces) |
| `( ... )` | agrupación |
| `" ..."` | terminal literal |
| `MAYÚSCULAS` | categoría de token (terminal del léxico) |

---

## 2. Estructura general del programa

```ebnf
programa      = "mate" IDENT "{" "arrancar" "(" ")" bloque "}" ;

bloque        = "{" { sentencia } "}" ;
```

Todo programa tiene la forma:

```java
mate Cocido {
    arrancar() {
        // sentencias
    }
}
```

---

## 3. Sentencias

```ebnf
sentencia     = declaracion
              | asignacion
              | sent_si
              | sent_mientras
              | sent_che
              | sent_devolver ;

declaracion   = "cebar" tipo IDENT [ "=" expresion ] ";" ;

asignacion    = IDENT "=" expresion ";" ;

sent_si       = "si" "(" expresion ")" bloque [ "sino" bloque ] ;

sent_mientras = "mientras" "(" expresion ")" bloque ;

sent_che      = "che" "(" expresion ")" ";" ;

sent_devolver = "devolver" [ expresion ] ";" ;
```

---

## 4. Tipos

```ebnf
tipo          = "entero" | "flota" | "palabra" | "bool" ;
```

| Tipo Mate Cocido | Equivalente Java | Dominio |
|---|---|---|
| `entero` | `int` | enteros |
| `flota` | `double` | punto flotante |
| `palabra` | `String` | cadenas de texto |
| `bool` | `boolean` | `posta` / `trucho` |

---

## 5. Expresiones (con precedencia y asociatividad)

La gramática está estratificada para codificar la **precedencia de operadores**
(de menor a mayor) y la **asociatividad izquierda**:

```ebnf
expresion     = exp_o ;

exp_o         = exp_y      { "o"  exp_y } ;
exp_y         = exp_igual  { "y"  exp_igual } ;
exp_igual     = exp_rel    { ( "==" | "!=" ) exp_rel } ;
exp_rel       = exp_suma   { ( "<" | ">" | "<=" | ">=" ) exp_suma } ;
exp_suma      = exp_term   { ( "+" | "-" ) exp_term } ;
exp_term      = exp_unaria { ( "*" | "/" | "%" ) exp_unaria } ;
exp_unaria    = ( "no" | "-" ) exp_unaria
              | primaria ;

primaria      = ENTERO
              | FLOTANTE
              | CADENA
              | "posta"
              | "trucho"
              | IDENT
              | "(" expresion ")" ;
```

### Tabla de precedencia (de menor a mayor)

| Nivel | Operadores | Asociatividad |
|---|---|---|
| 1 | `o` | izquierda |
| 2 | `y` | izquierda |
| 3 | `==` `!=` | izquierda |
| 4 | `<` `>` `<=` `>=` | izquierda |
| 5 | `+` `-` | izquierda |
| 6 | `*` `/` `%` | izquierda |
| 7 | `no` `-` (unarios) | derecha |

---

## 6. Tokens (especificación léxica)

Definida con expresiones regulares sobre el alfabeto de entrada:

```
ENTERO     = [0-9]+
FLOTANTE   = [0-9]+ "." [0-9]+
CADENA     = "\"" { cualquier_caracter_excepto_comilla } "\""
IDENT      = [a-zA-Z_][a-zA-Z0-9_]*
```

### Palabras reservadas

`mate`, `arrancar`, `cebar`, `si`, `sino`, `mientras`, `che`, `devolver`,
`entero`, `flota`, `palabra`, `bool`, `posta`, `trucho`, `y`, `o`, `no`.

> Las palabras reservadas tienen prioridad sobre `IDENT`: una secuencia que
> coincide con una palabra reservada se tokeniza como tal, no como identificador.

### Símbolos y operadores

```
+  -  *  /  %        operadores aritméticos
==  !=  <  >  <=  >= operadores relacionales
=                    asignación
(  )  {  }           delimitadores
;  ,                 separadores
```

### Ignorados por el léxico

- Espacios, tabulaciones y saltos de línea (solo actualizan línea/columna).
- Comentarios de línea: `// ... ` hasta fin de línea.
- Comentarios de bloque: `/* ... */`.

---

## 7. Ejemplo completo

```java
mate Cocido {
    arrancar() {
        cebar entero edad = 18;
        cebar palabra saludo = "Cebá unos mates";

        si (edad >= 18 y edad < 100) {
            che(saludo);
        } sino {
            che("Todavía tomás la leche");
        }

        cebar entero i = 0;
        mientras (i < 3) {
            che(i);
            i = i + 1;
        }
    }
}
```
