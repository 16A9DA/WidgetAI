# WIWI Widget

WIWI Widget: A terminal-callable desktop widget providing unified access to ChatGPT, Claude, and Perplexity without individual API keys or subscriptions.

## Features

- Terminal Accessible: Launch with `/wiai` command from terminal
- Multi-Service Support: Access ChatGPT, Claude, and Perplexity in one interface
- Secure Login: Handle authentication for each service
- Conversation History: Track and review conversations
- Clear History: Easily wipe conversation data
- Cross-Platform: Works on Windows, macOS, and Linux
- Docker Ready: Containerized for easy deployment

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wiai-widget.git
   cd wiai-widget
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python wiai.py
   ```

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t wiai .
   ```

2. Run the container:
   ```bash
   docker run -it --rm \
     -e DISPLAY=$DISPLAY \
     -v /tmp/.X11-unix:/tmp/.X11-unix \
     wiai-widget
   ```

## Usage

### Basic Commands

Once the widget is running, use these slash commands:

- `/chatgpt` Switch to ChatGPT service
- `/claude` Switch to Claude service
- `/perplexity` Switch to Perplexity service
- `/login` Login to the current active service
- `/history` Show conversation history
- `/clear-all` Clear all conversation history

### Example Workflow

1. Launch the widget: `python wiai.py`
2. Switch to preferred service: `/claude`
3. Login if needed: `/login` (complete login in the popped-up window)
4. Start chatting: Type questions directly
5. Switch services: `/chatgpt` to talk to ChatGPT instead
6. Review history: `/history` to see past conversations
7. Clear data: `/clear-all` to start fresh

## Architecture

The widget follows a clean modular architecture:

- wiai.py: Main application with Qt GUI
- browser_handler.py: Manages hidden browser instances for each service
- command_parser.py: Handles slash command parsing and execution
- history_manager.py: Stores and retrieves conversation history
- login_manager.py: Manages authentication states and login flows

## How It Works

1. The widget uses QtWebEngine to create hidden browser instances for each service.
2. When a query is typed, it is sent to the active service's browser.
3. Responses are captured and displayed in the chat interface.
4. Login processes use visible browsers for security, then transfer session to hidden browsers.
5. All conversations are stored locally in history.json.
6. Slash commands allow switching services and managing the widget.

## Security and Privacy

- All data is stored locally on the machine.
- No API keys are needed or stored.
- Login credentials are handled by the official service websites.
- Conversation history is saved only locally and can be cleared anytime.
- The widget does not modify or intercept communications with the services.

## Customization

For developers looking to extend or modify the widget:

- Add new services by extending service lists in browser_handler.py and login_manager.py.
- Improve response parsing by implementing actual DOM traversal in browser_handler.py.
- Enhance history management with search, filtering, or export features.
- Add settings panel for configuring appearance and behavior.

## Acknowledgments

Built with PySide6, inspired by the desire to make AI services more accessible without managing multiple subscriptions or API keys.