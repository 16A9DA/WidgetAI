import webbrowser
from urllib.parse import quote_plus
import time
import webbrowser
from urllib.parse import quote_plus
import subprocess



def press_enter():
    script = 'tell application "System Events" to key code 36'
    subprocess.run(["osascript", "-e", script], check=False)


def build_url(target: str, prompt: str) -> str | None:
    encoded_prompt = quote_plus(prompt)

    if target == "claude":
        return f"claude://claude.ai/new?q={encoded_prompt}"

    if target == "chatgpt":
        return f"https://chatgpt.com/?q={encoded_prompt}"

    if target == "perplexity":
        return f"https://www.perplexity.ai/search?q={encoded_prompt}"



    return None


def send_prompt(target: str, prompt: str) -> str:
    url = build_url(target, prompt)

    if not url:
        return f"No sender configured for {target}."

    webbrowser.open(url)
    time.sleep(1.8)
    press_enter()

    return f"Opened {target}, autofilled prompt, and tried to auto-send."