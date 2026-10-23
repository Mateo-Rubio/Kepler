import os
import json
import requests
from typing import Dict, List, Any

__all__ = ["parse_request", "build_format_schema"]


def _ollama_endpoint() -> str:
    raw_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    clean_url = raw_url.replace("[", "").replace("]", "").split("(")[0].strip()
    return f"{clean_url}/api/generate"


def build_format_schema(vocabularies: Dict[str, List[str]]) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "day": {"type": "string", "enum": vocabularies["day"]},
            "hour": {"type": "string", "enum": vocabularies["hour"]},
            "sensor": {"type": "string", "enum": list(vocabularies["sensor"])},
            "priority": {"type": "string", "enum": vocabularies["priority"]},
        },
        "required": ["day", "hour", "sensor", "priority"],
    }


def _call_ollama(
    prompt: str,
    model_name: str,
    temperature: float,
    format_schema: Dict[str, Any],
    num_predict: int = 200,
    repeat_penalty: float = 1.0,
) -> str:
    payload = {
        "model": model_name,
        "prompt": prompt,
        "format": format_schema,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "repeat_penalty": repeat_penalty,
        },
    }

    response = requests.post(_ollama_endpoint(), json=payload, stream=True, timeout=180)
    response.raise_for_status()

    output_chunks = []
    for line in response.iter_lines():
        if not line:
            continue
        line_object = json.loads(line)
        if "response" not in line_object:
            continue

        output_chunks.append(line_object["response"])

        if line_object.get("done"):
            break

    return "".join(output_chunks)


def parse_request(request_text: str, model_name: str, cfg: Dict[str, Any]) -> Dict[str, str]:
    vocabularies = cfg["vocabularies"]
    prompt = cfg["instruction_prompt"].format(
        request_text=request_text,
        day_values=json.dumps(vocabularies["day"]),
        hour_values=json.dumps(vocabularies["hour"]),
        sensor_values=json.dumps(vocabularies["sensor"]),
        priority_values=json.dumps(vocabularies["priority"]),
    )
    raw_text = _call_ollama(
        prompt, model_name, cfg["temperature"],
        format_schema=build_format_schema(vocabularies),
        num_predict=cfg["num_predict"], repeat_penalty=cfg["repeat_penalty"],
    )
    return json.loads(raw_text)