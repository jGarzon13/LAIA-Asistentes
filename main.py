
from core.models.ollama_provider import OllamaProvider


def main():
    print("=" * 50)
    print("LAIA - Asistentes de prueba")
    print("Universidad Autónoma de Occidente")
    print("=" * 50)

    provider = OllamaProvider(model="gemma3:1b")

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente académico universitario. "
                "Responde en español, de forma clara y breve. "
                "Si no sabes algo, indícalo."
            )
        },
        {
            "role": "user",
            "content": (
                "Explica qué es una variable en Python "
                "con un ejemplo sencillo."
            )
        }
    ]

    print("\nConsultando Ollama...\n")

    try:
        response = provider.generate(messages)
        print("Asistente:\n")
        print(response)

    except RuntimeError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
