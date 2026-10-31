import json
import os
import pathlib
import time
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

if os.name == "nt":
    os.system("")  # activa los códigos ANSI en la consola de Windows
for frame in range(12):
    print("\033[2J\033[H" + "\n" * (12 - frame) + SATELLITE + TRAILS[frame % 2])
    time.sleep(0.12)
print("\033[2J\033[H" + SATELLITE + BANNER)

cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
parsed = request_parser_main(input("Solicitud: "), cfg["model"], cfg)
print(json.dumps(parsed, indent=2, ensure_ascii=False))