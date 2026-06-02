from dataclasses import dataclass


SUPPORTED_TARGETS = {
    "chatgpt",
    "claude",
    "perplexity",
    "exit",
    "history",
}

history = []


@dataclass
class CommandResult:
    is_valid: bool
    target: str = ""
    prompt: str = ""
    error: str = ""


def parse_command(text: str) -> CommandResult:
    text = text.strip()

    if not text:
        return CommandResult(
            is_valid=False,
            error="Please type a command first."
        )

    if not text.startswith("/"):
        return CommandResult(
            is_valid=False,
            error="Command must start with /. Example: /chatgpt explain this code"
        )

    parts = text[1:].split(maxsplit=1)
    target = parts[0].lower() if parts else ""
    prompt = parts[1].strip() if len(parts) > 1 else ""

    if target not in SUPPORTED_TARGETS:
        return CommandResult(
            is_valid=False,
            error=f"Unknown target '{target}'."
        )

    if target in {"exit", "history"}:
        return CommandResult(
            is_valid=True,
            target=target,
            prompt="",
            error=""
        )

    if not prompt:
        return CommandResult(
            is_valid=False,
            error=f"Please add a message after /{target}."
        )

    history.append({
        "target": target,
        "prompt": prompt
    })

    return CommandResult(
        is_valid=True,
        target=target,
        prompt=prompt,
        error=""
    )


def get_history():
    return history
