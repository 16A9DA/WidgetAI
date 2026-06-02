import webbrowser
from urllib.parse import quote_plus


def build_url(target: str, prompt: str) -> str | None:
    encoded_prompt = quote_plus(prompt)

    if target == "chatgpt":
        return f"https://chatgpt.com/?q={encoded_prompt}"

    if target == "claude":
        return f"https://claude.ai/new?q={encoded_prompt}"

    if target == "perplexity":
        return f"https://www.perplexity.ai/search?q={encoded_prompt}"

    if target == "gemini":
        return f"https://gemini.google.com"

    return None


def send_prompt(target: str, prompt: str) -> str:
    url = build_url(target, prompt)

    if not url:
        return f"No sender configured for {target}."

    webbrowser.open(url)

    if target == "gemini":
        return f"Opened {target}.\nDirect prompt prefilling is not set yet."

    return f"Opened {target} with your prompt."
