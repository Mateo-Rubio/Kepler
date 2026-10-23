import json
import math
import pathlib
import sys
import pandas as pd
from scipy import stats
from run_request_parser import (load_config, clean_model_name, parse_scenario,
                                sampled_scenarios, N_SCENARIOS)

ROOT = pathlib.Path(sys.argv[1])  # carpeta maquina_a de KeplerDF-Datos
SEED = 2026
REPS = ["rep_1", "rep_2"]
E = 0.05
N_PILOT = 5
CATEGORIES = ["day", "hour"]
FACTORS = [None, "modelo", "temp", "estrategia"]  # None = global
FUGA = ("stage 1 - reasoning", "stage 2 - final", "which exact string", "copy it verbatim")

cfg = load_config("config.yaml")
PARSERS = cfg["models"]
cache = {}


def sample_paths(sample):
    return [p for p in sorted(ROOT.glob("*/*/temp_*/rep_*/scenario_*/ollama_prompts_combined.json"))
            if int(p.parent.name.split("_")[1]) in sample and p.parent.parent.name in REPS]


def parse_sample(sample):
    for path in sample_paths(sample):
        for model in PARSERS:
            out = path.parent / f"parsed_requests_{clean_model_name(model)}.json"
            if not out.exists():
                print(f"  [RUN] {path.parent} | parser={model}")
                out.write_text(json.dumps(parse_scenario(path, model, cfg, cache), indent=2,
                                          ensure_ascii=False), encoding="utf-8")


def load_rows(sample):
    rows = []
    for path in sample_paths(sample):
        modelo, estrategia, temp, rep, esc = path.relative_to(ROOT).parts[:5]
        tasks = json.loads(path.read_text(encoding="utf-8"))["tasks"]
        fuga = [estrategia == "chain_of_thought" and any(k in t["generated_output"].lower() for k in FUGA)
                for t in tasks]
        base = {"modelo": modelo, "estrategia": estrategia, "temp": temp, "esc": esc}
        for c in CATEGORIES:
            hits = sum(t["validation"][f"{c}_match"] and not f for t, f in zip(tasks, fuga))
            rows.append({**base, "validador": "kdf", "categoria": c, "aciertos": hits, "total": len(tasks)})
        for model in PARSERS:
            parsed = json.loads((path.parent / f"parsed_requests_{clean_model_name(model)}.json")
                                .read_text(encoding="utf-8"))
            for c in CATEGORIES:
                hits = sum(p["parser_match"][f"{c}_match"] and not f for p, f in zip(parsed, fuga))
                rows.append({**base, "validador": model, "categoria": c, "aciertos": hits, "total": len(parsed)})
    return pd.DataFrame(rows)


def min_n(s):
    for n in range(2, N_SCENARIOS + 1):
        if stats.t.ppf(0.975, n - 1) * s / math.sqrt(n) * math.sqrt(1 - n / N_SCENARIOS) <= E:
            return n


def required_n(df):
    detalle = []
    for factor in FACTORS:
        keys = ["esc", "categoria"] + ([factor] if factor else [])
        sums = df.groupby(keys + ["validador"])[["aciertos", "total"]].sum()
        y = (sums["aciertos"] / sums["total"]).unstack("validador")
        d = y[PARSERS].sub(y["kdf"], axis=0)
        s = d.groupby(level=keys[1:]).std(ddof=1)
        for nivel, fila in s.iterrows():
            for parser, s_val in fila.items():
                detalle.append({"factor": factor or "global", "nivel": str(nivel), "parser": parser,
                                "s_d": s_val, "n_requerido": min_n(s_val)})
    return pd.DataFrame(detalle)


n = N_PILOT
while True:
    sample = sampled_scenarios(n, SEED)
    parse_sample(sample)
    detalle = required_n(load_rows(sample))
    n_req = int(detalle["n_requerido"].max())
    print(f"  Escenarios parseados: {n} | n requerido: {n_req}")
    if n_req <= n:
        break
    n = n_req

detalle.to_csv(ROOT / "muestreo_detalle.csv", index=False)
(ROOT / "muestreo.json").write_text(json.dumps({
    "seed": SEED, "reps": REPS, "E": E, "categorias": CATEGORIES, "parsers": PARSERS,
    "n": n, "escenarios": sample,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  Muestra final: {sample}")
