
import json
import tempfile
import unittest
from pathlib import Path

from core.rag.rag_service import RAGService

from core.rag.rag_service import expand_query


class FakeProvider:
    def __init__(self):
        self.calls = []

    def generate(self, messages):
        self.calls.append(messages)
        return "Respuesta de prueba [FUENTE 1]."


class TestRAGService(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)

        self.index_file = root / "chunks.json"
        self.metadata_file = root / "metadata.json"

        self.index_file.write_text(
            json.dumps({
                "documents": [{
                    "id": "doc001",
                    "filename": "reglamento.pdf",
                    "source_path": "reglamento.pdf"
                }],
                "chunks": [{
                    "id": "doc001-C0001",
                    "document_id": "doc001",
                    "filename": "reglamento.pdf",
                    "page": 5,
                    "text": (
                        "Los estudiantes deben presentar "
                        "evaluaciones académicas."
                    ),
                    "extraction_method": "text",
                    "requires_review": False
                }]
            }),
            encoding="utf-8"
        )

        self.metadata_file.write_text(
            json.dumps({
                "documents": {
                    "reglamento.pdf": {
                        "document_id": "doc001",
                        "effective": {
                            "scope": "posgrado",
                            "validity": "no_verificada"
                        }
                    }
                }
            }),
            encoding="utf-8"
        )

        self.provider = FakeProvider()

        self.rag = RAGService(
            provider=self.provider,
            index_file=self.index_file,
            metadata_file=self.metadata_file
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_grounded_answer_calls_provider(self):
        result = self.rag.ask(
            "evaluaciones académicas",
            "posgrado"
        )

        self.assertEqual(len(self.provider.calls), 1)
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(
            result["sources"][0]["page"], 5
        )

    def test_wrong_scope_blocks_model(self):
        result = self.rag.ask(
            "evaluaciones académicas",
            "pregrado"
        )

        self.assertEqual(self.provider.calls, [])
        self.assertEqual(result["sources"], [])

    def test_no_match_blocks_model(self):
        result = self.rag.ask(
            "astronomía planetaria",
            "posgrado"
        )

        self.assertEqual(self.provider.calls, [])
        self.assertEqual(result["sources"], [])

    def test_empty_question_blocks_model(self):
        result = self.rag.ask("", "posgrado")

        self.assertEqual(self.provider.calls, [])
        self.assertEqual(result["sources"], [])


    def test_colloquial_graduation_expansion(self):
        expanded = expand_query(
            "¿Qué debo hacer para graduarme?"
        )

        self.assertIn("requisitos para grado", expanded)
        self.assertIn("obtener titulo academico", expanded)

    def test_unrelated_query_not_expanded(self):
        question = "¿Cuáles son mis deberes?"

        self.assertEqual(
            expand_query(question),
            question
        )


    def test_student_rag_role(self):
        result = self.rag.ask(
            "evaluaciones académicas",
            "posgrado",
            assistant_type="estudiante"
        )

        self.assertEqual(len(self.provider.calls), 1)
        self.assertTrue(result["sources"])

        messages = self.provider.calls[0]

        self.assertIn(
            "Asistente Estudiante",
            messages[0]["content"]
        )

    def test_teacher_rag_role(self):
        result = self.rag.ask(
            "evaluaciones académicas",
            "posgrado",
            assistant_type="docente"
        )

        self.assertEqual(len(self.provider.calls), 1)
        self.assertTrue(result["sources"])

        messages = self.provider.calls[0]

        self.assertIn(
            "Asistente Docente",
            messages[0]["content"]
        )

    def test_invalid_rag_role(self):
        with self.assertRaises(ValueError):
            self.rag.ask(
                "evaluaciones académicas",
                "posgrado",
                assistant_type="administrador"
            )

        self.assertEqual(
            self.provider.calls, []
        )



if __name__ == "__main__":
    unittest.main()
