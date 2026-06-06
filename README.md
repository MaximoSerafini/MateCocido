<p align="center">
  <img src="docs/logo.png" alt="Logo Mate Cocido" width="220">
</p>

<h1 align="center">🧉 Mate Cocido — Compilador</h1>

> Trabajo Práctico Integrador — **Teoría de la Computación**

**Mate Cocido** es un mini-lenguaje de programación imperativo (una parodia
argentina de Java) y este repositorio contiene su **compilador**, implementado
en Python desde cero, con las **tres primeras fases** de un compilador:

| Fase | Nombre | Entrada → Salida |
|---|---|---|
| 1 | **Análisis Léxico** (scanner) | código fuente → *tokens* |
| 2 | **Análisis Sintáctico** (parser) | tokens → *árbol de sintaxis abstracta (AST)* |
| 3 | **Análisis Semántico** | AST → AST validado + *tabla de símbolos* |

> El TPI pedía un mínimo de **2 fases**; este trabajo implementa **3**.

---

## Requisitos

- **Python 3.10+** (no usa librerías externas; solo la biblioteca estándar).

---

## Cómo se usa

Desde la raíz del proyecto:

```powershell
# Compilar un programa y ver el resumen de las 3 fases
python src/main.py ejemplos/02_mayoria.mate

# Ver el detalle de cada fase
python src/main.py ejemplos/02_mayoria.mate --tokens   # Fase 1: tabla de tokens
python src/main.py ejemplos/02_mayoria.mate --ast      # Fase 2: AST en árbol ASCII
python src/main.py ejemplos/02_mayoria.mate --tabla    # Fase 3: tabla de símbolos
python src/main.py ejemplos/02_mayoria.mate --todo     # todo junto
```

### Tests

```powershell
python -m unittest discover -s tests -v
```

---

## El lenguaje Mate Cocido

```java
mate Cocido {
    arrancar() {
        cebar entero edad = 18;

        si (edad >= 18 y edad < 100) {
            che("Cebá unos mates, maestro");
        } sino {
            che("Todavía tomás la leche");
        }

        cebar entero i = 0;
        mientras (i < 3) {
            che(i);
            i = i + 1;
        }
    }
}
```

| Mate Cocido | Java | Rol |
|---|---|---|
| `mate Nombre { }` | `class` | declara el programa |
| `arrancar()` | `main` | punto de entrada |
| `cebar TIPO x = ...` | declaración | variable nueva |
| `entero` `flota` `palabra` `bool` | `int double String boolean` | tipos |
| `posta` / `trucho` | `true` / `false` | booleanos |
| `si` / `sino` | `if` / `else` | condicional |
| `mientras` | `while` | bucle |
| `che(...)` | `System.out.println` | salida |
| `devolver` | `return` | retorno |
| `y` `o` `no` | `&&` `\|\|` `!` | operadores lógicos |

La **gramática formal completa (EBNF)** está en [`docs/gramatica.md`](docs/gramatica.md).

---

## Estructura del proyecto

```
MateCocido/
├── README.md
├── docs/
│   ├── gramatica.md          # gramática formal EBNF
│   └── informe.md            # documento del TPI
├── src/
│   ├── main.py               # CLI que orquesta las 3 fases
│   └── matecocido/
│       ├── tokens.py         # definición de tokens
│       ├── errores.py        # excepciones por fase
│       ├── lexer.py          # Fase 1 — análisis léxico
│       ├── ast_nodes.py      # nodos del AST
│       ├── parser.py         # Fase 2 — análisis sintáctico
│       ├── semantic.py       # Fase 3 — análisis semántico
│       └── imprimir.py       # presentación de tokens/AST/tabla
├── ejemplos/
│   ├── 01_hola.mate
│   ├── 02_mayoria.mate
│   ├── 03_errores_semanticos.mate
│   ├── 04_error_lexico.mate
│   └── 05_error_sintactico.mate
└── tests/
    └── test_compilador.py    # 35 tests (unittest)
```

---

## Ejemplos incluidos

| Archivo | Qué demuestra |
|---|---|
| `01_hola.mate` | programa mínimo válido |
| `02_mayoria.mate` | condicionales, bucles y precedencia |
| `03_errores_semanticos.mate` | 5 errores semánticos detectados |
| `04_error_lexico.mate` | carácter inválido (Fase 1) |
| `05_error_sintactico.mate` | falta `;` (Fase 2) |
