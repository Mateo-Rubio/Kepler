import hashlib
import json
import os
import pathlib
import requests
import yaml
from request_parser.main import request_parser_main

DATOS = pathlib.Path("../KeplerDF-Datos")
SALIDA = pathlib.Path("../Kepler-Parsed-Requests")
MAQUINAS = ["maquina_a", "maquina_b", "maquina_c", "maquina_d"]
FIELDS = ["day", "hour", "sensor", "priority"]


def load_config() -> dict:
    return yaml.safe_load(pathlib.Path("config.yaml").read_text(encoding="utf-8"))


def clean_model_name(model: str) -> str:
    return model.replace(":", "_").replace(".", "_")


def check_ollama_models_available(models: list):
    base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    installed = {m["name"] for m in requests.get(f"{base_url}/api/tags", timeout=10).json()["models"]}
    installed |= {name[:-len(":latest")] for name in installed if name.endswith(":latest")}
    missing = [m for m in models if m not in installed]
    if missing:
        raise ConnectionError(f"Models not installed in Ollama: {missing}")


def combined_paths() -> list:
    return sorted(p for m in MAQUINAS
                  for p in (DATOS / m).glob("*/*/temp_*/rep_*/scenario_*/ollama_prompts_combined.json"))


def parse_scenario(path: pathlib.Path, model: str, cfg: dict, cache: dict) -> list:
    use_cache = path.parent.parent.parent.name == "temp_0.0"  # solo a 0.0 se repiten los textos
    results = []
    for task in json.loads(path.read_text(encoding="utf-8"))["tasks"]:
        key = hashlib.sha1(task["generated_output"].encode("utf-8")).digest()
        if use_cache and key in cache:
            parsed = cache[key]
        else:
            parsed = request_parser_main(task["generated_output"], model, cfg)
            if use_cache:
                cache[key] = parsed
        results.append({
            "task_id": task["task_id"],
            "parsed": parsed,
            "parser_match": {f"{f}_match": parsed[f] == task["ground_truth"][f"expected_{f}"] for f in FIELDS},
            "validation": {f"{f}_match": task["validation"][f"{f}_match"] for f in FIELDS},
        })
    return results


def main():
    cfg = load_config()
    check_ollama_models_available(cfg["models"])
    paths = combined_paths()
    print(f"Archivos de escenario: {len(paths)}")
    for model in cfg["models"]:  # un modelo a la vez, para no recargarlo en la GPU
        cache = {}
        for path in paths:
            out = SALIDA / path.parent.relative_to(DATOS) / f"parsed_requests_{clean_model_name(model)}.json"
            if out.exists():
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(parse_scenario(path, model, cfg, cache), indent=2, ensure_ascii=False),
                           encoding="utf-8")
            print(f"  [OK] {out}")
    print("Evaluación completa terminada.")


if __name__ == "__main__":
    main()