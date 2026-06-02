import webbrowser


TARGET_URLS = {
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "perplexity": "https://www.perplexity.ai",
    "gemini": "https://gemini.google.com",
}


def send_prompt(target: str, prompt: str) -> str:
    if target not in TARGET_URLS:
        return f"No sender configured for {target}."

    url = TARGET_URLS[target]
    webbrowser.open(url)

    return f"Opened {target}.\nPrompt: {prompt}"
