
from core.rag.rag_service import RAGService


SCOPE_OPTIONS = {
    "1": "pregrado",
    "2": "posgrado",
    "3": "general"
}


def select_scope():
    while True:
        print("\nSelecciona el ámbito documental:")
        print("1. Pregrado")
        print("2. Posgrado")
        print("3. General")
        print("0. Volver")

        option = input("\nOpción: ").strip()

        if option == "0":
            return None

        if option in SCOPE_OPTIONS:
            return SCOPE_OPTIONS[option]

        print("Selecciona una opción válida.")


def run_rag_console(provider, assistant_type):
    if assistant_type not in {
        "estudiante", "docente"
    }:
        raise ValueError("Tipo de asistente no válido.")

    scope = select_scope()

    if scope is None:
        return

    rag = RAGService(provider=provider)

    title = (
        "Asistente Estudiante"
        if assistant_type == "estudiante"
        else "Asistente Docente - Consulta documental"
    )

    print(f"\n--- LAIA - {title} ---")
    print(f"Ámbito actual: {scope}")
    print("Comandos: /salir, /back, /reiniciar, /ambito")
    print(
        "Aviso: las normas y páginas OCR pueden "
        "requerir verificación institucional."
    )

    while True:
        question = input("\nTú: ").strip()

        if question.lower() in {
            "/salir", "/exit", "/back"
        }:
            return

        if question.lower() == "/ambito":
            new_scope = select_scope()

            if new_scope is not None:
                scope = new_scope
                print(f"Ámbito actualizado: {scope}")

            continue

        if question.lower() == "/reiniciar":
            print(
                "Consulta reiniciada. "
                "Cada pregunta recuperará fuentes nuevas."
            )
            continue

        if not question:
            continue

        print("\nConsultando documentos...")

        try:
            result = rag.ask(
                question=question,
                scope=scope,
                assistant_type=assistant_type
            )
        except Exception as exc:
            print(
                f"\nError al consultar RAG: "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        print(f"\nLAIA - {title}:")
        print(result["answer"])

        if result.get("sources"):
            print("\nFuentes recuperadas:")

            for source in result["sources"]:
                page = source.get("page")
                page_label = (
                    str(page)
                    if page is not None
                    else "No disponible"
                )

                print(
                    f"- [{source['reference']}] "
                    f"{source['filename']}, "
                    f"página {page_label}, "
                    f"relevancia {source['score']:.4f}"
                )

        if result.get("warning"):
            print("\nAviso:", result["warning"])
