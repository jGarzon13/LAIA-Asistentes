
import json
from urllib import request, error

from core.models.base import ModelProvider


class OllamaProvider(ModelProvider):

    def __init__(
        self,
        model: str = "gemma3:1b",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        messages: list[dict[str, str]]
    ) -> str:

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "temperature": 0.3
            }
        }

        data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url=f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                result = json.load(response)

            return result["message"]["content"]

        except error.URLError as exc:
            raise RuntimeError(
                f"No se pudo conectar con Ollama: {exc}"
            ) from exc

        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "La respuesta de Ollama no tiene el formato esperado."
            ) from exc
