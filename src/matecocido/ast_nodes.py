"""
Nodos del Árbol de Sintaxis Abstracta (AST) de Mate Cocido.

El analizador sintáctico construye un árbol con estas clases. Cada nodo
representa una construcción del lenguaje (un programa, una sentencia, una
expresión). El analizador semántico luego recorre este árbol.

Todos los nodos guardan `linea` y `columna` para poder reportar errores
semánticos con ubicación precisa.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ====================================================================== #
# Nodo base
# ====================================================================== #
@dataclass
class Nodo:
    """Nodo base con posición en el código fuente."""
    linea: int = field(default=0, kw_only=True)
    columna: int = field(default=0, kw_only=True)


# ====================================================================== #
# Programa y estructura
# ====================================================================== #
@dataclass
class Programa(Nodo):
    """`mate <nombre> { arrancar() { <cuerpo> } }`"""
    nombre: str
    cuerpo: list[Nodo]


# ====================================================================== #
# Sentencias
# ====================================================================== #
@dataclass
class Declaracion(Nodo):
    """`cebar <tipo> <nombre> [= <valor>];`"""
    tipo: str            # "entero" | "flota" | "palabra" | "bool"
    nombre: str
    valor: Nodo | None   # expresión inicial o None


@dataclass
class Asignacion(Nodo):
    """`<nombre> = <valor>;`"""
    nombre: str
    valor: Nodo


@dataclass
class Si(Nodo):
    """`si (<condicion>) { <entonces> } [sino { <sino> }]`"""
    condicion: Nodo
    entonces: list[Nodo]
    sino: list[Nodo] | None


@dataclass
class Mientras(Nodo):
    """`mientras (<condicion>) { <cuerpo> }`"""
    condicion: Nodo
    cuerpo: list[Nodo]


@dataclass
class Che(Nodo):
    """`che(<expresion>);`  (salida estándar)"""
    expresion: Nodo


@dataclass
class Devolver(Nodo):
    """`dame [<expresion>];`"""
    expresion: Nodo | None


# ====================================================================== #
# Expresiones
# ====================================================================== #
@dataclass
class Binaria(Nodo):
    """Operación binaria: `<izq> <op> <der>`."""
    op: str
    izquierda: Nodo
    derecha: Nodo


@dataclass
class Unaria(Nodo):
    """Operación unaria: `<op> <operando>` (no x, -x)."""
    op: str
    operando: Nodo


@dataclass
class Literal(Nodo):
    """Valor constante: entero, flotante, cadena o booleano."""
    valor: object
    tipo: str            # "entero" | "flota" | "palabra" | "bool"


@dataclass
class Variable(Nodo):
    """Uso de una variable por su nombre."""
    nombre: str
