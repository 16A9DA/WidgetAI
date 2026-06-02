TARGETS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/",
    "perplexity": "https://www.perplexity.ai/",
}


def get_target_url(target: str) -> str | None:
    return TARGETS.get(target)


