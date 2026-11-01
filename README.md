# Kepler — evaluación del Request Parser (rama `request_parser_tests`)

Esta rama contiene los scripts que evalúan el **Request Parser** de Kepler como extractor alternativo al validador de [KEPLER Data Factory](https://github.com/Mateo-Rubio/KeplerDF-Logica) (KDF). El uso normal del parser, con una solicitud a la vez, está en la rama `main`.

La evaluación tiene dos partes:

1. **Muestra para anotación humana** (`evaluar_muestra.py`): una muestra aleatoria de 1 068 solicitudes que se anota manualmente, para estimar la precisión de KDF y de cada modelo parser frente a la lectura humana, con intervalos de confianza del 95 % y semiamplitud de 0,03 como máximo.
2. **Evaluación completa** (`evaluar_todo.py`): el parser aplicado a todas las solicitudes generadas en el experimento de KDF, comparado contra el *ground truth*.

## Estructura de carpetas requerida

Los tres repositorios deben clonarse en la misma carpeta:

```
carpeta/
├── Kepler/                    esta rama (scripts y request_parser)
├── KeplerDF-Datos/            solicitudes generadas por KDF (solo lectura)
└── Kepler-Parsed-Requests/    resultados del parser (escritura y publicación)
```

KeplerDF-Datos debe tener completas las carpetas `maquina_a` a `maquina_d`: 40 800 archivos `ollama_prompts_combined.json` (34 escenarios × 120 condiciones × 10 repeticiones). La `maquina_e` no se usa. Si el clon es parcial:

```bash
git -C KeplerDF-Datos sparse-checkout set maquina_a maquina_b maquina_c maquina_d
git -C KeplerDF-Datos pull
```

## Requisitos

- Python 3.10 o superior, con las dependencias de `requirements.txt`:
  ```bash
  python -m venv .venv
  .venv/bin/pip install -r requirements.txt
  ```
- [Ollama](https://ollama.com) en ejecución, con los cinco modelos parser de `config.yaml`:
  ```bash
  for m in gemma2:27b llama3.1:8b phi3.5:3.8b phi4:14b qwen2:7b; do ollama pull $m; done
  ```
- Para publicar con `auto_commit.py`, un token de GitHub *fine-grained* con permiso *Contents: Read and write* sobre Kepler-Parsed-Requests.

## Scripts

Todos se ejecutan desde la raíz de esta rama. Leen `config.yaml` (modelos parser, temperatura, *prompt* de instrucción y vocabularios) y verifican al inicio que Ollama responda y que los cinco modelos estén descargados.

### `evaluar_muestra.py`

1. Construye la población: todas las solicitudes de las máquinas A a D, excepto las de Chain-of-Thought que filtran su razonamiento.
2. Extrae una muestra aleatoria simple de 1 068 solicitudes, sin reemplazo, con semilla 2026.
3. Ejecuta los cinco modelos parser sobre los textos distintos de la muestra.
4. Guarda el resultado en `Kepler-Parsed-Requests/muestra/`.

Si `muestra/muestra.json` ya existe, no hace nada.

### `evaluar_todo.py`

Ejecuta los cinco modelos parser sobre todos los escenarios de las máquinas A a D, un modelo a la vez para no recargarlo en la GPU. Guarda un archivo por escenario y modelo en `Kepler-Parsed-Requests`, con la misma ruta que el escenario en KeplerDF-Datos. Es reanudable: si el archivo de salida ya existe, lo omite.

A temperatura 0.0, los textos idénticos se parsean una sola vez y se reutiliza la respuesta.

### `auto_commit.py`

Ejecuta `evaluar_muestra.py` y después `evaluar_todo.py`, y cada 5 a 7 minutos hace commit y push de los resultados en Kepler-Parsed-Requests. Al iniciar pide la letra de la máquina, que se usa solo para firmar los commits (`maquina_{letra}`), y el token de GitHub, que se mantiene en memoria y no se guarda en disco. La salida de los scripts se escribe en `evaluacion.log`. Para revisar el mientras se está en ejecución:

```bash
tail -n 20 evaluacion.log
ollama ps
```

La primera línea del log debe indicar `Archivos de escenario: 40800`. La columna `PROCESSOR` de `ollama ps` debe indicar `100% GPU`.

## Resultados

Los scripts no guardan resultados en este repositorio. Todo se escribe en el repositorio [Kepler-Parsed-Requests](https://github.com/Mateo-Rubio/Kepler-Parsed-Requests), clonado junto a este (ver [Estructura de carpetas requerida](#estructura-de-carpetas-requerida)), y `auto_commit.py` lo publica ahí. Las rutas de esta sección son relativas a la raíz de Kepler-Parsed-Requests.

### `muestra/anotacion.csv`

Hoja para la anotación humana. Contiene una fila por texto distinto de la muestra, en orden aleatorio, con las columnas `id`, `texto`, `day`, `hour`, `sensor` y `priority`. Las cuatro últimas están vacías y las llena el anotador.

La anotación es ciega: el anotador solo debe abrir este archivo, no `muestra.json`. Convenciones:

| Columna | Valores |
|---|---|
| `day` | `today`, `tomorrow`, `the day after tomorrow`, `in three days`, `in four days` |
| `hour` | `morning`, `mid-day`, `afternoon`, `evening`, `overnight`. Una hora explícita se asigna según los intervalos de KDF: 6–11, 11–14, 14–18, 18–23 y el resto. |
| `sensor` | `TIR`, `VNIR`, `SAR`, `NIR`, `VISUAL`, según las descripciones de `config.yaml` |
| `priority` | `low`, `medium`, `high` |

Si el texto no expresa la categoría o es ambiguo, se escribe `NA`. Se recomienda anotar sobre una copia del archivo, fuera de Kepler-Parsed-Requests, porque `auto_commit.py` puede estar publicando ese repositorio.

### `muestra/muestra.json`

Contiene `seed`, `N` (tamaño de la población), `n` (tamaño de la muestra), `textos_distintos` y `filas`. Cada fila corresponde a una solicitud sorteada:

| Campo | Contenido |
|---|---|
| `maquina`, `modelo`, `estrategia`, `temp`, `rep`, `escenario`, `task_id` | Ubicación de la solicitud en KeplerDF-Datos |
| `texto` | Texto generado |
| `ground_truth` | Valores esperados según KDF |
| `kdf` | Etiquetas predichas por el validador de KDF, con su similitud y acierto |
| `parsers` | Etiquetas asignadas por cada uno de los cinco modelos parser |
| `id_anotacion` | `id` del texto en `anotacion.csv` |

### `maquina_x/{modelo}/{estrategia}/temp_{T}/rep_{r}/scenario_{i}/parsed_requests_{parser}.json`

Una entrada por tarea del escenario:

| Campo | Contenido |
|---|---|
| `task_id` | Identificador de la tarea |
| `parsed` | Etiquetas asignadas por el modelo parser |
| `parser_match` | Si cada etiqueta del parser coincide con el *ground truth* |
| `validation` | Si cada etiqueta de KDF coincide con el *ground truth* |