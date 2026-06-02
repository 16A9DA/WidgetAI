import json
from .baseproviders import BaseAIProvider


class ClaudeProvider(BaseAIProvider):
    name = "claude"
    domains = ("claude.ai", "claude.com")

    def matches(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    def inject_script(self, prompt: str) -> str:
        prompt_js = json.dumps(prompt)
        return f"""
        (() => {{
            const promptText = {prompt_js};
            const editor =
                document.querySelector('[contenteditable="true"][role="textbox"]') ||
                document.querySelector('div[contenteditable="true"]') ||
                document.querySelector('textarea');

            if (!editor)
                return "Editor not found";

            editor.focus();

            if (editor.tagName === "TEXTAREA") {{
                editor.value = promptText;
                editor.dispatchEvent(new Event("input", {{ bubbles: true }}));
                editor.dispatchEvent(new Event("change", {{ bubbles: true }}));
                return "Prompt inserted into textarea";
            }}

            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, promptText);

            editor.dispatchEvent(new InputEvent("input", {{
                bubbles: true,
                 promptText,
                inputType: "insertText"
            }}));

            return "Prompt inserted into editable";
        }})();
        """

    def submit_script(self) -> str:
        return """
        (() => {
            const btn =
                document.querySelector('button[aria-label*="Send"]') ||
                document.querySelector('button[aria-label*="send"]') ||
                document.querySelector('button[type="submit"]');

            if (btn && !btn.disabled) {
                btn.click();
                return "Send button clicked";
            }

            const editor =
                document.querySelector('[contenteditable="true"][role="textbox"]') ||
                document.querySelector('div[contenteditable="true"]') ||
                document.querySelector('textarea');

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

    def extract_script(self) -> str:
        return """
        (() => {
            const candidates = [
                ...document.querySelectorAll('[data-is-streaming]'),
                ...document.querySelectorAll('[class*="assistant"]'),
                ...document.querySelectorAll('article'),
                ...document.querySelectorAll('[role="article"]')
            ];

            const texts = candidates
                .map(el => (el.innerText || el.textContent || "").trim())
                .filter(Boolean)
                .filter(t => t.length > 20);

            if (!texts.length)
                return "";

            return texts[texts.length - 1];
        })();
        """
