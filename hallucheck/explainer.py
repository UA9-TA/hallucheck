import os
from typing import Any, Dict, List

import anthropic

from .config import load_config
from .validator import Hallucination


def explain_hallucination(
    hallucination: Hallucination, index: Dict[str, List[Dict[str, Any]]], code_context: str
) -> str:
    config = load_config()
    api_key = os.environ.get("ANTHROPIC_API_KEY") or config.get("api_key")

    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable or config not set."

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
    The following hallucinated code reference was found in an AI-generated diff:

    File: {hallucination.file}
    Line: {hallucination.line}
    Symbol: {hallucination.reference}
    Kind: {hallucination.kind}

    Code Context:
    ```python
    {code_context}
    ```

    Error: {hallucination.message}

    Available suggestions from codebase index:
    {", ".join(hallucination.suggestions) if hallucination.suggestions else "None"}

    Please:
    1. Confirm if this is likely a hallucination.
    2. Explain what the AI was probably trying to do.
    3. Suggest the correct code using real symbols from the index.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Error communicating with Anthropic API: {str(e)}"
