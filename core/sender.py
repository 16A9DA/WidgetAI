import webbrowser
from urllib.parse import quote_plus


TARGET_PATTERNS = {
    "chatgpt": "https://chatgpt.com/?q={prompt}",
    "claude": "https://claude.ai/new?q={prompt}",
    "perplexity": "https://www.perplexity.ai/search?q={prompt}",
    "gemini": "https://gemini.google.com",
}


def send_prompt(target: str, prompt: str) -> str:
    if target not in TARGET_PATTERNS:
        return f"No sender configured for {target}."

    encoded_prompt = quote_plus(prompt)
    pattern = TARGET_PATTERNS[target]

    if "{prompt}" in pattern:
        url = pattern.format(prompt=encoded_prompt)
    else:
        url = pattern

    webbrowser.open(url)

    if target == "gemini":
        return f"Opened {target}. Prompt prefill not available yet."

    return f"Opened {target} with your prompt."
