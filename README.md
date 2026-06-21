# WIAI

WIAI is a compact, always on top, terminal style AI widget. It gives you one
small command console for ChatGPT, Claude, and Perplexity without any API keys.
The widget launches as a thin strip that shows the time, the active provider,
and a single input line. It grows only when there is output to display and
collapses back to its compact footprint when you clear it.

WIAI is built to feel like a command widget, not a chat application. The
interaction is command first, keyboard driven, and visually minimal.

## Highlights

* Compact floating widget that stays small and always on top.
* Command first interaction through simple slash commands.
* Three providers in one place: ChatGPT, Claude, and Perplexity.
* Persistent sessions, so you normally sign in once per provider.
* Responses extracted and displayed inside the widget itself.
* Lightweight local history with cross provider continuity.
* Clean shutdown with no orphan browser processes.

## Requirements

* Python 3.10 or newer
* PySide6 (Qt for Python) with the WebEngine module

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



## Running

```bash
python wiai.py

```

On first launch:

1. Sign in to a provider with `/login chatgpt` (or `claude` or `perplexity`).
   A browser window opens for that provider. Complete the sign in there. The
   window tucks itself away once you are signed in, and the widget stays open
   the entire time.
2. Choose the active provider with `/chatgpt`, `/claude`, or `/perplexity`.
3. Type a prompt and press Enter. The reply appears inside the widget.

Cookies and storage persist in `~/.wiai`, so you usually log in only once per
provider.

## Commands

* `/chatgpt` : Switch the active provider to ChatGPT
* `/claude` : Switch the active provider to Claude
* `/perplexity` : Switch the active provider to Perplexity
* `/login [provider]` : Sign in, using the current provider if omitted
* `/history` : Show recent history in a compact format
* `/clear-all` : Clear the output and stored history
* `/debug` : Report what extraction finds on the page
* `/help`, `/helpme` : Show the command help
* `/exit` : Close the widget cleanly

Any text that does not start with a slash is sent to the active provider as a
prompt.

## Architecture

WIAI is organized into small modules, each with a single responsibility.

* `wiai.py` : The widget itself. Handles the UI, clock, status row, compact and expand behavior, and signal wiring.
* `command_parser.py` : Parses slash commands and dispatches them to callbacks.
* `browser_handler.py` : Maintains one browser view per provider, sends prompts, and reads replies.
* `login_manager.py` : Tracks the login state for each provider.
* `history_manager.py` : Stores JSON backed recent history in `~/.wiai/history.json`.
* `providers.py` : Provider abstraction holding URLs and DOM selectors, defined declaratively.

All provider specific knowledge lives in `providers.py`. Everything else is
provider agnostic, so adding a new provider is a single entry in that file.

## Login and session handling

WIAI uses a single persistent browser profile. Persistent cookies are forced on,
and cache and storage are pointed at `~/.wiai/profile`, so sessions survive
restarts. Each provider has one long lived browser view that is normally hidden.

The `/login` command reuses that provider view, shows it as a normal top level
window pointed at the sign in page, and polls the page state. Login is inferred
from real page state: the URL has left any sign in path (such as `/login`,
`/auth`, `/signin`, `/signup`, `/oauth`) and the application shell is present.
This is a genuine session check, not a simulated login. When login is detected,
the provider is marked as signed in and the window is hidden. The login window
is reused rather than destroyed, so closing it never closes the widget.

## Command flow

Pressing Enter in the input line routes the text to the submit handler. If the
text begins with a slash, the command parser interprets it and calls the matching
callback (switch provider, login, history, clear, debug, or exit) or returns the
help text. Otherwise the text is treated as a prompt: the widget verifies the
login state, prepends a small amount of recent history for continuity across
providers, and hands the prompt to the browser handler.

## Response extraction

Sending a prompt injects JavaScript into the hidden browser view to type the text
into the provider's real input and submit it. A timer then polls the page for the
latest assistant message and emits the result once the text stops changing
(streaming has finished) or once a timeout is reached. The whole pipeline is
signal and slot driven, so the interface never freezes while waiting for a reply.

If a reply does not appear, run `/debug`. It reports the current URL and whether
the input, send button, and response selectors matched on the live page, along
with a snippet of the latest reply. Any field that reports NOT FOUND points to
the exact selector in `providers.py` that needs updating.

## Compact and expand behavior

WIAI starts collapsed, showing only the status row and the input line, with the
output area hidden and the height locked. The first piece of output (a reply,
history, help, or a system message) expands the widget: it unlocks the height,
shows the output area, and grows to a comfortable reading size while remaining
widget sized rather than full screen. The `/clear-all` command collapses the
widget back to the thin strip. In short, the widget grows only when there is
something to show.

## Data and privacy

* All data stays on the local machine.
* No API keys are stored or required.
* Authentication uses each provider's own website directly.
* Cookies and storage live in `~/.wiai/profile`.
* History lives in `~/.wiai/history.json` and is removed with `/clear-all`.

## Notes and limitations

WIAI drives the providers' web interfaces rather than official APIs, so it
depends on those pages remaining reachable and on your session staying valid.
Provider sites change their page structure over time. If a prompt stops
producing output, use `/debug` and update the relevant selectors in
`providers.py`.