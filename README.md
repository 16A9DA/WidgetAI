# WIAI

A compact desktop widget that gives a single command-line interface to ChatGPT, Claude, and Perplexity through their free web interfaces, no API keys required.

## Features

- Compact, terminal-style Qt widget, designed to stay small not to fill the screen
- Slash-command-only interaction, no buttons or chrome
- Multi-service support: ChatGPT, Claude, Perplexity
- Persistent login via `~/.wiai/profile` cookies, sign in once per service
- Conversation history saved to `history.json` and browsable through the widget
- Cross-platform: works wherever PySide6 runs (Windows, macOS, Linux/X11)
- Docker-ready

## Installation

### Local

```bash
git clone https://github.com/16A9DA/WidgetAI.git
cd WidgetAI
pip install -r requirements.txt
python wiai.py
```

### Docker

```bash
docker build -t wiai .
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix wiai
```

## Commands

| Command            | What it does                            |
| ------------------ | --------------------------------------- |
| `/chatgpt`         | switch to ChatGPT                       |
| `/claude`          | switch to Claude                        |
| `/perplexity`      | switch to Perplexity                    |
| `/login [provider]` | log in to a provider (or current one)   |
| `/help` / `/helpme` | show this help                          |
| `/history`         | show recent history                     |
| `/clear-all`       | clear chat output and stored history    |
| `/exit`            | quit the widget                         |

Anything that does not start with `/` is sent to the currently active provider as a prompt.

## Workflow

1. Launch: `python wiai.py`
2. If not logged in: `/login chatgpt` (or whichever service) and complete the sign-in shown in the popped-up browser
3. Pick a provider: `/chatgpt`, `/claude`, or `/perplexity`
4. Type a prompt into the input line and press Enter
5. Switch providers mid-session without re-logging in, persistent cookies stay valid until you `/clear-all` the cookies manually

## Architecture

- `wiai.py` - Qt main window, signal wiring, command dispatch
- `browser_handler.py` - one persistent `QWebEngineView` per service; JS injection for sending prompts and extracting the latest assistant reply
- `command_parser.py` - slash-command parsing and validation
- `history_manager.py` - JSON-backed history (`history.json`)
- `login_manager.py` - tracks per-provider login state

Cookies and storage live in `~/.wiai/profile`, configured as a persistent `QWebEngineProfile` in `browser_handler.py`.

## How it works

Each provider has a long-lived browser view loaded with the service's URL. When you send a prompt, the widget injects JavaScript that types the prompt into the existing input box on the page and clicks submit. A polling loop runs JS that returns the latest assistant message from the DOM.

Login works the same way: `/login provider` brings the existing service view to the front and navigates it to that service's login URL. The widget watches the URL/dominant content until it no longer matches `/login`/`/auth` paths, then marks the provider as logged in. Cookies persist for future sessions.

## Privacy

- All data stays on the local machine.
- No API keys are stored or needed.
- Authentication uses each provider's website directly.
- History lives in `history.json` and can be wiped with `/clear-all`.
- Cookies live in `~/.wiai/profile` and are removed only when the directory is deleted or the widget is uninstalled.