import csv
import json
import random
from request_parser.main import request_parser_main
from evaluar_todo import DATOS, SALIDA, FIELDS, load_config, check_ollama_models_available, combined_paths

SEED = 2026
N_MUESTRA = 1068
FUGA = ("stage 1 - reasoning", "stage 2 - final", "which exact string", "copy it verbatim")
DESTINO = SALIDA / "muestra"


def poblacion(paths: list) -> list:
    refs = []
    for i, path in enumerate(paths):
        estrategia = path.relative_to(DATOS).parts[2]
        for j, task in enumerate(json.loads(path.read_text(encoding="utf-8"))["tasks"]):
            if estrategia == "chain_of_thought" and any(k in task["generated_output"].lower() for k in FUGA):
                continue
            refs.append((i, j))
    return refs


def main():
    if (DESTINO / "muestra.json").exists():
        print("La muestra ya existe, se omite.")
        return
    cfg = load_config()
    check_ollama_models_available(cfg["models"])
    paths = combined_paths()
    refs = poblacion(paths)
    print(f"Archivos de escenario: {len(paths)} | Población N: {len(refs)} | Muestra n: {N_MUESTRA}")

    filas = []
    for i, j in random.Random(SEED).sample(refs, N_MUESTRA):
        maquina, modelo, estrategia, temp, rep, escenario = paths[i].relative_to(DATOS).parts[:6]
        task = json.loads(paths[i].read_text(encoding="utf-8"))["tasks"][j]
        filas.append({
            "maquina": maquina, "modelo": modelo, "estrategia": estrategia, "temp": temp,
            "rep": rep, "escenario": escenario, "task_id": task["task_id"],
            "texto": task["generated_output"], "ground_truth": task["ground_truth"],
            "kdf": task["validation"], "parsers": {},
        })

    textos = list(dict.fromkeys(f["texto"] for f in filas))  # textos distintos, en el orden aleatorio de la muestra
    ids = {t: k + 1 for k, t in enumerate(textos)}
    for model in cfg["models"]:
        print(f"  [RUN] parser={model} | {len(textos)} textos")
        salidas = {t: request_parser_main(t, model, cfg) for t in textos}
        for f in filas:
            f["parsers"][model] = salidas[f["texto"]]
    for f in filas:
        f["id_anotacion"] = ids[f["texto"]]

    DESTINO.mkdir(parents=True, exist_ok=True)
    with (DESTINO / "anotacion.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "texto", *FIELDS])
        for t in textos:
            writer.writerow([ids[t], t, "", "", "", ""])
    (DESTINO / "muestra.json").write_text(json.dumps({
        "seed": SEED, "N": len(refs), "n": N_MUESTRA, "textos_distintos": len(textos), "filas": filas,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Muestra guardada en {DESTINO}")


if __name__ == "__main__":
    main()