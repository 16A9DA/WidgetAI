# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Tasks

### Running the Application
- Local execution: `python wiai.py`
- Install dependencies: `pip install -r requirements.txt`
- Docker build: `docker build -t wiai .`
- Docker run: `docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix wiai`

### Development Workflow
1. Make changes to the Python modules as needed
2. Test by running the application locally
3. For service-specific changes, modify the corresponding handler:
   - `browser_handler.py`: Manages browser instances and query sending
   - `login_manager.py`: Handles authentication flows
   - `history_manager.py`: Manages conversation storage
   - `command_parser.py`: Processes slash commands
4. The main application logic resides in `wiai.py`

### Testing
Currently, there are no automated tests. To add testing:
- Create unit tests for each module (e.g., `test_browser_handler.py`)
- Use a testing framework like pytest
- Mock PySide6 components where necessary for headless testing

### Linting and Code Quality
No linting configuration exists. Consider adding:
- `flake8` or `pylint` for style checking
- `black` for code formatting
- Add configuration files (`.flake8`, `pyproject.toml`, etc.) to enforce standards

## Code Architecture and Structure

### High-Level Overview
The WIAI Widget follows a modular architecture with separated concerns:
- **Main Application (`wiai.py`)**: Contains the Qt GUI and orchestrates interactions between modules
- **Browser Handler (`browser_handler.py`)**: Manages hidden QWebEngineView instances for each service and simulates query responses
- **Command Parser (`command_parser.py`)**: Parses slash commands and routes them to appropriate callbacks
- **History Manager (`history_manager.py`)**: Stores and retrieves conversation history in JSON format
- **Login Manager (`login_manager.py`)**: Handles authentication states and launches visible browsers for login

### Data Flow
1. User enters text in the input field
2. If text starts with "/", it's treated as a command and processed by `CommandParser`
3. Otherwise, the text is treated as a query:
   - Application checks if user is logged in to the active service via `LoginManager`
   - If logged in, query is sent to `BrowserHandler` via a worker thread
   - `BrowserHandler` simulates sending the query to the active service's browser and returns a simulated response
   - Response is displayed in the chat area and saved to history via `HistoryManager`

### Module Responsibilities

#### wiai.py
- Sets up the Qt GUI components (chat display, input field, buttons)
- Initializes all manager instances
- Handles user interactions (sending messages, processing commands)
- Manages worker threads for query processing to avoid freezing the GUI
- Updates UI elements (status labels, service indicators)

#### browser_handler.py
- Creates and manages hidden QWebEngineView instances for ChatGPT, Claude, and Perplexity
- Tracks active service and browser
- Simulates query processing and response generation (currently returns hardcoded simulated responses)
- Provides methods for JavaScript injection and page content retrieval (for future enhancement)

#### command_parser.py
- Registers callback functions from the main application
- Parses slash commands using regex
- Routes commands to appropriate callbacks (service switching, login, history, clear)
- Provides help text for available commands

#### history_manager.py
- Loads and saves conversation history from/to `history.json` file
- Adds new entries with timestamp, query, response, and service
- Provides methods to retrieve all history or recent entries
- Clears history when requested

#### login_manager.py
- Tracks login state for each service
- Launches visible QWebEngineView windows for users to complete login
- Simulates login process (in a real implementation, would detect successful login via cookies or session storage)
- Provides logout functionality to clear login states and close visible browsers

### Extending the Widget
To add new services:
1. Add service constants to service lists in `browser_handler.py` (initialize_browsers) and `login_manager.py` (login_urls)
2. Update the service switching logic in `command_parser.py` to recognize the new service command
3. Enhance `browser_handler.py` to implement actual DOM traversal for sending queries and retrieving responses (currently simulated)
4. Consider adding service-specific handling in `login_manager.py` if login flows differ significantly

### Current Limitations and Future Improvements
- Responses are currently simulated; real implementation would require:
  - Actual DOM traversal to find input fields and submit buttons
  - Waiting for and extracting responses from the service's DOM
  - Handling dynamic content and potential anti-bot measures
- Login simulation uses a simple timer; real implementation would detect successful login
- No error handling for network issues or service changes
- History is stored locally only; consider encryption for sensitive data
- GUI is fixed size; consider making it more responsive or customizable

## Directory Structure
```
.
├── wiai.py                 # Main application
├── browser_handler.py      # Browser management and query simulation
├── command_parser.py       # Slash command processing
├── history_manager.py      # Conversation storage
├── login_manager.py        # Authentication handling
├── requirements.txt        # Python dependencies (PySide6)
├── Dockerfile              # Containerization instructions
├── README.md               # Project overview and usage instructions
└── history.json            # Auto-generated conversation history
```