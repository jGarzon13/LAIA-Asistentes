
from pathlib import Path

from core.assistant import Assistant
from core.models.ollama_provider import OllamaProvider


BASE_DIR = Path(__file__).resolve().parent


def run_chat(assistant: Assistant):
    print(f"\n--- {assistant.name} ---")
    print("Comandos: /salir, /exit, /back → volver al menú.")
    print("Escribe /reiniciar para borrar el contexto.\n")

    while True:
        message = input("Tú: ").strip()

        if message.lower() in( "/salir", "/exit", "break"):
            break

        if message.lower() == "/reiniciar":
            assistant.reset()
            print("Conversación reiniciada.\n")
            continue

        if not message:
            continue

        try:
            print("\nGenerando respuesta...\n")
            response = assistant.chat(message)
            print(f"{assistant.name}:\n{response}\n")

        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}\n")


def main():
    provider = OllamaProvider(model="gemma3:1b")

    assistants = {
        "1": Assistant(
            BASE_DIR / "assistants" / "docente",
            provider
        ),
        "2": Assistant(
            BASE_DIR / "assistants" / "estudiante",
            provider
        )
    }

    while True:
        print("\n" + "=" * 50)
        print("LAIA - Asistentes académicos")
        print("Universidad Autónoma de Occidente")
        print("=" * 50)
        print("1. Asistente Docente")
        print("2. Asistente Estudiante")
        print("0. Salir")

        option = input("\nSelecciona una opción: ").strip()

        if option == "0":
            print("Finalizando LAIA...")
            break

        if option in assistants:
            run_chat(assistants[option])
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
