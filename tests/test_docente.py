
import unittest
from pathlib import Path

from core.assistant import Assistant
from core.models.base import ModelProvider


ROOT = Path(__file__).resolve().parents[1]


class FakeProvider(ModelProvider):
    def __init__(self):
        self.last_messages = []

    def generate(self, messages):
        self.last_messages = [
            message.copy() for message in messages
        ]
        return "Respuesta simulada del asistente."


class TestAssistantDocente(unittest.TestCase):

    def setUp(self):
        self.provider = FakeProvider()
        self.assistant = Assistant(
            ROOT / "assistants" / "docente",
            self.provider
        )

    def test_load_config(self):
        self.assertEqual(
            self.assistant.config["id"],
            "laia-docente"
        )
        self.assertEqual(
            self.assistant.config["version"],
            "0.1.0"
        )

    def test_load_prompt(self):
        self.assertIn(
            "Asistente Docente",
            self.assistant.system_prompt
        )

    def test_chat(self):
        response = self.assistant.chat(
            "Diseña una actividad de aprendizaje."
        )

        self.assertEqual(
            response,
            "Respuesta simulada del asistente."
        )
        self.assertEqual(
            self.provider.last_messages[-1]["role"],
            "user"
        )

    def test_empty_message(self):
        with self.assertRaises(ValueError):
            self.assistant.chat("   ")

    def test_reset(self):
        self.assistant.chat("Primera consulta")
        self.assistant.reset()

        self.assertEqual(len(self.assistant.messages), 1)
        self.assertEqual(
            self.assistant.messages[0]["role"],
            "system"
        )

    def test_history_limit(self):
        for index in range(5):
            self.assistant.chat(f"Consulta {index}")

        self.assertLessEqual(
            len(self.assistant.messages),
            5
        )

        self.assertEqual(
            self.assistant.messages[0]["role"],
            "system"
        )


if __name__ == "__main__":
    unittest.main()
