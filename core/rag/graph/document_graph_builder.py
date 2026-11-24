
"""Constructor automático del grafo documental de LAIA."""

import json
from collections import Counter
from pathlib import Path

import networkx as nx


ROOT = Path(__file__).resolve().parents[3]

INDEX_FILE = ROOT / "knowledge/index/chunks.json"
OUTPUT_FILE = ROOT / "knowledge/graph/document_graph.json"

EXCLUDED_FILES = {
    "procedimiento_academico_ficticio.txt",
}


def build_document_graph(chunks):
    """Construye relaciones estructurales del corpus."""

    graph = nx.DiGraph()
    included = []

    for chunk in chunks:
        filename = chunk["filename"]

        if filename.casefold() in EXCLUDED_FILES:
            continue

        included.append(chunk)

        document_id = f"doc:{chunk['document_id']}"
        page_id = f"page:{chunk['document_id']}:{chunk['page']}"
        chunk_id = f"chunk:{chunk['id']}"

        graph.add_node(
            document_id,
            type="document",
            filename=filename,
        )

        graph.add_node(
            page_id,
            type="page",
            filename=filename,
            page=chunk["page"],
        )

        graph.add_node(
            chunk_id,
            type="chunk",
            filename=filename,
            page=chunk["page"],
            chunk_id=chunk["id"],
            text=chunk["text"],
            requires_review=bool(
                chunk.get("requires_review", False)
            ),
        )

        graph.add_edge(
            document_id,
            page_id,
            relation="HAS_PAGE",
        )

        graph.add_edge(
            page_id,
            chunk_id,
            relation="HAS_CHUNK",
        )

    # Enlazar fragmentos consecutivos del mismo documento,
    # respetando el orden que tiene el índice original.
    previous_by_document = {}

    for chunk in included:
        document_key = chunk["document_id"]
        current = f"chunk:{chunk['id']}"

        previous = previous_by_document.get(document_key)

        if previous is not None:
            graph.add_edge(
                previous,
                current,
                relation="NEXT_CHUNK",
            )

        previous_by_document[document_key] = current

    return graph


def save_graph(graph, output_path=OUTPUT_FILE):
    """Guarda un JSON independiente de NetworkX."""

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    data = {
        "schema_version": 1,
        "graph_type": "document_structure",
        "nodes": [
            {"id": node_id, **attributes}
            for node_id, attributes in graph.nodes(data=True)
        ],
        "edges": [
            {
                "source": origin,
                "target": destination,
                **attributes,
            }
            for origin, destination, attributes
            in graph.edges(data=True)
        ],
    }

    temp = output_path.with_suffix(".json.tmp")

    try:
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(output_path)
    finally:
        if temp.exists():
            temp.unlink()


def main():
    data = json.loads(
        INDEX_FILE.read_text(encoding="utf-8")
    )

    graph = build_document_graph(data["chunks"])
    save_graph(graph)

    counts = Counter(
        attrs["type"]
        for _, attrs in graph.nodes(data=True)
    )

    relations = Counter(
        attrs["relation"]
        for _, _, attrs in graph.edges(data=True)
    )

    review_count = sum(
        attrs.get("requires_review", False)
        for _, attrs in graph.nodes(data=True)
        if attrs["type"] == "chunk"
    )

    print("\nLAIA - Grafo documental multidocumento")
    print("Documentos:", counts["document"])
    print("Páginas:", counts["page"])
    print("Fragmentos:", counts["chunk"])
    print("Marcados para revisión:", review_count)
    print("Total de nodos:", graph.number_of_nodes())
    print("Total de relaciones:", graph.number_of_edges())

    print("\nTIPOS DE RELACIÓN:")
    for relation, count in relations.items():
        print(f"- {relation}: {count}")

    print("\nGrafo guardado en:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
