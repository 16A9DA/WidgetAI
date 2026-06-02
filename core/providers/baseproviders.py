from abc import ABC, abstractmethod




class BaseAIProvider(ABC):
    name = "base"
    domains: tuple[str, ...] = ()

    def matches(self, url: str) -> bool:
        return any(domain in url for domain in self.domains)

    @abstractmethod
    def inject_script(self, prompt: str) -> str:
        pass

    @abstractmethod
    def submit_script(self) -> str:
        pass

    @abstractmethod
    def extract_script(self) -> str:
        pass
