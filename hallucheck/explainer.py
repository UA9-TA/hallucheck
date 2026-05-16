import anthropic

from .config import get_api_key


def explain_hallucination(hallucination_str):
    api_key = get_api_key()
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set. Run `hallucheck config` to set it."

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
    You are an expert developer assistant. A tool called HalluCheck has detected a hallucinated code reference in an AI-generated diff.

    Here is the hallucination:
    {hallucination_str}

    Please:
    1. Explain what the AI was likely trying to do when it hallucinated this reference.
    2. Suggest how to fix it using the suggested real alternatives, or standard Python library alternatives if applicable.
    Keep your answer concise and focused on the code.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        # Handle the new TextBlock format
        return response.content[0].text
    except Exception as e:
        return f"Error calling Claude API: {e}"
