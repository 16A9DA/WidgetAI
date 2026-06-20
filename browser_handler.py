import time
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl, QTimer, QEventLoop


class BrowserHandler:

    def __init__(self, login_manager):
        self.login_manager = login_manager
        self.browsers = {}
        self.pages = {}
        self.active_browser = None
        self.active_service = None
        self.response_ready = False
        self.response_text = ""

        self.initialize_browsers()

    def initialize_browsers(self):
        services = ["chatgpt", "claude", "perplexity"]
        urls = {
            "chatgpt": "https://chat.openai.com/",
            "claude": "https://claude.ai/chats",
            "perplexity": "https://www.perplexity.ai/",
        }

        for service in services:
            browser = QWebEngineView()
            browser.setVisible(False)
            browser.resize(1024, 768)

            page = QWebEnginePage(browser)
            browser.setPage(page)

            page.loadFinished.connect(
                lambda ok, s=service: self.on_load_finished(ok, s)
            )

            self.browsers[service] = browser
            self.pages[service] = page

        self.set_active_service("chatgpt")

    def set_active_service(self, service):

        if service in self.browsers:
            self.active_service = service
            self.active_browser = self.browsers[service]
            return True
        return False

    def on_load_finished(self, ok, service):

        if ok:
            print(f"{service} page loaded successfully")
        else:
            print(f"Failed to load {service} page")

    def send_query(self, query):
        """Send a query to the active service using JavaScript/DOM interaction."""
        if not self.active_browser or not self.active_service:
            return "Error: No active browser"

        # Clear previous response state
        self.response_ready = False
        self.response_text = ""

        # Execute JavaScript to send query to the active service
        self._execute_query_javascript(query)

        # Return immediately - response will be available via get_response() after processing
        return ""

    def simulate_response(self):

        self.response_ready = True

    def get_simulated_response(self, query):

        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        responses = {
            "chatgpt": f"[ChatGPT Simulation] Received query at {timestamp}: '{query}'. This is a simulated response showing the widget is working correctly.",
            "claude": f"[Claude Simulation] Processing your request at {timestamp}: '{query}'. The widget successfully interfaces with the service.",
            "perplexity": f"[Perplexity Simulation] Searching for information at {timestamp}: '{query}'. Results would appear here in a real implementation.",
        }

        return responses.get(
            self.active_service,
            f"[Simulation] Response from {self.active_service} at {timestamp}",
        )

    def inject_javascript(self, script):

        if self.active_browser and self.active_browser.page():
            self.active_browser.page().runJavaScript(script)

    def get_page_content(self):

        if self.active_browser and self.active_browser.page():
            pass

    def _execute_query_javascript(self, query):
        """Execute JavaScript to input query and submit for the active service."""
        # Escape the query for JavaScript string
        escaped_query = query.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        escaped_query = escaped_query.replace('`', '\\`')  # Escape backticks too

        # Service-specific JavaScript to input query and submit
        js_script = f"""
        (function() {{
            // Determine which service we're dealing with based on URL or page content
            const url = window.location.href;

            let input = null;
            let submitButton = null;

            if (url.includes('claude.ai')) {{
                // Claude.ai selectors
                input = document.querySelector('div[contenteditable="true"][data-placeholder*="Ask Claude"]');
                if (!input) {{
                    input = document.querySelector('div[contenteditable="true"]');
                }}
                // Submit button or use Enter key
                submitButton = document.querySelector('button[aria-label*="Send"]');
            }} else if (url.includes('chat.openai.com')) {{
                // ChatGPT selectors
                input = document.querySelector('textarea[id="prompt-textarea"]');
                if (!input) {{
                    input = document.querySelector('textarea[placeholder*="Ask anything"]');
                }}
                if (!input) {{
                    input = document.querySelector('div[contenteditable="true"]');
                }}
                submitButton = document.querySelector('button[data-testid="send-button"]');
            }} else if (url.includes('perplexity.ai')) {{
                // Perplexity.ai selectors
                input = document.querySelector('textarea[placeholder*="Ask anything"]');
                if (!input) {{
                    input = document.querySelector('div[contenteditable="true"]');
                }}
                submitButton = document.querySelector('button[aria-label*="Submit"]');
            }} else {{
                // Fallback to generic selectors
                input = document.querySelector('textarea, div[contenteditable="true"]');
                if (input && input.tagName === 'DIV') {{
                    // Prefer textarea over div if both exist
                    const textarea = document.querySelector('textarea');
                    if (textarea) input = textarea;
                }}
                submitButton = document.querySelector('button[type="submit"], button:contains("Send"), button:contains("→")');
            }}

            if (input) {{
                // Focus and clear input
                input.focus();
                if (input.tagName === 'TEXTAREA') {{
                    input.value = '';
                }} else {{
                    input.innerHTML = '';
                }}

                // Type the query
                if (input.tagName === 'TEXTAREA') {{
                    input.value = arguments[0];
                }} else {{
                    input.innerHTML = arguments[0];
                }}

                // Trigger input event
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));

                // Try to click submit button if found
                let submitted = false;
                if (submitButton && submitButton.offsetParent !== null) {{
                    submitButton.click();
                    submitted = true;
                }}

                // If no button found or clicking failed, try pressing Enter
                if (!submitted) {{
                    input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
                    input.dispatchEvent(new KeyboardEvent('keypress', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
                    input.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
                }}

                return true;
            }}

            return false;
        }})();
        """

        if self.active_browser and self.active_browser.page():
            self.active_browser.page().runJavaScript(js_script, escaped_query)

    def wait_for_response(self, timeout_ms=20000):
        """Wait for response to be ready with timeout by polling for response indicators via JavaScript."""
        import time

        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            # Check for response using JavaScript
            response_text = self._check_for_response()
            if response_text and len(response_text.strip()) > 0:
                self.response_ready = True
                self.response_text = response_text.strip()
                return True
            time.sleep(0.5)  # Check every 500ms to reduce overhead
        return False

    def _check_for_response(self):
        """Check if AI response has been received and extract it using JavaScript.
        Returns the response text if found, empty string if not ready yet."""
        js_script = """
        (function() {
            // Service-specific response detection

            // Get the most recent assistant/AI message
            let latestResponse = '';

            // Try service-specific selectors first
            const url = window.location.href;

            if (url.includes('claude.ai')) {{
                // Claude.ai: look for assistant message content
                const elements = document.querySelectorAll('[data-testid="chat-assistant-message"] .message-content, .assistant-message');
                if (elements.length > 0) {{
                    const last = elements[elements.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }}
            }} else if (url.includes('chat.openai.com')) {{
                // ChatGPT: look for assistant message
                const elements = document.querySelectorAll('[data-message-author-role="assistant"]');
                if (elements.length > 0) {{
                    const last = elements[elements.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }}
            }} else if (url.includes('perplexity.ai')) {{
                // Perplexity: look for answer content
                const elements = document.querySelectorAll('.answer, .ai-response');
                if (elements.length > 0) {{
                    const last = elements[elements.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }}
            }}

            // Fallback: look for any recent message that appears to be from AI
            if (!latestResponse || latestResponse.length < 10) {{
                const messageSelectors = [
                    '.message:last-child',
                    '.chat-message:last-child',
                    '[role="log"] > div:last-child'
                ];

                for (const selector of messageSelectors) {{
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {{
                        const last = elements[elements.length - 1];
                        const text = (last.innerText || last.textContent || '').trim();
                        // Heuristic: if it's substantial and not a user message, assume it's AI response
                        if (text.length > 15 &&
                            !text.startsWith('You:') &&
                            !text.toLowerCase().includes('loading') &&
                            !text.toLowerCase().includes('thinking')) {{
                            latestResponse = text;
                            break;
                        }}
                    }}
                }}
            }}

            // Final check: if we have a response that seems complete
            if (latestResponse && latestResponse.length > 10) {{
                // Check if it looks like it's done loading (not showing loading indicators)
                const lowerText = latestResponse.toLowerCase();
                if (!lowerText.includes('loading') &&
                    !lowerText.includes('generating') &&
                    !lowerText.includes('thinking...') &&
                    !latestResponse.endsWith('...')) {{
                    return latestResponse;
                }}
            }}

            return '';
        })();
        """

        if self.active_browser and self.active_browser.page():
            # Run JavaScript and get result
            from PySide6.QtCore import QEventLoop
            result = [None]  # Use list to store result from callback
            loop = QEventLoop()

            def callback(res):
                result[0] = res
                loop.quit()

            self.active_browser.page().runJavaScript(js_script, callback)
            loop.exec()  # Wait for JavaScript to finish

            return result[0] if result[0] is not None else ""
        return ""
