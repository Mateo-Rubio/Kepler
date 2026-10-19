from typing import Dict, Any
from .parser import parse_request

__all__ = ["request_parser_main"]


def request_parser_main(request_text: str, model: str, cfg: Dict[str, Any]) -> Dict[str, str]:
    parsed = parse_request(request_text, model, cfg)
    return {
        "day": parsed["day"],
        "hour": parsed["hour"],
        "sensor": parsed["sensor"],
        "priority": parsed["priority"],
    }
