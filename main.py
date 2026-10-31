import json
import os
import pathlib
import time
import requests
import yaml
from request_parser.main import request_parser_main

CONFIG = pathlib.Path(__file__).parent / "request_parser" / "config.yaml"

SATELLITE = r"""
              .-''''-.
            .'        '.
           /            \
          ;              ;
          |              |
          ;              ;
           \            /
            '.        .'
            /|'-....-'|\
           / |        | \
          /  |        |  \
         /   |        |   \
"""
TRAILS = ["        *    .    '   .    *", "       '   *    .   *   '   ."]
BANNER = """
  ==============================================================
                       Bienvenido a Kepler
  ==============================================================
   Departamento de Ingeniería de Sistemas y Computación
   Universidad de los Andes

   Kepler es un sistema de planeación de tareas para
   constelaciones de satélites LEO. Esta primera etapa traduce
   la solicitud de un operador de misión, escrita en lenguaje
   natural, a los parámetros de la tarea: día, franja horaria,
   sensor y prioridad.
  ==============================================================
"""

def check_ollama(model: str):
    base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        installed = {m["name"] for m in requests.get(f"{base_url}/api/tags", timeout=10).json()["models"]}
    except requests.RequestException:
        raise SystemExit(f"No se pudo conectar con Ollama en {base_url}. Verifica que esté en ejecución.")
    installed |= {name[:-len(":latest")] for name in installed if name.endswith(":latest")}
    if model not in installed:
        raise SystemExit(f"El modelo '{model}' no está descargado. Ejecuta: ollama pull {model}")


cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
check_ollama(cfg["model"])

if os.name == "nt":
    os.system("")  # activa los códigos ANSI en la consola de Windows
for frame in range(12):
    print("\033[2J\033[H" + "\n" * (12 - frame) + SATELLITE + TRAILS[frame % 2])
    time.sleep(0.12)
print("\033[2J\033[H" + SATELLITE + BANNER)

parsed = request_parser_main(input("Solicitud: "), cfg["model"], cfg)
print(json.dumps(parsed, indent=2, ensure_ascii=False))