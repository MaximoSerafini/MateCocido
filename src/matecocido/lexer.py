"""
Fase 1 — Analizador Léxico (scanner / tokenizer) de Mate Cocido.

Recorre el código fuente carácter por carácter y produce la secuencia de
tokens. Está implementado a mano como un **autómata finito**: en cada paso, el
carácter actual determina qué subrutina de reconocimiento ejecutar
(número, identificador, cadena, operador, etc.).

Lleva el control de **línea y columna** para que todas las fases posteriores
puedan reportar errores con ubicación precisa.
"""

from __future__ import annotations

from .errores import ErrorLexico
from .tokens import PALABRAS_RESERVADAS, Token, TipoToken


class Lexer:
    """Convierte una cadena de código fuente en una lista de `Token`."""

    def __init__(self, fuente: str):
        self.fuente = fuente
        self.pos = 0          # índice del carácter actual
        self.linea = 1
        self.columna = 1
        self.tokens: list[Token] = []

    # ------------------------------------------------------------------ #
    # Utilidades de bajo nivel sobre el flujo de caracteres
    # ------------------------------------------------------------------ #
    def _fin(self) -> bool:
        """¿Llegamos al final del fuente?"""
        return self.pos >= len(self.fuente)

    def _actual(self) -> str:
        """Carácter actual sin consumir (cadena vacía si es fin)."""
        if self._fin():
            return ""
        return self.fuente[self.pos]

    def _siguiente(self) -> str:
        """Carácter siguiente al actual sin consumir (lookahead de 1)."""
        if self.pos + 1 >= len(self.fuente):
            return ""
        return self.fuente[self.pos + 1]

    def _avanzar(self) -> str:
        """Consume y devuelve el carácter actual, actualizando línea/columna."""
        c = self.fuente[self.pos]
        self.pos += 1
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    def _agregar(self, tipo: TipoToken, lexema: str, linea: int, columna: int,
                 valor: object = None) -> None:
        self.tokens.append(Token(tipo, lexema, linea, columna, valor))

    # ------------------------------------------------------------------ #
    # Bucle principal
    # ------------------------------------------------------------------ #
    def tokenizar(self) -> list[Token]:
        """Escanea todo el fuente y devuelve la lista de tokens (con EOF al final)."""
        while not self._fin():
            c = self._actual()

            # 1) Espacios en blanco -> se ignoran
            if c in " \t\r\n":
                self._avanzar()
                continue

            # 2) Comentarios
            if c == "/" and self._siguiente() == "/":
                self._comentario_linea()
                continue
            if c == "/" and self._siguiente() == "*":
                self._comentario_bloque()
                continue

            # 3) Números
            if c.isdigit():
                self._numero()
                continue

            # 4) Identificadores y palabras reservadas
            if c.isalpha() or c == "_":
                self._identificador()
                continue

            # 5) Cadenas de texto
            if c == '"':
                self._cadena()
                continue

            # 6) Operadores y delimitadores
            self._simbolo()

        self._agregar(TipoToken.EOF, "", self.linea, self.columna)
        return self.tokens

    # ------------------------------------------------------------------ #
    # Reconocedores específicos (cada uno es un estado del autómata)
    # ------------------------------------------------------------------ #
    def _comentario_linea(self) -> None:
        """Descarta desde `//` hasta el fin de línea."""
        while not self._fin() and self._actual() != "\n":
            self._avanzar()

    def _comentario_bloque(self) -> None:
        """Descarta desde `/*` hasta `*/`. Error si no se cierra."""
        linea_ini, col_ini = self.linea, self.columna
        self._avanzar()  # /
        self._avanzar()  # *
        while not self._fin():
            if self._actual() == "*" and self._siguiente() == "/":
                self._avanzar()  # *
                self._avanzar()  # /
                return
            self._avanzar()
        raise ErrorLexico("Comentario de bloque sin cerrar (falta '*/')",
                          linea_ini, col_ini)

    def _numero(self) -> None:
        """Reconoce ENTERO o FLOTANTE: [0-9]+ ( '.' [0-9]+ )?"""
        linea, columna = self.linea, self.columna
        inicio = self.pos
        while not self._fin() and self._actual().isdigit():
            self._avanzar()

        es_flotante = False
        # Solo es flotante si hay un dígito después del punto (1.5),
        # no en casos como "1." que dejaríamos como error o entero+punto.
        if self._actual() == "." and self._siguiente().isdigit():
            es_flotante = True
            self._avanzar()  # consume '.'
            while not self._fin() and self._actual().isdigit():
                self._avanzar()

        lexema = self.fuente[inicio:self.pos]
        if es_flotante:
            self._agregar(TipoToken.FLOTANTE, lexema, linea, columna, float(lexema))
        else:
            self._agregar(TipoToken.ENTERO, lexema, linea, columna, int(lexema))

    def _identificador(self) -> None:
        """Reconoce IDENT y resuelve si es palabra reservada."""
        linea, columna = self.linea, self.columna
        inicio = self.pos
        while not self._fin() and (self._actual().isalnum() or self._actual() == "_"):
            self._avanzar()

        lexema = self.fuente[inicio:self.pos]
        tipo = PALABRAS_RESERVADAS.get(lexema, TipoToken.IDENT)

        # Los literales booleanos llevan su valor ya interpretado.
        if tipo == TipoToken.POSTA:
            self._agregar(tipo, lexema, linea, columna, True)
        elif tipo == TipoToken.TRUCHO:
            self._agregar(tipo, lexema, linea, columna, False)
        else:
            self._agregar(tipo, lexema, linea, columna)

    def _cadena(self) -> None:
        """Reconoce CADENA: '"' ... '"' con escapes \\n \\t \\" \\\\."""
        linea, columna = self.linea, self.columna
        self._avanzar()  # comilla de apertura
        partes: list[str] = []
        while not self._fin() and self._actual() != '"':
            c = self._avanzar()
            if c == "\n":
                raise ErrorLexico("Cadena sin cerrar (salto de línea dentro de la cadena)",
                                  linea, columna)
            if c == "\\":  # secuencia de escape
                if self._fin():
                    break
                esc = self._avanzar()
                partes.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc))
            else:
                partes.append(c)

        if self._fin():
            raise ErrorLexico("Cadena sin cerrar (falta comilla de cierre)", linea, columna)

        self._avanzar()  # comilla de cierre
        valor = "".join(partes)
        self._agregar(TipoToken.CADENA, f'"{valor}"', linea, columna, valor)

    def _simbolo(self) -> None:
        """Reconoce operadores y delimitadores (incluye los de dos caracteres)."""
        linea, columna = self.linea, self.columna
        c = self._avanzar()
        sig = self._actual()

        # Operadores de dos caracteres
        dobles = {
            "==": TipoToken.IGUAL_IGUAL,
            "!=": TipoToken.DISTINTO,
            "<=": TipoToken.MENOR_IGUAL,
            ">=": TipoToken.MAYOR_IGUAL,
        }
        par = c + sig
        if par in dobles:
            self._avanzar()
            self._agregar(dobles[par], par, linea, columna)
            return

        # Operadores y delimitadores de un carácter
        simples = {
            "+": TipoToken.MAS,
            "-": TipoToken.MENOS,
            "*": TipoToken.POR,
            "/": TipoToken.DIV,
            "%": TipoToken.MOD,
            "<": TipoToken.MENOR,
            ">": TipoToken.MAYOR,
            "=": TipoToken.ASIGNA,
            "(": TipoToken.PAR_IZQ,
            ")": TipoToken.PAR_DER,
            "{": TipoToken.LLAVE_IZQ,
            "}": TipoToken.LLAVE_DER,
            ";": TipoToken.PUNTO_COMA,
            ",": TipoToken.COMA,
        }
        if c in simples:
            self._agregar(simples[c], c, linea, columna)
            return

        # '!' suelto (sin '=') o cualquier otro carácter es un error léxico.
        raise ErrorLexico(f"Carácter no reconocido: {c!r}", linea, columna)


def tokenizar(fuente: str) -> list[Token]:
    """Función de conveniencia: tokeniza una cadena de código fuente."""
    return Lexer(fuente).tokenizar()
