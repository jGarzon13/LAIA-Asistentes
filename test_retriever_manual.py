
from core.rag.retriever import DocumentRetriever


def main():
    retriever = DocumentRetriever()

    print("=" * 50)
    print("LAIA - Prueba de recuperación documental")
    print("=" * 50)

    while True:
        query = input("\nPregunta (/salir): ").strip()

        if query.lower() in {"/salir", "/exit"}:
            break

        results = retriever.search(
            query,
            top_k=3,
            filename="Reglamento-posgrados-Res-CA-6605.pdf"
        )

        if not results:
            print("No se encontraron coincidencias.")
            continue

        for number, result in enumerate(results, start=1):
            print(f"\n--- Resultado {number} ---")
            print(f"Documento: {result['filename']}")
            print(f"Página: {result['page']}")
            print(f"Relevancia: {result['score']:.4f}")
            print(f"Términos: {result['matched_terms']}")
            print(f"Método: {result['extraction_method']}")
            print(f"Revisión OCR: {result['requires_review']}")
            print(f"\n{result['text'][:650]}...")


if __name__ == "__main__":
    main()
