import json
from typing import List


def payload_setter(
    image_uri: str,
    client_name: str,
    use_case_name: str,
    markets: List[dict],
    user_prompt: str,
    budget: float
) -> dict:

    payload = {
        "image_uri": image_uri,
        "client_name": client_name,
        "use_case_name": use_case_name,
        "markets": markets,
        "user_prompt": user_prompt,
        "budget": budget,
    }

    return payload