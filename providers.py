from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Provider:
    key: str                      
    label: str                   
    chat_url: str                 
    login_url: str               
    input_selectors: List[str]    
    submit_selectors: List[str]   
    response_selectors: List[str] 
    contenteditable: bool = False
    login_hosts: List[str] = field(default_factory=list)


PROVIDERS = {
    "chatgpt": Provider(
        key="chatgpt",
        label="ChatGPT",
        chat_url="https://chatgpt.com/",
        login_url="https://chatgpt.com/auth/login",
        input_selectors=[
            "#prompt-textarea",
            'div[contenteditable="true"]#prompt-textarea',
            "textarea#prompt-textarea",
        ],
        submit_selectors=[
            'button[data-testid="send-button"]',
            'button[aria-label*="Send" i]',
        ],
        response_selectors=[
            '[data-message-author-role="assistant"] .markdown',
            '[data-message-author-role="assistant"]',
        ],
        contenteditable=True,
        login_hosts=["chatgpt.com", "openai.com"],
    ),
    "claude": Provider(
        key="claude",
        label="Claude",
        chat_url="https://claude.ai/new",
        login_url="https://claude.ai/login",
        input_selectors=[
            'div[contenteditable="true"].ProseMirror',
            'div[contenteditable="true"]',
        ],
        submit_selectors=[
            'button[aria-label*="Send" i]',
            'button[data-testid="send-button"]',
        ],
        response_selectors=[
            ".font-claude-message",
            '[data-testid="chat-assistant-message"]',
        ],
        contenteditable=True,
        login_hosts=["claude.ai"],
    ),
    "perplexity": Provider(
        key="perplexity",
        label="Perplexity",
        chat_url="https://www.perplexity.ai/",
        login_url="https://www.perplexity.ai/",
        input_selectors=[
            'textarea[placeholder*="Ask" i]',
            'div[contenteditable="true"]',
            "textarea",
        ],
        submit_selectors=[
            'button[aria-label*="Submit" i]',
            'button[data-testid="submit-button"]',
            'button[type="submit"]',
        ],
        response_selectors=[
            '[data-testid="answer"]',
            ".prose",
            ".answer",
        ],
        contenteditable=False,
        login_hosts=["perplexity.ai"],
    ),
}

LOGIN_PATH_FRAGMENTS = ("/login", "/auth", "/signin", "/signup", "/oauth")

ORDER = ["chatgpt", "claude", "perplexity"]


def get(key: str) -> Provider:
    return PROVIDERS[key]


def exists(key: str) -> bool:
    return key in PROVIDERS
