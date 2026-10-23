import base64
import getpass
import os
import pathlib
import random
import subprocess
import sys
import time

INTERVALO_S = 300
DATOS = pathlib.Path("../KeplerDF-Datos")
CARPETA = "maquina_a"  # datos que se parsean (población del muestreo)
MAQUINA = f"maquina_{input('Letra de esta máquina (escribe solo la letra, ej. a): ').strip().lower()}"

token = getpass.getpass("Token de GitHub (no se muestra al escribir): ").strip()
if os.name == "nt":
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "[Windows.ApplicationModel.DataTransfer.Clipboard, Windows.ApplicationModel.DataTransfer, ContentType=WindowsRuntime] | Out-Null; "
                    "[Windows.ApplicationModel.DataTransfer.Clipboard]::ClearHistory() | Out-Null"])
cred = base64.b64encode(f"x-access-token:{token}".encode()).decode()
GIT_ENV = {**os.environ, "GIT_CONFIG_COUNT": "2",
           "GIT_CONFIG_KEY_0": "credential.helper", "GIT_CONFIG_VALUE_0": "",
           "GIT_CONFIG_KEY_1": "http.https://github.com/.extraheader",
           "GIT_CONFIG_VALUE_1": f"AUTHORIZATION: basic {cred}"}
if subprocess.run(["git", "ls-remote", "origin"], cwd=DATOS, env=GIT_ENV, capture_output=True).returncode:
    raise PermissionError("El token no es válido o no tiene acceso a KeplerDF-Datos.")


def publicar():
    subprocess.run(["git", "add", CARPETA], cwd=DATOS)
    nuevos = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=DATOS,
                            capture_output=True, text=True).stdout.split()
    if nuevos:
        subprocess.run(["git", "-c", f"user.name={MAQUINA}", "-c", f"user.email={MAQUINA}@keplerdf.local",
                        "commit", "-m", f"{MAQUINA}: request parser, {len(nuevos)} archivos"], cwd=DATOS)
    for _ in range(10):
        subprocess.run(["git", "pull", "--rebase"], cwd=DATOS, env=GIT_ENV)
        if subprocess.run(["git", "push", "origin", "HEAD"], cwd=DATOS, env=GIT_ENV).returncode == 0:
            break
        time.sleep(random.uniform(1, 10))


with open("muestreo_ic.log", "a", encoding="utf-8") as log:
    proc = subprocess.Popen([sys.executable, "-u", "muestreo_ic.py", str(DATOS / CARPETA)],
                            stdout=log, stderr=subprocess.STDOUT)
    while True:
        terminado = proc.poll() is not None
        publicar()
        if terminado:
            break
        time.sleep(INTERVALO_S + random.uniform(0, 120))