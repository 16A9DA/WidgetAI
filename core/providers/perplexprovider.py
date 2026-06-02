import json
from .baseproviders import BaseAIProvider


class PerplexityProvider(BaseAIProvider):
    name = "perplexity"
    domains = ("perplexity.ai", "www.perplexity.ai")

    def matches(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    def inject_script(self, prompt: str) -> str:
        prompt_js = json.dumps(prompt)
        return f"""
        (() => {{
            const promptText = {prompt_js};
            const editor =
                document.querySelector('textarea[placeholder*="Ask anything"]') ||
                document.querySelector('textarea[placeholder*="ask"]') ||
                document.querySelector('textarea[aria-label*="message"]') ||
                document.querySelector('textarea[role="textbox"]') ||
                document.querySelector('[contenteditable="true"]') ||
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
                document.querySelector('button[aria-label*="Submit"]') ||
                document.querySelector('button[aria-label*="submit"]') ||
                document.querySelector('button[aria-label*="Send"]') ||
                document.querySelector('button[type="submit"]') ||
                document.querySelector('button[class*="arrow"]') ||
                document.querySelector('button[title*="Send"]');

            if (btn && !btn.disabled) {
                btn.click();
                return "Send button clicked";
            }

            const editor =
                document.querySelector('textarea') ||
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
            const selectors = [
                '[data-testid*="answer"]',
                '[data-testid*="response"]',
                '[class*="answer"]',
                '[class*="response"]',
                '[class*="prose"]',
                'main article',
                'article',
                '[role="article"]',
                'main'
            ];

            const candidates = [];
            for (const selector of selectors) {
                for (const el of document.querySelectorAll(selector)) {
                    const text = (el.innerText || el.textContent || "").trim();
                    if (text && text.length > 80) {
                        candidates.push({
                            el,
                            text,
                            len: text.length
                        });
                    }
                }
            }

            if (!candidates.length) {
                return "";
            }

            const filtered = candidates.filter(item => {
                const text = item.text.toLowerCase();
                return !text.includes("ask anything") &&
                    !text.includes("follow-up") &&
                    !text.includes("sources") &&
                    !text.includes("related") &&
                    !text.includes("sign in");
            });

            const usable = filtered.length ? filtered : candidates;
            return usable[usable.length - 1].text;
        })();
        """

