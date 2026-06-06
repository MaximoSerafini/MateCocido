"""
Excepciones del compilador Mate Cocido.

Cada fase del compilador lanza su propia excepción, todas derivadas de
`ErrorCompilacion`. Esto permite distinguir en qué fase falló la compilación
y mostrar un mensaje uniforme con la posición del error.
"""

from __future__ import annotations


class ErrorCompilacion(Exception):
    """Error base de todas las fases del compilador."""

    fase = "compilación"

    def __init__(self, mensaje: str, linea: int | None = None, columna: int | None = None):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        super().__init__(self.formatear())

    def formatear(self) -> str:
        ubicacion = ""
        if self.linea is not None:
            ubicacion = f" (línea {self.linea}"
            if self.columna is not None:
                ubicacion += f", columna {self.columna}"
            ubicacion += ")"
        return f"[Error {self.fase}]{ubicacion}: {self.mensaje}"


class ErrorLexico(ErrorCompilacion):
    """Carácter o secuencia no válida durante el análisis léxico."""

    fase = "léxico"


class ErrorSintactico(ErrorCompilacion):
    """Secuencia de tokens que no respeta la gramática."""

    fase = "sintáctico"


class ErrorSemantico(ErrorCompilacion):
    """Programa bien formado pero con significado inválido (tipos, ámbitos)."""

    fase = "semántico"


class ErrorEjecucion(ErrorCompilacion):
    """Error que solo aparece al ejecutar el programa (p. ej. división por cero)."""

    fase = "ejecución"
