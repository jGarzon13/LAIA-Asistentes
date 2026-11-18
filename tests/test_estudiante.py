
import unittest
from pathlib import Path

from core.assistant import Assistant
from core.models.base import ModelProvider


ROOT = Path(__file__).resolve().parents[1]


class FakeProvider(ModelProvider):
    def generate(self, messages):
        return "Respuesta educativa simulada."


class TestAssistantEstudiante(unittest.TestCase):

    def setUp(self):
        self.assistant = Assistant(
            ROOT / "assistants" / "estudiante",
            FakeProvider()
        )

    def test_load_config(self):
        self.assertEqual(
            self.assistant.config["id"],
            "laia-estudiante"
        )

    def test_load_prompt(self):
        self.assertIn(
            "Asistente de Gestión Académica",
            self.assistant.system_prompt
        )

    
    def test_chat(self):
        response = self.assistant.chat(
            "¿Cómo cancelo una asignatura en la UAO?"
        )

        self.assertIn(
            "No dispongo de información institucional verificada",
            response
        )

        self.assertEqual(
            len(self.assistant.messages),
            1
        )


    def test_independent_prompts(self):
        docente = Assistant(
            ROOT / "assistants" / "docente",
            FakeProvider()
        )

        self.assertNotEqual(
            docente.system_prompt,
            self.assistant.system_prompt
        )

    
    def test_chat_does_not_mix_assistants(self):
        docente = Assistant(
            ROOT / "assistants" / "docente",
            FakeProvider()
        )

        docente.chat("Actividad para docentes")

        response = self.assistant.chat(
            "¿Cuál es el plazo de matrícula en la UAO?"
        )

        # El docente conserva su conversación normal
        self.assertEqual(
            docente.messages[1]["content"],
            "Actividad para docentes"
        )

        # El estudiante no genera respuestas sin fuentes
        self.assertIn(
            "No dispongo de información institucional verificada",
            response
        )

        # El historial del estudiante permanece independiente
        self.assertEqual(
            len(self.assistant.messages),
            1
        )


    def test_academic_management_identity(self):
        self.assertEqual(
            self.assistant.config["version"],
            "0.2.0"
        )

        self.assertEqual(
            self.assistant.config["id"],
            "laia-estudiante"
        )

        self.assertIn(
            "Gestión Académica",
            self.assistant.name
        )

    def test_rag_configuration(self):
        knowledge = self.assistant.config["knowledge"]

        self.assertEqual(
            knowledge["type"],
            "rag"
        )

        self.assertEqual(
            knowledge["status"],
            "pending_implementation"
        )

        self.assertTrue(
            knowledge["require_sources"]
        )

    def test_document_grounding_instructions(self):
        prompt = self.assistant.system_prompt

        self.assertIn(
            "No inventes artículos",
            prompt
        )

        self.assertIn(
            "información institucional verificada",
            prompt
        )


    def test_no_model_call_without_sources(self):
        class TrackingProvider(ModelProvider):
            def __init__(self):
                self.called = False

            def generate(self, messages):
                self.called = True
                return "Respuesta que no debería generarse."

        provider = TrackingProvider()

        assistant = Assistant(
            ROOT / "assistants" / "estudiante",
            provider
        )

        response = assistant.chat(
            "¿Cuántos días tengo para solicitar un supletorio?"
        )

        self.assertFalse(provider.called)

        self.assertIn(
            "No dispongo de información institucional verificada",
            response
        )




if __name__ == "__main__":
    unittest.main()
