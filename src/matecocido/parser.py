"""
Fase 2 — Analizador Sintáctico (parser) de Mate Cocido.

Implementa un **parser descendente recursivo** (recursive descent): hay un
método por cada regla no terminal de la gramática EBNF (`docs/gramatica.md`).
Consume la lista de tokens del lexer y produce el AST (`ast_nodes.py`).

La estratificación de las reglas de expresión (`_exp_o`, `_exp_y`, ...) codifica
directamente la **precedencia** y **asociatividad izquierda** de los operadores.
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errores import ErrorSintactico
from .tokens import TIPOS_DE_DATO, Token, TipoToken


class Parser:
    """Construye el AST a partir de la lista de tokens."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------------ #
    # Utilidades sobre el flujo de tokens
    # ------------------------------------------------------------------ #
    def _actual(self) -> Token:
        return self.tokens[self.pos]

    def _verificar(self, tipo: TipoToken) -> bool:
        """¿El token actual es del tipo dado?"""
        return self._actual().tipo == tipo

    def _avanzar(self) -> Token:
        """Consume y devuelve el token actual."""
        tok = self.tokens[self.pos]
        if tok.tipo != TipoToken.EOF:
            self.pos += 1
        return tok

    def _aceptar(self, tipo: TipoToken) -> Token | None:
        """Consume el token actual si coincide; si no, devuelve None."""
        if self._verificar(tipo):
            return self._avanzar()
        return None

    def _esperar(self, tipo: TipoToken, descripcion: str) -> Token:
        """Consume el token esperado o lanza un error sintáctico."""
        if self._verificar(tipo):
            return self._avanzar()
        tok = self._actual()
        lexema = tok.lexema if tok.tipo != TipoToken.EOF else "fin de archivo"
        raise ErrorSintactico(
            f"Se esperaba {descripcion} pero se encontró '{lexema}'",
            tok.linea, tok.columna,
        )

    # ------------------------------------------------------------------ #
    # Punto de entrada
    # ------------------------------------------------------------------ #
    def parsear(self) -> ast.Programa:
        """programa = 'mate' IDENT '{' 'arrancar' '(' ')' bloque '}'"""
        inicio = self._esperar(TipoToken.MATE, "la palabra 'mate' al inicio del programa")
        nombre = self._esperar(TipoToken.IDENT, "el nombre del programa")
        self._esperar(TipoToken.LLAVE_IZQ, "'{' después del nombre del programa")
        self._esperar(TipoToken.ARRANCAR, "el método 'arrancar'")
        self._esperar(TipoToken.PAR_IZQ, "'(' después de 'arrancar'")
        self._esperar(TipoToken.PAR_DER, "')'")
        cuerpo = self._bloque()
        self._esperar(TipoToken.LLAVE_DER, "'}' para cerrar el programa")
        self._esperar(TipoToken.EOF, "el fin del archivo")
        return ast.Programa(nombre.lexema, cuerpo, linea=inicio.linea, columna=inicio.columna)

    # ------------------------------------------------------------------ #
    # Sentencias
    # ------------------------------------------------------------------ #
    def _bloque(self) -> list[ast.Nodo]:
        """bloque = '{' { sentencia } '}'"""
        self._esperar(TipoToken.LLAVE_IZQ, "'{' para abrir un bloque")
        sentencias: list[ast.Nodo] = []
        while not self._verificar(TipoToken.LLAVE_DER) and not self._verificar(TipoToken.EOF):
            sentencias.append(self._sentencia())
        self._esperar(TipoToken.LLAVE_DER, "'}' para cerrar el bloque")
        return sentencias

    def _sentencia(self) -> ast.Nodo:
        """Despacha según el token actual a la regla de sentencia correspondiente."""
        tok = self._actual()
        if tok.tipo == TipoToken.CEBAR:
            return self._declaracion()
        if tok.tipo == TipoToken.SI:
            return self._sent_si()
        if tok.tipo == TipoToken.MIENTRAS:
            return self._sent_mientras()
        if tok.tipo == TipoToken.CHE:
            return self._sent_che()
        if tok.tipo == TipoToken.DEVOLVER:
            return self._sent_devolver()
        if tok.tipo == TipoToken.IDENT:
            return self._asignacion()
        raise ErrorSintactico(
            f"Sentencia no válida: no se esperaba '{tok.lexema or 'fin de archivo'}'",
            tok.linea, tok.columna,
        )

    def _declaracion(self) -> ast.Declaracion:
        """declaracion = 'cebar' tipo IDENT [ '=' expresion ] ';'"""
        ini = self._avanzar()  # 'cebar'
        tok_tipo = self._actual()
        if tok_tipo.tipo not in TIPOS_DE_DATO:
            raise ErrorSintactico(
                f"Se esperaba un tipo (entero, flota, palabra, bool) "
                f"pero se encontró '{tok_tipo.lexema}'",
                tok_tipo.linea, tok_tipo.columna,
            )
        self._avanzar()
        nombre = self._esperar(TipoToken.IDENT, "el nombre de la variable")
        valor: ast.Nodo | None = None
        if self._aceptar(TipoToken.ASIGNA):
            valor = self._expresion()
        self._esperar(TipoToken.PUNTO_COMA, "';' al final de la declaración")
        return ast.Declaracion(tok_tipo.lexema, nombre.lexema, valor,
                               linea=ini.linea, columna=ini.columna)

    def _asignacion(self) -> ast.Asignacion:
        """asignacion = IDENT '=' expresion ';'"""
        nombre = self._avanzar()  # IDENT
        self._esperar(TipoToken.ASIGNA, f"'=' para asignar a '{nombre.lexema}'")
        valor = self._expresion()
        self._esperar(TipoToken.PUNTO_COMA, "';' al final de la asignación")
        return ast.Asignacion(nombre.lexema, valor, linea=nombre.linea, columna=nombre.columna)

    def _sent_si(self) -> ast.Si:
        """sent_si = 'si' '(' expresion ')' bloque [ 'sino' bloque ]"""
        ini = self._avanzar()  # 'si'
        self._esperar(TipoToken.PAR_IZQ, "'(' después de 'si'")
        condicion = self._expresion()
        self._esperar(TipoToken.PAR_DER, "')' después de la condición")
        entonces = self._bloque()
        sino: list[ast.Nodo] | None = None
        if self._aceptar(TipoToken.SINO):
            sino = self._bloque()
        return ast.Si(condicion, entonces, sino, linea=ini.linea, columna=ini.columna)

    def _sent_mientras(self) -> ast.Mientras:
        """sent_mientras = 'mientras' '(' expresion ')' bloque"""
        ini = self._avanzar()  # 'mientras'
        self._esperar(TipoToken.PAR_IZQ, "'(' después de 'mientras'")
        condicion = self._expresion()
        self._esperar(TipoToken.PAR_DER, "')' después de la condición")
        cuerpo = self._bloque()
        return ast.Mientras(condicion, cuerpo, linea=ini.linea, columna=ini.columna)

    def _sent_che(self) -> ast.Che:
        """sent_che = 'che' '(' expresion ')' ';'"""
        ini = self._avanzar()  # 'che'
        self._esperar(TipoToken.PAR_IZQ, "'(' después de 'che'")
        expr = self._expresion()
        self._esperar(TipoToken.PAR_DER, "')' después de la expresión")
        self._esperar(TipoToken.PUNTO_COMA, "';' al final de 'che'")
        return ast.Che(expr, linea=ini.linea, columna=ini.columna)

    def _sent_devolver(self) -> ast.Devolver:
        """sent_devolver = 'devolver' [ expresion ] ';'"""
        ini = self._avanzar()  # 'devolver'
        expr: ast.Nodo | None = None
        if not self._verificar(TipoToken.PUNTO_COMA):
            expr = self._expresion()
        self._esperar(TipoToken.PUNTO_COMA, "';' al final de 'devolver'")
        return ast.Devolver(expr, linea=ini.linea, columna=ini.columna)

    # ------------------------------------------------------------------ #
    # Expresiones (estratificadas por precedencia, asociatividad izq.)
    # ------------------------------------------------------------------ #
    def _expresion(self) -> ast.Nodo:
        return self._exp_o()

    def _binaria_izq(self, sub_regla, tipos_op: dict[TipoToken, str]) -> ast.Nodo:
        """
        Patrón común: regla = sub_regla { OP sub_regla }.
        Construye un árbol asociativo a la izquierda.
        """
        nodo = sub_regla()
        while self._actual().tipo in tipos_op:
            op_tok = self._avanzar()
            derecha = sub_regla()
            nodo = ast.Binaria(tipos_op[op_tok.tipo], nodo, derecha,
                              linea=op_tok.linea, columna=op_tok.columna)
        return nodo

    def _exp_o(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_y, {TipoToken.O: "o"})

    def _exp_y(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_igual, {TipoToken.Y: "y"})

    def _exp_igual(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_rel, {
            TipoToken.IGUAL_IGUAL: "==",
            TipoToken.DISTINTO: "!=",
        })

    def _exp_rel(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_suma, {
            TipoToken.MENOR: "<",
            TipoToken.MAYOR: ">",
            TipoToken.MENOR_IGUAL: "<=",
            TipoToken.MAYOR_IGUAL: ">=",
        })

    def _exp_suma(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_term, {
            TipoToken.MAS: "+",
            TipoToken.MENOS: "-",
        })

    def _exp_term(self) -> ast.Nodo:
        return self._binaria_izq(self._exp_unaria, {
            TipoToken.POR: "*",
            TipoToken.DIV: "/",
            TipoToken.MOD: "%",
        })

    def _exp_unaria(self) -> ast.Nodo:
        """exp_unaria = ('no' | '-') exp_unaria | primaria"""
        tok = self._actual()
        if tok.tipo in (TipoToken.NO, TipoToken.MENOS):
            op = "no" if tok.tipo == TipoToken.NO else "-"
            self._avanzar()
            operando = self._exp_unaria()
            return ast.Unaria(op, operando, linea=tok.linea, columna=tok.columna)
        return self._primaria()

    def _primaria(self) -> ast.Nodo:
        """primaria = literal | IDENT | '(' expresion ')'"""
        tok = self._actual()

        if tok.tipo == TipoToken.ENTERO:
            self._avanzar()
            return ast.Literal(tok.valor, "entero", linea=tok.linea, columna=tok.columna)
        if tok.tipo == TipoToken.FLOTANTE:
            self._avanzar()
            return ast.Literal(tok.valor, "flota", linea=tok.linea, columna=tok.columna)
        if tok.tipo == TipoToken.CADENA:
            self._avanzar()
            return ast.Literal(tok.valor, "palabra", linea=tok.linea, columna=tok.columna)
        if tok.tipo in (TipoToken.POSTA, TipoToken.TRUCHO):
            self._avanzar()
            return ast.Literal(tok.valor, "bool", linea=tok.linea, columna=tok.columna)
        if tok.tipo == TipoToken.IDENT:
            self._avanzar()
            return ast.Variable(tok.lexema, linea=tok.linea, columna=tok.columna)
        if tok.tipo == TipoToken.PAR_IZQ:
            self._avanzar()
            expr = self._expresion()
            self._esperar(TipoToken.PAR_DER, "')' para cerrar la expresión entre paréntesis")
            return expr

        raise ErrorSintactico(
            f"Se esperaba una expresión pero se encontró '{tok.lexema or 'fin de archivo'}'",
            tok.linea, tok.columna,
        )


def parsear(tokens: list[Token]) -> ast.Programa:
    """Función de conveniencia: parsea una lista de tokens."""
    return Parser(tokens).parsear()
