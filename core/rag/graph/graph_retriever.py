
"""Recuperador experimental basado en el grafo académico de LAIA."""

import re
import unicodedata

import networkx as nx

from core.rag.graph.knowledge_graph import build_academic_graph


def normalize(text: str) -> str:
    """Normaliza texto para comparar consultas en español."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", text).strip()


class GraphRetriever:
    """Recupera hechos vinculados en un grafo académico."""

    def __init__(self, graph=None):
        self.graph = (
            graph if graph is not None
            else build_academic_graph()
        )

    def _detect_topics(self, question: str) -> set[str]:
        question = normalize(question)
        topics = set()

        graduation_terms = (
            "gradu", "titulo", "titulacion",
            "grado", "egresar"
        )

        if any(term in question for term in graduation_terms):
            topics.add("graduation")

        if any(term in question for term in (
            "saber pro", "percentil", "prueba de estado"
        )):
            topics.add("saber_pro")

        if any(term in question for term in (
            "vigencia", "desde cuando", "cuando aplica",
            "entra en vigor", "2027"
        )):
            topics.add("temporal")

        return topics

    def search(self, question: str, scope: str = "pregrado") -> dict:
        """Devuelve relaciones relevantes y su procedencia.

        Solo existe un grafo curado de pregrado en esta etapa.
        No se generan respuestas mediante un LLM.
        """
        if scope != "pregrado":
            return {
                "question": question,
                "scope": scope,
                "facts": [],
                "status": "unsupported_scope",
            }

        topics = self._detect_topics(question)

        if not topics:
            return {
                "question": question,
                "scope": scope,
                "facts": [],
                "status": "no_match",
            }

        selected_nodes = set()

        if "graduation" in topics:
            selected_nodes.update({
                "art_1", "art_2", "creditos",
                "requisitos_programa", "saber_pro",
                "percentil_40", "repetir_prueba",
                "ruta_fortalecimiento",
                "aplicacion_2027"
            })

        if "saber_pro" in topics:
            selected_nodes.update({
                "saber_pro", "percentil_40",
                "repetir_prueba", "ruta_fortalecimiento",
                "art_1", "art_2", "aplicacion_2027"
            })

        if "temporal" in topics:
            selected_nodes.update({
                "art_2", "aplicacion_2027"
            })

        facts = []

        for origin, destination, attributes in self.graph.edges(data=True):
            if (
                origin not in selected_nodes
                or destination not in selected_nodes
            ):
                continue

            facts.append({
                "origin": self.graph.nodes[origin]["name"],
                "relation": attributes["relation"],
                "destination": self.graph.nodes[destination]["name"],
                "article": attributes["article"],
                "page": attributes["page"],
                "source": attributes["source"],
            })

        return {
            "question": question,
            "scope": scope,
            "topics": sorted(topics),
            "facts": facts,
            "status": "ok" if facts else "no_match",
        }


if __name__ == "__main__":
    retriever = GraphRetriever()

    questions = [
        "¿Qué debo hacer para graduarme de pregrado?",
        "¿Qué pasa si no alcanzo el percentil 40 en Saber Pro?",
        "¿Desde cuándo aplica la Resolución 6865?",
        "¿Qué dice el reglamento de posgrado sobre evaluaciones?"
    ]

    for question in questions:
        scope = (
            "posgrado"
            if "posgrado" in normalize(question)
            else "pregrado"
        )

        result = retriever.search(question, scope=scope)

        print("\n" + "=" * 65)
        print("PREGUNTA:", question)
        print("ESTADO:", result["status"])
        print("RELACIONES:", len(result["facts"]))

        for fact in result["facts"]:
            print(
                f"- {fact['origin']} "
                f"--{fact['relation']}--> "
                f"{fact['destination']}"
            )
            print(
                f"  Fuente: {fact['source']}, "
                f"artículo {fact['article']}"
            )
