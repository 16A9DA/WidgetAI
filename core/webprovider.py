from pathlib import Path
import json

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView


class WebProviderWindow(QWidget):
    def __init__(self, url: str, prompt: str):
        super().__init__()

        self.setWindowTitle("WidgetAI Web Provider")
        self.resize(1100, 760)

        self.prompt = prompt

        self.last_response = ""
        self.same_count = 0

        layout = QVBoxLayout()

        self.browser = QWebEngineView()

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(self.browser, 4)
        layout.addWidget(self.output, 1)

        self.setLayout(layout)

        self.profile = self.create_persistent_profile()
        self.page = QWebEnginePage(self.profile, self.browser)

        self.browser.setPage(self.page)

        self.browser.loadFinished.connect(self.on_load_finished)
        self.browser.setUrl(QUrl(url))

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_response)

    def create_persistent_profile(self):
        base_dir = Path.home() / ".widgetai" / "webengine"

        storage_dir = base_dir / "storage"
        cache_dir = base_dir / "cache"

        storage_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        profile = QWebEngineProfile("WidgetAIProfile", self)

        profile.setPersistentStoragePath(str(storage_dir))
        profile.setCachePath(str(cache_dir))

        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.DiskHttpCache
        )

        return profile

    def on_load_finished(self, ok):
        if not ok:
            self.output.setPlainText("Failed to load page.")
            return

        self.output.setPlainText("Page loaded...")
        QTimer.singleShot(5000, self.inject_prompt)

    def inject_prompt(self):
        prompt_js = json.dumps(self.prompt)

        script = f"""
        (() => {{
            const promptText = {prompt_js};

            const editor =
                document.querySelector('#prompt-textarea') ||
                document.querySelector('[contenteditable="true"]') ||
                document.querySelector('[role="textbox"]');

            if (!editor)
                return "Editor not found";

            editor.focus();

            if (editor.tagName === "TEXTAREA") {{
                editor.value = promptText;
                editor.dispatchEvent(
                    new Event("input", {{ bubbles: true }})
                );
            }}
            else {{
                editor.textContent = promptText;

                editor.dispatchEvent(
                    new InputEvent("input", {{
                        bubbles: true,
                        data: promptText,
                        inputType: "insertText"
                    }})
                );
            }}

            return "Prompt inserted";
        }})();
        """

        self.page.runJavaScript(script, self.after_injection)

    def after_injection(self, result):
        self.output.setPlainText(str(result))
        QTimer.singleShot(1500, self.submit_prompt)

    def submit_prompt(self):
        script = """
        (() => {
            const btn =
                document.querySelector('button[data-testid="send-button"]') ||
                document.querySelector('button[aria-label*="Send"]') ||
                document.querySelector('button[aria-label*="send"]');

            if (btn) {
                if (btn.disabled) {
                    return "Send button found but disabled";
                }

                btn.click();
                return "Send button clicked";
            }

            const editor =
                document.querySelector('#prompt-textarea') ||
                document.querySelector('[contenteditable="true"][role="textbox"]') ||
                document.querySelector('[contenteditable="true"]');

            if (!editor)
                return "No editor for Enter fallback";

            editor.focus();

            const enterDown = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true,
                cancelable: true
            });

            const enterUp = new KeyboardEvent('keyup', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true,
                cancelable: true
            });

            editor.dispatchEvent(enterDown);
            editor.dispatchEvent(enterUp);

            return "Enter fallback dispatched";
        })();
        """

        self.page.runJavaScript(script, self.after_submit)


        self.page.runJavaScript(script, self.after_submit)

    def after_submit(self, result):
        self.output.setPlainText(str(result))

        self.last_response = ""
        self.same_count = 0

        self.poll_timer.start(2000)

    def poll_response(self):
        script = """
        (() => {
            const assistantNodes = [
                ...document.querySelectorAll('[data-message-author-role="assistant"]')
            ];

            const texts = assistantNodes
                .map(el => (el.innerText || el.textContent || "").trim())
                .filter(Boolean)
                .filter(t => t.length > 20);

            if (texts.length)
                return texts[texts.length - 1];

            const articles = [...document.querySelectorAll('article')];
            if (!articles.length)
                return "";

            const lastArticle = articles[articles.length - 1];
            return (lastArticle.innerText || lastArticle.textContent || "").trim();
        })();
        """

        self.page.runJavaScript(script, self.handle_poll_result)


    def handle_poll_result(self, text):
        if not text:
            return

        # Update bottom window continuously
        if text != self.last_response:
            self.output.clear()
            self.output.setPlainText(text)

        if text == self.last_response:
            self.same_count += 1
        else:
            self.same_count = 0
            self.last_response = text

        if self.same_count >= 3:
            self.poll_timer.stop()
            self.output.append("\n\n===== COMPLETE =====")


