
from pathlib import Path

from core.assistant import Assistant
from core.models.ollama_provider import OllamaProvider
from core.models.groq_provider import GroqProvider
from core.rag.console import run_rag_console


BASE_DIR = Path(__file__).resolve().parent


def select_provider():
    while True:
        print("\nSelecciona el proveedor de IA:")
        print("1. Ollama - Gemma 3 1B (local)")
        print("2. Groq - Qwen3.8-27B (API)")

        option = input("\nOpción: ").strip()

        if option == "1":
            return OllamaProvider(model="gemma3:1b")

        if option == "2":
            try:
                return GroqProvider(
                    model="qwen/qwen3.8-27b"
                )
            except RuntimeError as exc:
                print(f"Error al configurar Groq: {exc}")
                continue

        print("Opción no válida.")


def run_chat(assistant: Assistant):
    print(f"\n--- {assistant.name} ---")
    print("Comandos: /salir, /exit, /back → volver al menú.")
    print("Escribe /reiniciar para borrar el contexto.\n")

    while True:
        message = input("Tú: ").strip()

        if message.lower() in (
            "/salir", "/exit", "/back"
        ):
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

            print(
                f"{assistant.name}:\n"
                f"{response}\n"
            )

        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}\n")


def run_teacher_menu(assistant, provider):
    while True:
        print("\n" + "=" * 50)
        print("LAIA - Asistente Docente")
        print("=" * 50)
        print("1. Asistencia pedagógica")
        print("2. Consulta documental con RAG")
        print("0. Volver al menú principal")

        option = input("\nSelecciona una opción: ").strip()

        if option == "0":
            return

        if option == "1":
            # Mantiene el funcionamiento original.
            run_chat(assistant)

        elif option == "2":
            # Nuevo modo documental para docentes.
            run_rag_console(
                provider=provider,
                assistant_type="docente"
            )

        else:
            print("Opción no válida.")


def main():
    provider = select_provider()

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

        option = input(
            "\nSelecciona una opción: "
        ).strip()

        if option == "0":
            print("Finalizando LAIA...")
            break

        elif option == "1":
            run_teacher_menu(
                assistant=assistants["1"],
                provider=provider
            )

        elif option == "2":
            # El estudiante consulta la base documental.
            run_rag_console(
                provider=provider,
                assistant_type="estudiante"
            )

        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
