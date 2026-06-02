from .providers.chatgptprovider import ChatGPTProvider
from .providers.claudeprovider import ClaudeProvider
from .providers.perplexprovider import PerplexityProvider

PROVIDERS = [
    ChatGPTProvider(),
    ClaudeProvider(),
    PerplexityProvider(),
]

def get_provider(url: str):
    for provider in PROVIDERS:
        if provider.matches(url):
            return provider
    return None
