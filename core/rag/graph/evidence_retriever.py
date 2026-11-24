
"""Recuperación de evidencia documental para GraphRAG de LAIA."""

import json
import re
import unicodedata
from pathlib import Path

from core.rag.graph.graph_retriever import GraphRetriever


ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = ROOT / "knowledge" / "index" / "chunks.json"


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )


def article_markers(text):
    """Detecta encabezados como ARTÍCULO 1º o ARTÍCULO 2."""
    pattern = r"\barticulo\s+(?:n[oº°]\.?\s*)?([0-9]+)\s*[º°.]?"
    return set(re.findall(pattern, normalize(text)))


class EvidenceRetriever:
    """Localiza fragmentos originales vinculados a hechos del grafo."""

    def __init__(self, chunks=None, graph_retriever=None):
        self.graph_retriever = (
            graph_retriever
            if graph_retriever is not None
            else GraphRetriever()
        )

        if chunks is None:
            data = json.loads(
                INDEX_PATH.read_text(encoding="utf-8")
            )
            chunks = data["chunks"]

        self.chunks = chunks

    def search(self, question, scope="pregrado"):
        graph_result = self.graph_retriever.search(
            question, scope=scope
        )

        result = {
            "question": question,
            "scope": scope,
            "status": graph_result["status"],
            "facts": graph_result["facts"],
            "evidence": [],
            "missing_articles": [],
        }

        if graph_result["status"] != "ok":
            return result

        # Agrupar artículos requeridos por documento.
        requirements = {}

        for fact in graph_result["facts"]:
            filename = fact["source"]
            article = str(fact["article"])

            requirements.setdefault(filename, set()).add(
                article
            )

        evidence = []
        missing = []

        for filename, articles in requirements.items():
            document_chunks = [
                chunk for chunk in self.chunks
                if chunk.get("filename") == filename
            ]

            # El índice conserva el orden original de fragmentación.
            for article in sorted(articles):
                starts = [
                    i for i, chunk in enumerate(document_chunks)
                    if article in article_markers(
                        chunk.get("text", "")
                    )
                ]

                if not starts:
                    missing.append({
                        "source": filename,
                        "article": article,
                        "reason": "Encabezado no localizado",
                    })
                    continue

                # Recuperamos el comienzo del artículo y un
                # máximo de cuatro fragmentos posteriores.
                # Incluimos uno anterior por si el texto
                # empieza a mitad de un fragmento.
                start = starts[0]
                first = max(0, start - 1)
                last = min(len(document_chunks), start + 5)

                for chunk in document_chunks[first:last]:
                    evidence.append({
                        "id": chunk["id"],
                        "document_id": chunk["document_id"],
                        "filename": chunk["filename"],
                        "page": chunk["page"],
                        "text": chunk["text"],
                        "article": article,
                        "requires_review": chunk.get(
                            "requires_review", False
                        ),
                    })

        # Evitar fragmentos duplicados cuando dos artículos
        # comparten una misma ventana de recuperación.
        unique = {}
        for chunk in evidence:
            unique.setdefault(chunk["id"], chunk)

        result["evidence"] = list(unique.values())
        result["missing_articles"] = missing

        if not result["evidence"]:
            result["status"] = "no_evidence"
        elif missing:
            result["status"] = "partial_evidence"

        return result


if __name__ == "__main__":
    retriever = EvidenceRetriever()

    question = "¿Qué debo hacer para graduarme de pregrado?"
    result = retriever.search(question)

    print("PREGUNTA:", question)
    print("ESTADO:", result["status"])
    print("RELACIONES:", len(result["facts"]))
    print("FRAGMENTOS:", len(result["evidence"]))

    for chunk in result["evidence"]:
        print("\n" + "=" * 60)
        print("FUENTE:", chunk["filename"])
        print("PÁGINA:", chunk["page"])
        print("ID:", chunk["id"])
        print("TEXTO:")
        print(chunk["text"][:650])

    if result["missing_articles"]:
        print("\nARTÍCULOS NO LOCALIZADOS:")
        print(result["missing_articles"])
