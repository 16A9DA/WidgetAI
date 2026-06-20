# Implementation Plan for WIWI Widget

## Files to Create ([NEW])

1. **wiai.py** - Main application entry point
   - Contains the main PySide6 application
   - Sets up the GUI interface
   - Handles command parsing and execution
   - Manages the hidden browser instances
   - Implements login, history, clear-all functionality

2. **browser_handler.py** - Handles hidden browser operations
   - Manages QtWebEngine instances for each service
   - Loads appropriate URLs for chatgpt, claude, perplexity
   - Parses responses from the web pages (simplified for demo)
   - Provides methods to send queries and retrieve responses

3. **command_parser.py** - Parses and executes slash commands
   - Handles /chatgpt, /claude, /perplexity to switch active service
   - Handles /login to initiate login process
   - Handles /clear-all to clear conversation history
   - Handles /history to display history
   - Routes regular queries to the active service browser

4. **history_manager.py** - Manages conversation history
   - Stores query-response pairs
   - Provides methods to add, retrieve, clear history
   - Optionally saves history to file

5. **login_manager.py** - Handles authentication logic
   - Manages login state for each service
   - Opens visible browser for login when needed
   - Checks if user is logged in (via cookie inspection or similar)

6. **requirements.txt** - Python dependencies
   - PySide6
   - (Optional) other dependencies for web scraping if needed

7. **Dockerfile** - For containerizing the application
   - Based on python:3.9-slim or similar
   - Installs dependencies
   - Copies application code
   - Sets entry point to run wiai.py

8. **.gitignore** - Standard Python/git ignore rules

9. **README.md** - Project documentation
   - Description of the widget
   - Installation instructions
   - Usage guide
   - Features list

## Logical Changes

- **wiai.py**: 
  - Initialize QApplication
  - Create main window with input field and display area
  - Instantiate browser handlers for each service
  - Set up command parser and history manager
  - Handle submit button or enter key to process queries
  - Display responses in the chat area
  - Show login prompt when not authenticated

- **browser_handler.py**:
  - For each service, create a hidden QWebEngineView
  - Load the service's web interface (e.g., https://chat.openai.com for chatgpt)
  - Wait for page to load (simplified)
  - Provide send_query method that types into input and retrieves response
  - Note: Actual parsing will be simplified for demo purposes

- **command_parser.py**:
  - Detect messages starting with '/'
  - Map commands to appropriate actions
  - Switch active service browser for /chatgpt etc.
  - Trigger login process for /login
  - Clear history for /clear-all
  - Show history for /history

- **history_manager.py**:
  - Store each query and response with timestamp
  - Provide history as list of strings
  - Clear history method

- **login_manager.py**:
  - Track login state per service
  - For /login, launch visible browser to service login page
  - After login, update state and maybe copy cookies to hidden browser
  - Simple approach: assume login persists in hidden browser after visible login

## Dependencies
- PySide6 (for GUI and QtWebEngine)

## Notes
- Actual web parsing of chatgpt/claude/perplexity is complex and may violate terms of service; for portfolio/demo purposes, we'll implement simplified versions that simulate the behavior or use placeholder responses.
- The focus is on demonstrating clean architecture, command handling, and GUI integration rather than perfect web scraping.
- Dockerfile allows easy deployment and showcases DevOps skills.
