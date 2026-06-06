"""
Definición de los tokens del lenguaje Mate Cocido.

Un *token* es la unidad léxica mínima con significado. El analizador léxico
(lexer) transforma el código fuente en una secuencia de objetos `Token`, que
luego consume el analizador sintáctico.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TipoToken(Enum):
    """Categorías de token reconocidas por el lenguaje."""

    # --- Literales -----------------------------------------------------
    ENTERO = auto()      # 42
    FLOTANTE = auto()    # 3.14
    CADENA = auto()      # "hola"
    IDENT = auto()       # nombre de variable

    # --- Palabras reservadas ------------------------------------------
    MATE = auto()        # mate
    ARRANCAR = auto()    # arrancar
    CEBAR = auto()       # cebar
    SI = auto()          # si
    SINO = auto()        # sino
    MIENTRAS = auto()    # mientras
    CHE = auto()         # che
    DEVOLVER = auto()    # dame

    # Tipos
    TIPO_ENTERO = auto()    # entero
    TIPO_FLOTA = auto()     # flota
    TIPO_PALABRA = auto()   # palabra
    TIPO_BOOL = auto()      # bool

    # Booleanos
    POSTA = auto()       # posta  (true)
    TRUCHO = auto()      # trucho (false)

    # Operadores lógicos (palabra)
    Y = auto()           # y
    O = auto()           # o
    NO = auto()          # no

    # --- Operadores ----------------------------------------------------
    MAS = auto()         # +
    MENOS = auto()       # -
    POR = auto()         # *
    DIV = auto()         # /
    MOD = auto()         # %

    IGUAL_IGUAL = auto() # ==
    DISTINTO = auto()    # !=
    MENOR = auto()       # <
    MAYOR = auto()       # >
    MENOR_IGUAL = auto() # <=
    MAYOR_IGUAL = auto() # >=

    ASIGNA = auto()      # =

    # --- Delimitadores -------------------------------------------------
    PAR_IZQ = auto()     # (
    PAR_DER = auto()     # )
    LLAVE_IZQ = auto()   # {
    LLAVE_DER = auto()   # }
    PUNTO_COMA = auto()  # ;
    COMA = auto()        # ,

    # --- Especial ------------------------------------------------------
    EOF = auto()         # fin de archivo


# Mapa de palabras reservadas: lexema -> tipo de token.
# Se consulta después de leer un identificador para distinguir una palabra
# reservada de un identificador común.
PALABRAS_RESERVADAS: dict[str, TipoToken] = {
    "mate": TipoToken.MATE,
    "arrancar": TipoToken.ARRANCAR,
    "cebar": TipoToken.CEBAR,
    "si": TipoToken.SI,
    "sino": TipoToken.SINO,
    "mientras": TipoToken.MIENTRAS,
    "che": TipoToken.CHE,
    "dame": TipoToken.DEVOLVER,
    "entero": TipoToken.TIPO_ENTERO,
    "flota": TipoToken.TIPO_FLOTA,
    "palabra": TipoToken.TIPO_PALABRA,
    "bool": TipoToken.TIPO_BOOL,
    "posta": TipoToken.POSTA,
    "trucho": TipoToken.TRUCHO,
    "y": TipoToken.Y,
    "o": TipoToken.O,
    "no": TipoToken.NO,
}

# Conjunto de tipos de token que representan un tipo de dato del lenguaje.
TIPOS_DE_DATO = {
    TipoToken.TIPO_ENTERO,
    TipoToken.TIPO_FLOTA,
    TipoToken.TIPO_PALABRA,
    TipoToken.TIPO_BOOL,
}


@dataclass
class Token:
    """
    Un token con su categoría, lexema y posición en el fuente.

    Atributos:
        tipo:    categoría del token (TipoToken).
        lexema:  texto exacto leído del código fuente.
        valor:   valor ya interpretado (int/float/str) para literales; None si no aplica.
        linea:   número de línea (base 1) donde empieza el token.
        columna: número de columna (base 1) donde empieza el token.
    """

    tipo: TipoToken
    lexema: str
    linea: int
    columna: int
    valor: object = None

    def __repr__(self) -> str:
        if self.valor is not None:
            return (
                f"Token({self.tipo.name}, {self.lexema!r}, "
                f"valor={self.valor!r}, {self.linea}:{self.columna})"
            )
        return f"Token({self.tipo.name}, {self.lexema!r}, {self.linea}:{self.columna})"
