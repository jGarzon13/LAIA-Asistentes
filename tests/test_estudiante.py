
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
            "Asistente Estudiante",
            self.assistant.system_prompt
        )

    def test_chat(self):
        response = self.assistant.chat(
            "Explícame qué es una variable."
        )

        self.assertEqual(
            response,
            "Respuesta educativa simulada."
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
        self.assistant.chat("Explicación para estudiantes")

        self.assertEqual(
            docente.messages[1]["content"],
            "Actividad para docentes"
        )
        self.assertEqual(
            self.assistant.messages[1]["content"],
            "Explicación para estudiantes"
        )


if __name__ == "__main__":
    unittest.main()
