"""
Fase 4 (opcional) — Intérprete de Mate Cocido.

Recorre el AST ya validado por las fases anteriores y lo **ejecuta**: crea las
variables, evalúa las expresiones, corre los `si`/`mientras` y, sobre todo, hace
que `che(...)` imprima de verdad.

Es un *intérprete de árbol* (tree-walking interpreter): la forma más directa de
darle vida a un lenguaje. No genera código de máquina; ejecuta el programa
caminando el árbol nodo por nodo.

Como el analizador semántico ya garantizó que los tipos y los ámbitos son
correctos, acá nos concentramos en *calcular*; solo quedan por vigilar errores
que dependen de los valores en tiempo de ejecución (como dividir por cero).
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errores import ErrorEjecucion


class _Retorno(Exception):
    """Señal interna para implementar `devolver` (corta la ejecución)."""

    def __init__(self, valor: object):
        self.valor = valor


class Entorno:
    """
    Pila de ámbitos en tiempo de ejecución: cada ámbito mapea
    nombre de variable -> valor actual. Refleja los mismos ámbitos que
    controló el analizador semántico.
    """

    def __init__(self):
        self.ambitos: list[dict[str, object]] = [{}]

    def abrir(self) -> None:
        self.ambitos.append({})

    def cerrar(self) -> None:
        self.ambitos.pop()

    def definir(self, nombre: str, valor: object) -> None:
        self.ambitos[-1][nombre] = valor

    def asignar(self, nombre: str, valor: object) -> None:
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                ambito[nombre] = valor
                return
        # No debería pasar: el semántico ya lo verificó.
        raise ErrorEjecucion(f"Variable no declarada en ejecución: '{nombre}'")

    def obtener(self, nombre: str) -> object:
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        raise ErrorEjecucion(f"Variable no declarada en ejecución: '{nombre}'")


class Interprete:
    """Ejecuta un AST de Mate Cocido y acumula lo que el programa imprime."""

    def __init__(self):
        self.entorno = Entorno()
        self.salida: list[str] = []

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def ejecutar(self, programa: ast.Programa) -> list[str]:
        """Corre el programa. Devuelve la lista de líneas impresas por `che`."""
        try:
            for sentencia in programa.cuerpo:
                self._sentencia(sentencia)
        except _Retorno:
            pass  # `devolver` en el cuerpo principal simplemente termina
        return self.salida

    # ------------------------------------------------------------------ #
    # Sentencias
    # ------------------------------------------------------------------ #
    def _sentencia(self, nodo: ast.Nodo) -> None:
        if isinstance(nodo, ast.Declaracion):
            valor = self._evaluar(nodo.valor) if nodo.valor is not None else None
            self.entorno.definir(nodo.nombre, valor)
        elif isinstance(nodo, ast.Asignacion):
            self.entorno.asignar(nodo.nombre, self._evaluar(nodo.valor))
        elif isinstance(nodo, ast.Si):
            if self._evaluar(nodo.condicion):
                self._bloque(nodo.entonces)
            elif nodo.sino is not None:
                self._bloque(nodo.sino)
        elif isinstance(nodo, ast.Mientras):
            while self._evaluar(nodo.condicion):
                self._bloque(nodo.cuerpo)
        elif isinstance(nodo, ast.Che):
            self.salida.append(self._formatear(self._evaluar(nodo.expresion)))
        elif isinstance(nodo, ast.Devolver):
            valor = self._evaluar(nodo.expresion) if nodo.expresion is not None else None
            raise _Retorno(valor)

    def _bloque(self, sentencias: list[ast.Nodo]) -> None:
        self.entorno.abrir()
        try:
            for s in sentencias:
                self._sentencia(s)
        finally:
            self.entorno.cerrar()

    # ------------------------------------------------------------------ #
    # Expresiones
    # ------------------------------------------------------------------ #
    def _evaluar(self, nodo: ast.Nodo) -> object:
        if isinstance(nodo, ast.Literal):
            return nodo.valor
        if isinstance(nodo, ast.Variable):
            return self.entorno.obtener(nodo.nombre)
        if isinstance(nodo, ast.Unaria):
            return self._unaria(nodo)
        if isinstance(nodo, ast.Binaria):
            return self._binaria(nodo)
        raise ErrorEjecucion(f"Nodo de expresión desconocido: {type(nodo).__name__}")

    def _unaria(self, nodo: ast.Unaria) -> object:
        valor = self._evaluar(nodo.operando)
        if nodo.op == "no":
            return not valor
        if nodo.op == "-":
            return -valor
        raise ErrorEjecucion(f"Operador unario desconocido: '{nodo.op}'")

    def _binaria(self, nodo: ast.Binaria) -> object:
        op = nodo.op

        # Operadores lógicos con cortocircuito (no evalúan el lado derecho de más).
        if op == "y":
            return bool(self._evaluar(nodo.izquierda)) and bool(self._evaluar(nodo.derecha))
        if op == "o":
            return bool(self._evaluar(nodo.izquierda)) or bool(self._evaluar(nodo.derecha))

        izq = self._evaluar(nodo.izquierda)
        der = self._evaluar(nodo.derecha)

        # Aritméticos
        if op == "+":
            return izq + der            # suma números o concatena palabras
        if op == "-":
            return izq - der
        if op == "*":
            return izq * der
        if op == "/":
            return self._dividir(izq, der, nodo)
        if op == "%":
            return self._modulo(izq, der, nodo)

        # Relacionales
        if op == "<":
            return izq < der
        if op == ">":
            return izq > der
        if op == "<=":
            return izq <= der
        if op == ">=":
            return izq >= der

        # Igualdad
        if op == "==":
            return izq == der
        if op == "!=":
            return izq != der

        raise ErrorEjecucion(f"Operador binario desconocido: '{op}'")

    # ------------------------------------------------------------------ #
    # Auxiliares de cálculo
    # ------------------------------------------------------------------ #
    def _dividir(self, izq: object, der: object, nodo: ast.Binaria) -> object:
        if der == 0:
            raise ErrorEjecucion("División por cero", nodo.linea, nodo.columna)
        # entero / entero = entero (división truncada hacia cero, como en Java).
        if isinstance(izq, int) and isinstance(der, int):
            return int(izq / der)
        return izq / der

    def _modulo(self, izq: object, der: object, nodo: ast.Binaria) -> object:
        if der == 0:
            raise ErrorEjecucion("Módulo por cero", nodo.linea, nodo.columna)
        # Resto consistente con la división truncada hacia cero.
        return izq - int(izq / der) * der

    @staticmethod
    def _formatear(valor: object) -> str:
        """Convierte un valor a texto para mostrarlo con `che`."""
        if isinstance(valor, bool):
            return "posta" if valor else "trucho"   # fiel al lenguaje
        if valor is None:
            return "nada"
        return str(valor)


def ejecutar(programa: ast.Programa) -> list[str]:
    """Función de conveniencia: ejecuta un AST y devuelve su salida."""
    return Interprete().ejecutar(programa)
