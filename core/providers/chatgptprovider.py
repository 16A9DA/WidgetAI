import json
from . import baseproviders
from .baseproviders import BaseAIProvider


class ChatGPTProvider(BaseAIProvider):
    name = "chatgpt"
    domains = ("chatgpt.com", "chat.openai.com")

    def inject_script(self, prompt: str) -> str:
        prompt_js = json.dumps(prompt)
        return f"""
        (() => {{
            const promptText = {prompt_js};
            const editor =
                document.querySelector('#prompt-textarea') ||
                document.querySelector('[contenteditable="true"][role="textbox"]') ||
                document.querySelector('[contenteditable="true"]');

            if (!editor)
                return "Editor not found";

            editor.focus();

            if (editor.tagName === "TEXTAREA") {{
                editor.value = promptText;
                editor.dispatchEvent(new Event("input", {{ bubbles: true }}));
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

            return "Prompt inserted into ProseMirror editor";
        }})();
        """

    def submit_script(self) -> str:
        return """
        (() => {
            const btn =
                document.querySelector('button[data-testid="send-button"]') ||
                document.querySelector('button[aria-label*="Send"]') ||
                document.querySelector('button[aria-label*="send"]');

            if (btn && !btn.disabled) {
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

    def extract_script(self) -> str:
        return """
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
