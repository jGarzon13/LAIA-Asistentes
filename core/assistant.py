
import json
from pathlib import Path

from core.models.base import ModelProvider


class Assistant:
    def __init__(
        self,
        assistant_path: str,
        provider: ModelProvider
    ):
        self.path = Path(assistant_path)
        self.provider = provider

        with open(
            self.path / "config.json",
            encoding="utf-8"
        ) as file:
            self.config = json.load(file)

        with open(
            self.path / "prompt.md",
            encoding="utf-8"
        ) as file:
            self.system_prompt = file.read()

        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

    @property
    def name(self):
        return self.config["name"]

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()

        if not user_message:
            raise ValueError("El mensaje no puede estar vacío.")

        conversation = self.messages + [
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = self.provider.generate(conversation)

        self.messages.extend([
            {
                "role": "user",
                "content": user_message
            },
            {
                "role": "assistant",
                "content": response
            }
        ])

        
        self.messages = (
            self.messages[:1] + self.messages[-4:]
        )

        return response

    def reset(self):
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]
