"""
Fase 3 — Analizador Semántico de Mate Cocido.

Recorre el AST y verifica que el programa, además de ser sintácticamente
correcto, tenga *sentido*:

  1. **Tabla de símbolos con ámbitos anidados**: cada bloque (`arrancar`, `si`,
     `mientras`) abre un ámbito. Una variable debe declararse antes de usarse y
     no puede redeclararse en el mismo ámbito.
  2. **Chequeo de tipos**: las operaciones se aplican sobre tipos compatibles,
     las condiciones de `si`/`mientras` deben ser `bool`, y una asignación debe
     respetar el tipo declarado de la variable.

Reúne *todos* los errores encontrados (no se detiene en el primero) y al final
lanza `ErrorSemantico` con el resumen, o devuelve la tabla de símbolos si el
programa es válido.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import ast_nodes as ast
from .errores import ErrorSemantico


@dataclass
class Simbolo:
    """Una entrada de la tabla de símbolos."""
    nombre: str
    tipo: str            # "entero" | "flota" | "palabra" | "bool"
    linea: int
    inicializada: bool


class TablaSimbolos:
    """
    Pila de ámbitos (scopes). Cada ámbito es un diccionario nombre -> Simbolo.
    El ámbito del tope es el más interno (el actual).
    """

    def __init__(self):
        self.ambitos: list[dict[str, Simbolo]] = [{}]

    def abrir_ambito(self) -> None:
        self.ambitos.append({})

    def cerrar_ambito(self) -> None:
        self.ambitos.pop()

    def declarar(self, simbolo: Simbolo) -> bool:
        """Declara en el ámbito actual. Devuelve False si ya existía allí."""
        actual = self.ambitos[-1]
        if simbolo.nombre in actual:
            return False
        actual[simbolo.nombre] = simbolo
        return True

    def buscar(self, nombre: str) -> Simbolo | None:
        """Busca de adentro hacia afuera (shadowing permitido)."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def aplanar(self) -> list[Simbolo]:
        """Todos los símbolos declarados (para mostrar la tabla al usuario)."""
        out: list[Simbolo] = []
        for ambito in self.ambitos:
            out.extend(ambito.values())
        return out


# Reglas de tipos para operadores binarios.
# Para cada operador, qué combinaciones de operandos acepta y qué tipo produce.
TIPOS_NUMERICOS = {"entero", "flota"}


