import json
from .baseproviders import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    name = "gemini"
    domains = ("gemini.google.com", "ai.google.dev")

    def inject_script(self, prompt: str) -> str:
        prompt_js = json.dumps(prompt)
        return f"""
        (() => {{
            const promptText = {prompt_js};
            const editor =
                document.querySelector('textarea[aria-label*="message"]') ||
                document.querySelector('textarea[aria-label*="Message"]') ||
                document.querySelector('textarea[role="textbox"]') ||
                document.querySelector('[contenteditable="true"][role="textbox"]') ||
                document.querySelector('[contenteditable="true"]');

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
                document.querySelector('button[aria-label*="Submit"]') ||
                document.querySelector('button[type="submit"]');

            if (btn && !btn.disabled) {
                btn.click();
                return "Send button clicked";
            }

            const editor =
                document.querySelector('textarea[aria-label*="message"]') ||
                document.querySelector('textarea[aria-label*="Message"]') ||
                document.querySelector('textarea[role="textbox"]') ||
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

            return "Enter key fallback dispatched";
        })();
"""

    def extract_script(self) -> str:
        return """
        (() => {
            const assistantNodes = [
                ...document.querySelectorAll('[data-response-index]'),
                ...document.querySelectorAll('[class*="response"]'),
                ...document.querySelectorAll('article')
            ];

            if (!assistantNodes.length)
                return "";

            const lastNode = assistantNodes[assistantNodes.length - 1];
            const text = (lastNode.innerText || lastNode.textContent || "").trim();

            if (text.length > 20)
                return text;

            const paragraphs = [...lastNode.querySelectorAll('p')];
            if (paragraphs.length) {
                return paragraphs.map(p => p.innerText).join('\\n\\n').trim();
            }

            return "";
        })();
"""
