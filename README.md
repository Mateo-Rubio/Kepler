# Kepler

Kepler es un sistema de planeación de tareas para constelaciones de satélites LEO, desarrollado en el Departamento de Ingeniería de Sistemas y Computación de la Universidad de los Andes.

Este repositorio contiene su primera etapa, el **Request Parser**: recibe la solicitud de un operador de misión escrita en lenguaje natural y la traduce a los parámetros estructurados de la tarea:

| Parámetro | Valores posibles |
|---|---|
| `day` | `today`, `tomorrow`, `the day after tomorrow`, `in three days`, `in four days` |
| `hour` | `morning`, `mid-day`, `afternoon`, `evening`, `overnight` |
| `sensor` | `TIR`, `VNIR`, `SAR`, `NIR`, `VISUAL` |
| `priority` | Nivel bajo, medio o alto (ver `request_parser/config.yaml`) |

La traducción la hace un modelo de lenguaje servido localmente con [Ollama](https://ollama.com). Su respuesta se restringe con un esquema JSON, de modo que cada parámetro solo puede tomar uno de los valores permitidos.

## Requisitos

- Python 3.10 o superior.
- [Ollama](https://ollama.com/download) instalado y en ejecución.
- El modelo configurado en `request_parser/config.yaml`, descargado en Ollama. Por defecto es `phi3.5:3.8b`:

  ```bash
  ollama pull phi3.5:3.8b
  ```

## Instalación

```bash
git clone https://github.com/Mateo-Rubio/Kepler.git
cd Kepler
python -m venv .venv
```

Activa el entorno virtual:

- Linux y macOS: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Antes de empezar, el programa verifica que Ollama responda y que el modelo esté descargado. Luego muestra la pantalla de bienvenida y pide la solicitud. Por ejemplo:

```
Solicitud: We need a thermal scan of the port of Ravenna to detect heat anomalies, delivered tomorrow in the morning. This is routine monitoring.
{
  "day": "tomorrow",
  "hour": "morning",
  "sensor": "TIR",
  "priority": "medium priority standard operational tasking routine monitoring monitoring"
}
```

Se recomienda escribir las solicitudes en inglés, que es el idioma del *prompt* de instrucción y de los vocabularios.

## Configuración

Toda la configuración está en `request_parser/config.yaml`:

| Clave | Descripción |
|---|---|
| `model` | Modelo de Ollama que actúa como parser. |
| `temperature` | Temperatura de muestreo. En 0.0 la salida es determinista. |
| `num_predict` | Número máximo de tokens de la respuesta. |
| `repeat_penalty` | Penalización por repetición de Ollama. |
| `instruction_prompt` | Instrucción que recibe el modelo junto con la solicitud. |
| `vocabularies` | Valores permitidos para cada parámetro. En `sensor`, cada sigla va acompañada de la descripción de la observación que realiza. |

Para usar otro modelo, cambia `model` y descárgalo con `ollama pull`. Los modelos evaluados en el proyecto son `gemma2:27b`, `llama3.1:8b`, `phi3.5:3.8b`, `phi4:14b` y `qwen2:7b`.

Si Ollama corre en otra dirección o puerto, indícalo con la variable de entorno `OLLAMA_URL` (por defecto, `http://127.0.0.1:11434`).

## Estructura

```
Kepler/
├── main.py                 Punto de entrada: bienvenida, solicitud y resultado
├── requirements.txt
└── request_parser/
    ├── config.yaml         Modelo, parámetros, instrucción y vocabularios
    ├── main.py             request_parser_main: interfaz del módulo
    └── parser.py           Construcción del prompt y del esquema, y llamada a Ollama
```

Los scripts de evaluación del Request Parser frente al validador de KEPLER Data Factory están en la rama `request_parser_tests`.