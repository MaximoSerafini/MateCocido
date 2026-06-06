"""
Compilador de Mate Cocido — interfaz de línea de comandos.

Orquesta las tres fases del compilador sobre un archivo `.mate`:

    Fase 1  Léxico     fuente  -> tokens
    Fase 2  Sintáctico tokens  -> AST
    Fase 3  Semántico  AST     -> tabla de símbolos (validada)

Uso:
    python src/main.py <archivo.mate>            # compila y muestra el resumen
    python src/main.py <archivo.mate> --tokens   # además muestra los tokens
    python src/main.py <archivo.mate> --ast      # además muestra el AST
    python src/main.py <archivo.mate> --tabla    # además muestra la tabla de símbolos
    python src/main.py <archivo.mate> --todo     # muestra todo el detalle
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el archivo directamente (python src/main.py ...).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from matecocido import imprimir
from matecocido.errores import ErrorCompilacion
from matecocido.lexer import tokenizar
from matecocido.parser import parsear
from matecocido.semantic import analizar


def _reconfigurar_consola() -> None:
    """Fuerza UTF-8 en la salida para que los acentos se vean en Windows."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def _titulo(texto: str) -> str:
    return f"\n{'═' * 60}\n  {texto}\n{'═' * 60}"


def compilar(ruta: Path, mostrar_tokens: bool, mostrar_ast: bool,
             mostrar_tabla: bool) -> int:
    """Ejecuta las tres fases. Devuelve un código de salida (0 = OK)."""
    fuente = ruta.read_text(encoding="utf-8")
    print(f"Compilando: {ruta.name}")

    try:
        # ---- Fase 1: Léxico ----
        tokens = tokenizar(fuente)
        print("  ✔ Fase 1 (Léxico):     OK  "
              f"— {len(tokens)} tokens")
        if mostrar_tokens:
            print(_titulo("TOKENS"))
            print(imprimir.formatear_tokens(tokens))

        # ---- Fase 2: Sintáctico ----
        arbol = parsear(tokens)
        print("  ✔ Fase 2 (Sintáctico): OK  — AST construido")
        if mostrar_ast:
            print(_titulo("ÁRBOL DE SINTAXIS ABSTRACTA (AST)"))
            print(imprimir.formatear_ast(arbol))

        # ---- Fase 3: Semántico ----
        tabla = analizar(arbol)
        print("  ✔ Fase 3 (Semántico):  OK  — sin errores de tipos ni de ámbito")
        if mostrar_tabla:
            print(_titulo("TABLA DE SÍMBOLOS"))
            print(imprimir.formatear_tabla(tabla))

    except ErrorCompilacion as e:
        print()
        print(e.formatear())
        print("\n✘ La compilación falló.")
        return 1

    print(f"\n✔ ¡Listo el pomo! '{ruta.name}' compiló sin errores.")
    return 0


def main(argv: list[str] | None = None) -> int:
    _reconfigurar_consola()
    parser = argparse.ArgumentParser(
        description="Compilador del lenguaje Mate Cocido (TPI Teoría de la Computación).",
    )
    parser.add_argument("archivo", type=Path, help="archivo fuente .mate a compilar")
    parser.add_argument("--tokens", action="store_true", help="mostrar la lista de tokens (Fase 1)")
    parser.add_argument("--ast", action="store_true", help="mostrar el AST (Fase 2)")
    parser.add_argument("--tabla", action="store_true", help="mostrar la tabla de símbolos (Fase 3)")
    parser.add_argument("--todo", action="store_true", help="mostrar tokens, AST y tabla")
    args = parser.parse_args(argv)

    if not args.archivo.exists():
        print(f"No existe el archivo: {args.archivo}")
        return 2

    return compilar(
        args.archivo,
        mostrar_tokens=args.tokens or args.todo,
        mostrar_ast=args.ast or args.todo,
        mostrar_tabla=args.tabla or args.todo,
    )


if __name__ == "__main__":
    raise SystemExit(main())
