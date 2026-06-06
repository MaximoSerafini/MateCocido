"""
Suite de tests del compilador Mate Cocido (unittest, sin dependencias).

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Hace importable el paquete `matecocido` desde src/.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from matecocido import ast_nodes as ast
from matecocido.errores import (ErrorEjecucion, ErrorLexico, ErrorSemantico,
                                ErrorSintactico)
from matecocido.interprete import ejecutar
from matecocido.lexer import tokenizar
from matecocido.parser import parsear
from matecocido.semantic import analizar
from matecocido.tokens import TipoToken


def compilar(fuente: str):
    """Atajo: corre las tres fases y devuelve (arbol, tabla)."""
    arbol = parsear(tokenizar(fuente))
    tabla = analizar(arbol)
    return arbol, tabla


def correr(fuente: str) -> list[str]:
    """Atajo: compila y ejecuta, devolviendo lo que el programa imprime."""
    arbol = parsear(tokenizar(fuente))
    analizar(arbol)
    return ejecutar(arbol)


PROGRAMA_MINIMO = """
mate Cocido {{
    arrancar() {{
        {cuerpo}
    }}
}}
"""


def envolver(cuerpo: str) -> str:
    return PROGRAMA_MINIMO.format(cuerpo=cuerpo)


# ====================================================================== #
# Fase 1 — Léxico
# ====================================================================== #
class TestLexer(unittest.TestCase):

    def test_tipos_de_token_basicos(self):
        toks = tokenizar("cebar entero x = 42;")
        tipos = [t.tipo for t in toks]
        self.assertEqual(tipos[0], TipoToken.CEBAR)
        self.assertEqual(tipos[1], TipoToken.TIPO_ENTERO)
        self.assertEqual(tipos[2], TipoToken.IDENT)
        self.assertEqual(tipos[3], TipoToken.ASIGNA)
        self.assertEqual(tipos[4], TipoToken.ENTERO)
        self.assertEqual(tipos[-1], TipoToken.EOF)

    def test_valor_entero_y_flotante(self):
        toks = tokenizar("42 3.14")
        self.assertEqual(toks[0].valor, 42)
        self.assertEqual(toks[1].tipo, TipoToken.FLOTANTE)
        self.assertEqual(toks[1].valor, 3.14)

    def test_operadores_dobles(self):
        toks = tokenizar("== != <= >=")
        tipos = [t.tipo for t in toks[:4]]
        self.assertEqual(tipos, [TipoToken.IGUAL_IGUAL, TipoToken.DISTINTO,
                                 TipoToken.MENOR_IGUAL, TipoToken.MAYOR_IGUAL])

    def test_cadena_con_escape(self):
        toks = tokenizar('"hola\\nchau"')
        self.assertEqual(toks[0].tipo, TipoToken.CADENA)
        self.assertEqual(toks[0].valor, "hola\nchau")

    def test_booleanos_tienen_valor(self):
        toks = tokenizar("posta trucho")
        self.assertIs(toks[0].valor, True)
        self.assertIs(toks[1].valor, False)

    def test_comentarios_se_ignoran(self):
        toks = tokenizar("// esto es un comentario\n/* y esto otro */ x")
        self.assertEqual(toks[0].tipo, TipoToken.IDENT)
        self.assertEqual(toks[0].lexema, "x")

    def test_linea_y_columna(self):
        toks = tokenizar("uno\n  dos")
        self.assertEqual((toks[0].linea, toks[0].columna), (1, 1))
        self.assertEqual((toks[1].linea, toks[1].columna), (2, 3))

    def test_caracter_invalido(self):
        with self.assertRaises(ErrorLexico):
            tokenizar("cebar entero x = 5 @ 3;")

    def test_cadena_sin_cerrar(self):
        with self.assertRaises(ErrorLexico):
            tokenizar('"sin cerrar')

    def test_comentario_bloque_sin_cerrar(self):
        with self.assertRaises(ErrorLexico):
            tokenizar("/* nunca termina")


# ====================================================================== #
# Fase 2 — Sintáctico
# ====================================================================== #
class TestParser(unittest.TestCase):

    def test_programa_minimo(self):
        arbol = parsear(tokenizar(envolver("")))
        self.assertIsInstance(arbol, ast.Programa)
        self.assertEqual(arbol.nombre, "Cocido")
        self.assertEqual(arbol.cuerpo, [])

    def test_declaracion_con_inicializacion(self):
        arbol = parsear(tokenizar(envolver("cebar entero x = 5;")))
        decl = arbol.cuerpo[0]
        self.assertIsInstance(decl, ast.Declaracion)
        self.assertEqual(decl.tipo, "entero")
        self.assertEqual(decl.nombre, "x")
        self.assertIsInstance(decl.valor, ast.Literal)

    def test_precedencia_multiplicacion_sobre_suma(self):
        # 2 + 3 * 4  debe ser  2 + (3 * 4)
        arbol = parsear(tokenizar(envolver("cebar entero x = 2 + 3 * 4;")))
        suma = arbol.cuerpo[0].valor
        self.assertEqual(suma.op, "+")
        self.assertIsInstance(suma.derecha, ast.Binaria)
        self.assertEqual(suma.derecha.op, "*")

    def test_asociatividad_izquierda_resta(self):
        # 10 - 3 - 2  debe ser  (10 - 3) - 2
        arbol = parsear(tokenizar(envolver("cebar entero x = 10 - 3 - 2;")))
        raiz = arbol.cuerpo[0].valor
        self.assertEqual(raiz.op, "-")
        self.assertIsInstance(raiz.izquierda, ast.Binaria)
        self.assertEqual(raiz.izquierda.op, "-")

    def test_parentesis_cambian_precedencia(self):
        # (2 + 3) * 4
        arbol = parsear(tokenizar(envolver("cebar entero x = (2 + 3) * 4;")))
        raiz = arbol.cuerpo[0].valor
        self.assertEqual(raiz.op, "*")
        self.assertIsInstance(raiz.izquierda, ast.Binaria)
        self.assertEqual(raiz.izquierda.op, "+")

    def test_si_sino(self):
        arbol = parsear(tokenizar(envolver(
            "cebar bool b = posta; si (b) { che(1); } sino { che(2); }")))
        nodo = arbol.cuerpo[1]
        self.assertIsInstance(nodo, ast.Si)
        self.assertIsNotNone(nodo.sino)

    def test_mientras(self):
        arbol = parsear(tokenizar(envolver(
            "cebar entero i = 0; mientras (i < 3) { i = i + 1; }")))
        self.assertIsInstance(arbol.cuerpo[1], ast.Mientras)

    def test_falta_punto_y_coma(self):
        with self.assertRaises(ErrorSintactico):
            parsear(tokenizar(envolver("cebar entero x = 5 che(x);")))

    def test_falta_llave(self):
        with self.assertRaises(ErrorSintactico):
            parsear(tokenizar("mate Cocido { arrancar() { "))

    def test_tipo_invalido_en_declaracion(self):
        with self.assertRaises(ErrorSintactico):
            parsear(tokenizar(envolver("cebar Cocido x = 5;")))


# ====================================================================== #
# Fase 3 — Semántico
# ====================================================================== #
class TestSemantico(unittest.TestCase):

    def test_programa_valido(self):
        _, tabla = compilar(envolver(
            "cebar entero x = 5; cebar entero z = x + 1; che(z);"))
        nombres = {s.nombre for s in tabla.aplanar()}
        self.assertEqual(nombres, {"x", "z"})

    def test_variable_no_declarada(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("x = 5;"))

    def test_redeclaracion_en_mismo_ambito(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("cebar entero x = 1; cebar entero x = 2;"))

    def test_asignacion_tipo_incompatible(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("cebar bool b = 5;"))

    def test_promocion_entero_a_flota(self):
        # asignar un entero a una flota es válido (promoción)
        _, tabla = compilar(envolver("cebar flota f = 5;"))
        self.assertTrue(any(s.nombre == "f" for s in tabla.aplanar()))

    def test_condicion_no_booleana(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("cebar entero x = 1; si (x + 1) { che(1); }"))

    def test_operador_aritmetico_sobre_tipos_invalidos(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver('cebar palabra s = "hola"; cebar entero n = s * 2;'))

    def test_concatenacion_de_palabras(self):
        _, tabla = compilar(envolver('cebar palabra s = "ce" + "bar";'))
        self.assertTrue(any(s.nombre == "s" for s in tabla.aplanar()))

    def test_logico_requiere_bool(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("cebar bool b = 1 y posta;"))

    def test_ambito_de_bloque(self):
        # 'z' se declara dentro del si y no existe afuera -> error al usarla fuera
        with self.assertRaises(ErrorSemantico):
            compilar(envolver(
                "cebar bool b = posta; si (b) { cebar entero z = 1; } che(z);"))

    def test_variable_usada_sin_inicializar(self):
        with self.assertRaises(ErrorSemantico):
            compilar(envolver("cebar entero x; che(x);"))


# ====================================================================== #
# Fase 4 — Intérprete (ejecución)
# ====================================================================== #
class TestInterprete(unittest.TestCase):

    def test_che_imprime(self):
        self.assertEqual(correr(envolver('che("hola");')), ["hola"])

    def test_aritmetica_entera(self):
        self.assertEqual(correr(envolver("che(2 + 3 * 4);")), ["14"])

    def test_division_entera_trunca(self):
        self.assertEqual(correr(envolver("che(7 / 2);")), ["3"])

    def test_division_flotante(self):
        self.assertEqual(correr(envolver("che(7.0 / 2);")), ["3.5"])

    def test_modulo(self):
        self.assertEqual(correr(envolver("che(7 % 3);")), ["1"])

    def test_booleano_se_muestra_como_palabra(self):
        self.assertEqual(correr(envolver("che(3 > 2);")), ["posta"])
        self.assertEqual(correr(envolver("che(3 < 2);")), ["trucho"])

    def test_concatenacion(self):
        self.assertEqual(correr(envolver('che("ce" + "bar");')), ["cebar"])

    def test_si_toma_la_rama_correcta(self):
        prog = "cebar entero x = 10; si (x > 5) { che(\"grande\"); } sino { che(\"chico\"); }"
        self.assertEqual(correr(envolver(prog)), ["grande"])

    def test_mientras_cuenta(self):
        prog = "cebar entero i = 0; mientras (i < 3) { che(i); i = i + 1; }"
        self.assertEqual(correr(envolver(prog)), ["0", "1", "2"])

    def test_factorial(self):
        prog = ("cebar entero n = 5; cebar entero f = 1; cebar entero i = 1; "
                "mientras (i <= n) { f = f * i; i = i + 1; } che(f);")
        self.assertEqual(correr(envolver(prog)), ["120"])

    def test_logicos_con_cortocircuito(self):
        self.assertEqual(correr(envolver("che(posta y trucho);")), ["trucho"])
        self.assertEqual(correr(envolver("che(trucho o posta);")), ["posta"])
        self.assertEqual(correr(envolver("che(no trucho);")), ["posta"])

    def test_division_por_cero(self):
        with self.assertRaises(ErrorEjecucion):
            correr(envolver("che(5 / 0);"))


# ====================================================================== #
# Integración sobre los archivos de ejemplo
# ====================================================================== #
class TestEjemplos(unittest.TestCase):
    EJEMPLOS = RAIZ / "ejemplos"

    def _fuente(self, nombre: str) -> str:
        return (self.EJEMPLOS / nombre).read_text(encoding="utf-8")

    def test_ejemplos_validos_compilan(self):
        for nombre in ("01_hola.mate", "02_mayoria.mate"):
            with self.subTest(ejemplo=nombre):
                compilar(self._fuente(nombre))

    def test_ejemplo_factorial_ejecuta(self):
        # El archivo puede editarse; solo verificamos que ejecuta y produce salida.
        salida = correr(self._fuente("06_factorial.mate"))
        self.assertTrue(salida)
        self.assertIn("El factorial de:", salida)

    def test_ejemplo_error_lexico(self):
        with self.assertRaises(ErrorLexico):
            tokenizar(self._fuente("04_error_lexico.mate"))

    def test_ejemplo_error_sintactico(self):
        with self.assertRaises(ErrorSintactico):
            parsear(tokenizar(self._fuente("05_error_sintactico.mate")))

    def test_ejemplo_errores_semanticos(self):
        with self.assertRaises(ErrorSemantico):
            compilar(self._fuente("03_errores_semanticos.mate"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
