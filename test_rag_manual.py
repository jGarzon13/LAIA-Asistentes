
import os

from core.models.groq_provider import GroqProvider
from core.rag.rag_service import RAGService


def main():
    if not os.getenv("GROQ_API_KEY"):
        print("Falta configurar GROQ_API_KEY.")
        return

    provider = GroqProvider(
        model="qwen/qwen3.8-27b"
    )

    rag = RAGService(provider)

    print("=" * 55)
    print("LAIA - Primera prueba RAG con Groq")
    print("=" * 55)

    while True:
        scope = input(
            "\nÁmbito (pregrado/posgrado/general, "
            "/salir): "
        ).strip().lower()

        if scope == "/salir":
            break

        question = input("\nTu pregunta: ").strip()

        if question == "/salir":
            break

        print("\nConsultando documentos...")

        result = rag.ask(question, scope)

        print("\nLAIA:")
        print(result["answer"])

        if result["sources"]:
            print("\nFuentes recuperadas:")

            for source in result["sources"]:
                print(
                    f"- [{source['reference']}] "
                    f"{source['filename']}, "
                    f"página {source['page']}, "
                    f"score {source['score']:.4f}"
                )

        if result.get("warning"):
            print("\nAviso:", result["warning"])


if __name__ == "__main__":
    main()
