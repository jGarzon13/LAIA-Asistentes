
import time

from core.models.groq_provider import GroqProvider


def main():
    print("=" * 50)
    print("LAIA - Prueba de conexión con Groq")
    print("=" * 50)

    try:
        provider = GroqProvider(
            model="qwen/qwen3.8-27b"
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente académico de prueba. "
                    "Responde en español de manera breve."
                )
            },
            {
                "role": "user",
                "content": (
                    "Explica qué es RAG en inteligencia "
                    "artificial en máximo tres oraciones."
                )
            }
        ]

        print(f"\nModelo: {provider.model}")
        print("Consultando Groq...\n")

        start = time.perf_counter()

        response = provider.generate(messages)

        elapsed = time.perf_counter() - start

        print("Respuesta:\n")
        print(response)

        print(f"\nTiempo de respuesta: {elapsed:.2f} s")

    except RuntimeError as exc:
        print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
