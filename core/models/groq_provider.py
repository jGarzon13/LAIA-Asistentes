
import json
import os
from urllib import request, error

from core.models.base import ModelProvider


class GroqProvider(ModelProvider):

    def __init__(
        self,
        model: str = "qwen/qwen3.8-27b",
        api_key: str | None = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        self.base_url = (
            "https://api.groq.com/openai/v1/chat/completions"
        )

        if not self.api_key:
            raise RuntimeError(
                "No se encontró GROQ_API_KEY. "
                "Configura la variable de entorno."
            )

    def generate(
        self,
        messages: list[dict[str, str]]
    ) -> str:

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 1200,
            "stream": False
        }

        data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url=self.base_url,
            data=data,
            
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "LAIA-Academic-Assistants/0.2"
            },

            method="POST"
        )

        try:
            with request.urlopen(
                req,
                timeout=90
            ) as response:
                result = json.load(response)

            content = result["choices"][0]["message"]["content"]


            finish_reason = result["choices"][0].get("finish_reason")

            usage = result.get("usage", {})

            print("\n--- Métricas de Groq ---")
            print("Tokens de entrada:", usage.get("prompt_tokens"))
            print("Tokens de salida:", usage.get("completion_tokens"))
            print("Tokens totales:", usage.get("total_tokens"))
            print("Motivo de finalización:", finish_reason)
            print("-----------------------\n")

            if finish_reason == "length":
                print(
                    "ADVERTENCIA: La respuesta alcanzó "
                    "el límite de tokens y podría estar incompleta."
                )


            if not isinstance(content, str) or not content.strip():
                raise RuntimeError(
                    "Groq devolvió una respuesta sin contenido."
                )

            return content

        except error.HTTPError as exc:
            if exc.code == 401:
                message = "Clave API inválida o no autorizada."
            
            elif exc.code == 403:
                message = (
                    "Groq rechazó la solicitud (403). "
                    "Puede tratarse de permisos, restricciones "
                    "de cuenta o acceso al modelo."
                )

            elif exc.code == 404:
                message = "Modelo no disponible en esta cuenta."
            elif exc.code == 429:
                message = (
                    "Se alcanzó un límite de solicitudes "
                    "o tokens de Groq."
                )
            else:
                message = f"Error HTTP {exc.code} al consultar Groq."

            
                # Leer el motivo devuelto por Groq sin mostrar credenciales.
                try:
                    details = json.loads(
                        exc.read().decode("utf-8")
                    )
                    api_error = details.get("error", {})
                    if isinstance(api_error, dict):
                        reason = api_error.get("message", "")
                        if reason:
                            message += f" Detalle: {reason[:500]}"
                except (ValueError, UnicodeDecodeError):
                    pass


            raise RuntimeError(message) from exc

        except error.URLError as exc:
            raise RuntimeError(
                "No fue posible establecer conexión con Groq."
            ) from exc

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "La respuesta de Groq tiene un formato inesperado."
            ) from exc
