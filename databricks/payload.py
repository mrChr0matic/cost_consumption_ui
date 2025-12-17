from typing import List, Optional


def payload_setter(
    image_uris: Optional[List[str]],
    file_uris: Optional[List[str]],
    client_name: str,
    use_case_name: str,
    markets: List[dict],
    user_prompt: Optional[str],
    budget: Optional[float]
) -> dict:
    """
    Builds the payload for Databricks job execution.

    image_uris: list of image URLs (can be empty)
    file_uris: list of document URLs (can be empty)
    """

    payload = {
        "image_uris": image_uris or [],
        "file_uris": file_uris or [],
        "client_name": client_name,
        "use_case_name": use_case_name,
        "markets": markets,
        "user_prompt": user_prompt,
        "budget": budget,
    }

    return payload
