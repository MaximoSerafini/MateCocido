"""
Utilidades de presentación: muestran de forma legible los resultados de cada
fase del compilador (tokens, AST como árbol ASCII, tabla de símbolos).

Sirven tanto para depurar como para que el resultado del compilador sea
didáctico en la defensa del TPI.
"""

from __future__ import annotations

from . import ast_nodes as ast
from .semantic import TablaSimbolos
from .tokens import Token


# ---------------------------------------------------------------------- #
# Tokens
# ---------------------------------------------------------------------- #
def formatear_tokens(tokens: list[Token]) -> str:
    filas = ["  #  | TIPO            | LEXEMA            | LÍNEA:COL",
             "-----+-----------------+-------------------+----------"]
    for i, t in enumerate(tokens):
        lexema = t.lexema if t.lexema else "ε"
        filas.append(f"{i:>4} | {t.tipo.name:<15} | {lexema:<17} | {t.linea}:{t.columna}")
    return "\n".join(filas)


# ---------------------------------------------------------------------- #
# AST como árbol ASCII
# ---------------------------------------------------------------------- #
def formatear_ast(programa: ast.Programa) -> str:
    lineas: list[str] = [f"Programa '{programa.nombre}'"]
    _hijos(programa.cuerpo, "", lineas)
    return "\n".join(lineas)


def _rama(prefijo: str, ultimo: bool) -> tuple[str, str]:
    """Devuelve (conector, prefijo_para_hijos)."""
    if ultimo:
        return prefijo + "└─ ", prefijo + "   "
    return prefijo + "├─ ", prefijo + "│  "


def _hijos(nodos: list[ast.Nodo], prefijo: str, out: list[str]) -> None:
    for i, n in enumerate(nodos):
        _nodo(n, prefijo, i == len(nodos) - 1, out)


def _nodo(n: ast.Nodo, prefijo: str, ultimo: bool, out: list[str]) -> None:
    conector, hijo_prefijo = _rama(prefijo, ultimo)

    if isinstance(n, ast.Declaracion):
        out.append(f"{conector}Declaracion: cebar {n.tipo} {n.nombre}")
        if n.valor is not None:
            _nodo(n.valor, hijo_prefijo, True, out)

    elif isinstance(n, ast.Asignacion):
        out.append(f"{conector}Asignacion: {n.nombre} =")
        _nodo(n.valor, hijo_prefijo, True, out)

    elif isinstance(n, ast.Si):
        out.append(f"{conector}Si")
        _etiqueta(hijo_prefijo, "condicion", [n.condicion], out, n.sino is None and not n.entonces)
        _etiqueta(hijo_prefijo, "entonces", n.entonces, out, n.sino is None)
        if n.sino is not None:
            _etiqueta(hijo_prefijo, "sino", n.sino, out, True)

    elif isinstance(n, ast.Mientras):
        out.append(f"{conector}Mientras")
        _etiqueta(hijo_prefijo, "condicion", [n.condicion], out, False)
        _etiqueta(hijo_prefijo, "cuerpo", n.cuerpo, out, True)

    elif isinstance(n, ast.Che):
        out.append(f"{conector}Che")
        _nodo(n.expresion, hijo_prefijo, True, out)

    elif isinstance(n, ast.Devolver):
        out.append(f"{conector}Devolver")
        if n.expresion is not None:
            _nodo(n.expresion, hijo_prefijo, True, out)

    elif isinstance(n, ast.Binaria):
        out.append(f"{conector}Binaria '{n.op}'")
        _nodo(n.izquierda, hijo_prefijo, False, out)
        _nodo(n.derecha, hijo_prefijo, True, out)

    elif isinstance(n, ast.Unaria):
        out.append(f"{conector}Unaria '{n.op}'")
        _nodo(n.operando, hijo_prefijo, True, out)

    elif isinstance(n, ast.Literal):
        out.append(f"{conector}Literal {n.valor!r} ({n.tipo})")

    elif isinstance(n, ast.Variable):
        out.append(f"{conector}Variable '{n.nombre}'")

    else:
        out.append(f"{conector}{type(n).__name__}")


def _etiqueta(prefijo: str, nombre: str, nodos: list[ast.Nodo],
              out: list[str], ultimo: bool) -> None:
    conector, hijo_prefijo = _rama(prefijo, ultimo)
    out.append(f"{conector}{nombre}:")
    _hijos(nodos, hijo_prefijo, out)


# ---------------------------------------------------------------------- #
# Tabla de símbolos
# ---------------------------------------------------------------------- #
def formatear_tabla(tabla: TablaSimbolos) -> str:
    simbolos = tabla.aplanar()
    if not simbolos:
        return "(sin variables declaradas)"
    filas = ["NOMBRE          | TIPO    | LÍNEA | INICIALIZADA",
             "----------------+---------+-------+-------------"]
    for s in simbolos:
        filas.append(
            f"{s.nombre:<15} | {s.tipo:<7} | {s.linea:>5} | {'sí' if s.inicializada else 'no'}"
        )
    return "\n".join(filas)
