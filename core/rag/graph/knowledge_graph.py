
import networkx as nx


SOURCE = "res-ca-6865-requisitos-titulo-programas-pregrado-profesional.pdf"


def build_academic_graph():
    """Grafo académico experimental basado en la Resolución 6865."""

    graph = nx.DiGraph()

    nodes = {
        "res_6865": (
            "documento",
            "Resolución CA 6865 de 2026"
        ),
        "art_1": (
            "articulo",
            "Artículo 1 - Requisitos para grado"
        ),
        "art_2": (
            "articulo",
            "Artículo 2 - Aplicación temporal"
        ),
        "creditos": (
            "requisito",
            "Aprobar créditos del plan de estudios"
        ),
        "requisitos_programa": (
            "requisito",
            "Cumplir requisitos específicos del programa"
        ),
        "saber_pro": (
            "requisito",
            "Presentar Saber Pro"
        ),
        "percentil_40": (
            "condicion",
            "Alcanzar el percentil mínimo 40"
        ),
        "repetir_prueba": (
            "alternativa",
            "Presentar nuevamente Saber Pro"
        ),
        "ruta_fortalecimiento": (
            "alternativa",
            "Completar la Ruta de Fortalecimiento y pagar"
        ),
        "aplicacion_2027": (
            "fecha_aplicacion",
            "Primer periodo académico de 2027"
        )
    }

    for node_id, (node_type, name) in nodes.items():
        graph.add_node(
            node_id,
            type=node_type,
            name=name,
            scope="pregrado",
            source=SOURCE
        )

    def connect(origin, destination, relation, article):
        graph.add_edge(
            origin,
            destination,
            relation=relation,
            article=article,
            page=1,
            source=SOURCE
        )

    connect("res_6865", "art_1", "contiene", "1")
    connect("res_6865", "art_2", "contiene", "2")

    connect("art_1", "creditos", "establece", "1")
    connect(
        "art_1", "requisitos_programa",
        "establece", "1"
    )
    connect("art_1", "saber_pro", "establece", "1")
    connect(
        "saber_pro", "percentil_40",
        "exige", "1"
    )
    connect(
        "percentil_40", "repetir_prueba",
        "permite_alternativa", "1"
    )
    connect(
        "percentil_40", "ruta_fortalecimiento",
        "permite_alternativa", "1"
    )
    connect(
        "art_2", "aplicacion_2027",
        "determina_aplicacion", "2"
    )

    return graph


def get_document_facts(graph, document_id):
    """Recorre el documento y sus relaciones alcanzables."""

    if document_id not in graph:
        raise ValueError("Documento inexistente en el grafo.")

    facts = []

    for origin, destination in nx.bfs_edges(
        graph, document_id
    ):
        edge = graph.edges[origin, destination]

        facts.append({
            "from": graph.nodes[origin]["name"],
            "relation": edge["relation"],
            "to": graph.nodes[destination]["name"],
            "article": edge["article"],
            "page": edge["page"],
            "source": edge["source"]
        })

    return facts


if __name__ == "__main__":
    graph = build_academic_graph()

    print("LAIA - Grafo académico experimental")
    print("Nodos:", graph.number_of_nodes())
    print("Relaciones:", graph.number_of_edges())

    print("\nConocimiento vinculado:")

    for fact in get_document_facts(graph, "res_6865"):
        print(
            f"- {fact['from']} "
            f"--{fact['relation']}--> "
            f"{fact['to']} "
            f"(artículo {fact['article']})"
        )
