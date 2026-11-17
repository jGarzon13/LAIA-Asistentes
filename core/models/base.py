
from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]]
    ) -> str:
        """Genera una respuesta a partir de mensajes."""
        pass
