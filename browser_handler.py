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
        if not self.active_browser or not self.active_service:
            return "Error: No active browser"

        self.response_ready = False
        self.response_text = ""

        return self._execute_query_javascript(query)

    def get_response(self):
        """Return the last captured response text."""
        return self.response_text

    def _execute_query_javascript(self, query):
        """Inject query into the active service's input field and submit."""
        # Escape the query string for safe JS embedding
        escaped = query.replace("\\", "\\\\")
        escaped = escaped.replace("'", "\\'")
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace("`", "\\`")
        escaped = escaped.replace("\n", "\\n")

        js_script = f"""
        (function() {{
            const url = window.location.href;
            let input = null;
            let submitButton = null;

            // Provider-specific selectors
            if (url.includes('claude.ai')) {{
                input = document.querySelector('div[contenteditable="true"][data-placeholder*="Ask"], div[contenteditable="true"]');
                submitButton = document.querySelector('button[aria-label*="Send"], button[aria-label*="send"]');
            }} else if (url.includes('chat.openai.com') || url.includes('chatgpt.com')) {{
                input = document.querySelector('textarea[id="prompt-textarea"], textarea[placeholder*="Ask"], div[contenteditable="true"]');
                submitButton = document.querySelector('button[data-testid="send-button"], button[aria-label*="Send"]');
            }} else if (url.includes('perplexity.ai')) {{
                input = document.querySelector('textarea[placeholder*="Ask"], textarea, div[contenteditable="true"]');
                submitButton = document.querySelector('button[aria-label*="Submit"], button[type="submit"], button svg');
            }} else {{
                input = document.querySelector('textarea, div[contenteditable="true"]');
                submitButton = document.querySelector('button[type="submit"]');
            }}

            if (!input) {{
                console.error('WIAI: Could not find input element');
                return false;
            }}

            // Focus and clear
            input.focus();
            if (input.tagName === 'TEXTAREA') {{
                input.value = '';
            }} else if (input.contentEditable) {{
                input.innerHTML = '<p><br></p>';
            }}

            // Set query text
            const queryText = '{escaped}';
            if (input.tagName === 'TEXTAREA') {{
                input.value = queryText;
            }} else {{
                input.innerHTML = '<p>' + queryText.replace(/\\n/g, '<br>') + '</p>';
            }}

            // Dispatch input event to trigger any listeners
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));

            // Try to click submit button, fallback to Enter key
            let submitted = false;
            if (submitButton && submitButton.offsetParent !== null) {{
                submitButton.click();
                submitted = true;
            }}

            if (!submitted) {{
                const enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true,
                    cancelable: true,
                }});
                input.dispatchEvent(enterEvent);
            }}

            return true;
        }})();
        """

        if self.active_browser and self.active_browser.page():
            self.active_browser.page().runJavaScript(js_script)
            return True
        return False

    def wait_for_response(self, timeout_ms=20000):
        import time

        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            response_text = self._check_for_response()
            if response_text and len(response_text.strip()) > 0:
                self.response_ready = True
                self.response_text = response_text.strip()
                return True
            time.sleep(0.5)
        return False

    def _check_for_response(self):
        js_script = """
        (function() {
            let latestResponse = '';
            const url = window.location.href;

            // Provider-specific selectors for assistant responses
            if (url.includes('claude.ai')) {
                const claudeEls = document.querySelectorAll('[data-testid="chat-assistant-message"] .message-content, .assistant-message, .message-content__text, article[data-testid="chat-message"]');
                if (claudeEls.length > 0) {
                    const last = claudeEls[claudeEls.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }
            } else if (url.includes('chat.openai.com') || url.includes('chatgpt.com')) {
                const chatEls = document.querySelectorAll('[data-message-author-role="assistant"] .markdown, [data-message-author-role="assistant"], .group .prose, .text-message');
                if (chatEls.length > 0) {
                    const last = chatEls[chatEls.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }
            } else if (url.includes('perplexity.ai')) {
                const perpEls = document.querySelectorAll('.answer, .ai-response, .prose, [data-testid="copilot-response"]');
                if (perpEls.length > 0) {
                    const last = perpEls[perpEls.length - 1];
                    latestResponse = last.innerText || last.textContent || '';
                }
            }

            // Fallback: try generic selectors for any remaining response text
            if (!latestResponse || latestResponse.length < 20) {
                const fallbackSelectors = [
                    '[data-message-author-role="assistant"]:last-child',
                    '.message:last-child',
                    '.chat-message:last-child',
                    '[role="log"] > div:last-child',
                    '.conversation-container .message:last-child',
                    'article:last-child .prose',
                ];

                for (const selector of fallbackSelectors) {
                    try {
                        const el = document.querySelector(selector);
                        if (el) {
                            const text = (el.innerText || el.textContent || '').trim();
                            if (text.length > 20 &&
                                !text.toLowerCase().includes('you:') &&
                                !text.toLowerCase().includes('ask anything')) {
                                latestResponse = text;
                                break;
                            }
                        }
                    } catch (e) {}
                }
            }

            // Validate: must be non-empty, non-loading, and reasonably long
            if (latestResponse && latestResponse.length > 15) {
                const lowerText = latestResponse.toLowerCase();
                if (!lowerText.includes('loading') &&
                    !lowerText.includes('generating') &&
                    !lowerText.includes('thinking') &&
                    !lowerText.includes('please wait') &&
                    !latestResponse.endsWith('...') &&
                    !latestResponse.endsWith('…')) {
                    return latestResponse;
                }
            }

            return '';
        })();
        """

        if self.active_browser and self.active_browser.page():
            from PySide6.QtCore import QEventLoop
            result = [None]
            loop = QEventLoop()

            def callback(res):
                result[0] = res
                loop.quit()

            self.active_browser.page().runJavaScript(js_script, callback)
            loop.exec()

            return result[0] if result[0] is not None else ""
        return ""

    def get_page_content(self):

        if self.active_browser and self.active_browser.page():
            pass