class AnalizadorSemantico:
    """Recorre el AST acumulando símbolos y errores semánticos."""

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores: list[ErrorSemantico] = []

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def analizar(self, programa: ast.Programa) -> TablaSimbolos:
        for sentencia in programa.cuerpo:
            self._sentencia(sentencia)
        if self.errores:
            detalle = "\n".join("  - " + e.formatear() for e in self.errores)
            raise ErrorSemantico(
                f"Se encontraron {len(self.errores)} error(es) semántico(s):\n{detalle}"
            )
        return self.tabla

    def _error(self, mensaje: str, nodo: ast.Nodo) -> None:
        self.errores.append(ErrorSemantico(mensaje, nodo.linea, nodo.columna))

    # ------------------------------------------------------------------ #
    # Sentencias
    # ------------------------------------------------------------------ #
    def _sentencia(self, nodo: ast.Nodo) -> None:
        if isinstance(nodo, ast.Declaracion):
            self._declaracion(nodo)
        elif isinstance(nodo, ast.Asignacion):
            self._asignacion(nodo)
        elif isinstance(nodo, ast.Si):
            self._si(nodo)
        elif isinstance(nodo, ast.Mientras):
            self._mientras(nodo)
        elif isinstance(nodo, ast.Che):
            self._tipo_de(nodo.expresion)
        elif isinstance(nodo, ast.Devolver):
            if nodo.expresion is not None:
                self._tipo_de(nodo.expresion)

    def _bloque(self, sentencias: list[ast.Nodo]) -> None:
        self.tabla.abrir_ambito()
        for s in sentencias:
            self._sentencia(s)
        self.tabla.cerrar_ambito()

    def _declaracion(self, nodo: ast.Declaracion) -> None:
        inicializada = nodo.valor is not None
        if inicializada:
            tipo_valor = self._tipo_de(nodo.valor)
            if tipo_valor is not None and not self._compatible_asignacion(nodo.tipo, tipo_valor):
                self._error(
                    f"No se puede asignar un valor de tipo '{tipo_valor}' a la "
                    f"variable '{nodo.nombre}' de tipo '{nodo.tipo}'",
                    nodo,
                )
        simbolo = Simbolo(nodo.nombre, nodo.tipo, nodo.linea, inicializada)
        if not self.tabla.declarar(simbolo):
            self._error(
                f"La variable '{nodo.nombre}' ya fue declarada en este ámbito",
                nodo,
            )

    def _asignacion(self, nodo: ast.Asignacion) -> None:
        simbolo = self.tabla.buscar(nodo.nombre)
        tipo_valor = self._tipo_de(nodo.valor)
        if simbolo is None:
            self._error(
                f"Variable no declarada: '{nodo.nombre}' "
                f"(¿te olvidaste de cebarla con 'cebar'?)",
                nodo,
            )
            return
        if tipo_valor is not None and not self._compatible_asignacion(simbolo.tipo, tipo_valor):
            self._error(
                f"No se puede asignar un valor de tipo '{tipo_valor}' a la "
                f"variable '{nodo.nombre}' de tipo '{simbolo.tipo}'",
                nodo,
            )
        simbolo.inicializada = True

    def _si(self, nodo: ast.Si) -> None:
        self._verificar_condicion(nodo.condicion, "si")
        self._bloque(nodo.entonces)
        if nodo.sino is not None:
            self._bloque(nodo.sino)

    def _mientras(self, nodo: ast.Mientras) -> None:
        self._verificar_condicion(nodo.condicion, "mientras")
        self._bloque(nodo.cuerpo)

    def _verificar_condicion(self, cond: ast.Nodo, kw: str) -> None:
        tipo = self._tipo_de(cond)
        if tipo is not None and tipo != "bool":
            self._error(
                f"La condición de '{kw}' debe ser 'bool' pero es '{tipo}'", cond
            )

    # ------------------------------------------------------------------ #
    # Inferencia y chequeo de tipos de expresiones
    # ------------------------------------------------------------------ #
    def _tipo_de(self, nodo: ast.Nodo) -> str | None:
        """Devuelve el tipo de una expresión, o None si hubo error (ya reportado)."""
        if isinstance(nodo, ast.Literal):
            return nodo.tipo
        if isinstance(nodo, ast.Variable):
            return self._tipo_variable(nodo)
        if isinstance(nodo, ast.Unaria):
            return self._tipo_unaria(nodo)
        if isinstance(nodo, ast.Binaria):
            return self._tipo_binaria(nodo)
        return None

    def _tipo_variable(self, nodo: ast.Variable) -> str | None:
        simbolo = self.tabla.buscar(nodo.nombre)
        if simbolo is None:
            self._error(
                f"Variable no declarada: '{nodo.nombre}' "
                f"(¿te olvidaste de cebarla con 'cebar'?)",
                nodo,
            )
            return None
        if not simbolo.inicializada:
            self._error(
                f"La variable '{nodo.nombre}' se usa antes de tener un valor", nodo
            )
        return simbolo.tipo

    def _tipo_unaria(self, nodo: ast.Unaria) -> str | None:
        tipo = self._tipo_de(nodo.operando)
        if tipo is None:
            return None
        if nodo.op == "no":
            if tipo != "bool":
                self._error(f"El operador 'no' requiere un 'bool' pero recibió '{tipo}'", nodo)
                return None
            return "bool"
        if nodo.op == "-":
            if tipo not in TIPOS_NUMERICOS:
                self._error(f"El '-' unario requiere un número pero recibió '{tipo}'", nodo)
                return None
            return tipo
        return None

    def _tipo_binaria(self, nodo: ast.Binaria) -> str | None:
        ti = self._tipo_de(nodo.izquierda)
        td = self._tipo_de(nodo.derecha)
        if ti is None or td is None:
            return None
        op = nodo.op

        # Aritméticos
        if op in ("+", "-", "*", "/", "%"):
            # '+' también concatena palabras
            if op == "+" and ti == "palabra" and td == "palabra":
                return "palabra"
            if ti in TIPOS_NUMERICOS and td in TIPOS_NUMERICOS:
                # entero op entero = entero; si interviene flota, el resultado es flota
                return "flota" if "flota" in (ti, td) else "entero"
            self._error(
                f"El operador '{op}' no se puede aplicar entre '{ti}' y '{td}'", nodo
            )
            return None

        # Relacionales
        if op in ("<", ">", "<=", ">="):
            if ti in TIPOS_NUMERICOS and td in TIPOS_NUMERICOS:
                return "bool"
            self._error(
                f"El operador '{op}' requiere números pero recibió '{ti}' y '{td}'", nodo
            )
            return None

        # Igualdad
        if op in ("==", "!="):
            if ti == td or (ti in TIPOS_NUMERICOS and td in TIPOS_NUMERICOS):
                return "bool"
            self._error(
                f"No se pueden comparar con '{op}' los tipos '{ti}' y '{td}'", nodo
            )
            return None

        # Lógicos
        if op in ("y", "o"):
            if ti == "bool" and td == "bool":
                return "bool"
            self._error(
                f"El operador '{op}' requiere 'bool' pero recibió '{ti}' y '{td}'", nodo
            )
            return None

        return None

    # ------------------------------------------------------------------ #
    # Reglas auxiliares
    # ------------------------------------------------------------------ #
    @staticmethod
    def _compatible_asignacion(destino: str, origen: str) -> bool:
        """¿Se puede guardar un valor de tipo `origen` en una variable `destino`?"""
        if destino == origen:
            return True
        # Promoción implícita: un entero cabe en una flota.
        if destino == "flota" and origen == "entero":
            return True
        return False


def analizar(programa: ast.Programa) -> TablaSimbolos:
    """Función de conveniencia: analiza semánticamente un AST."""
    return AnalizadorSemantico().analizar(programa)
