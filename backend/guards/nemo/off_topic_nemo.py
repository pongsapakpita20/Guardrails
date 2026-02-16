"""
NeMo Guardrails — Off-Topic Detection Guard
Uses LLM-based topic classification with NeMo-style Colang flow.
"""
from typing import Tuple
from backend.ollama_service import ollama_service

class OffTopicGuard:
    def check(self, text: str, model: str) -> Tuple[bool, str]:
        prompt = f"""# NeMo Topic Rail
You are a content filter for a State Railway of Thailand chatbot.
Classify the following user message as either ON_TOPIC or OFF_TOPIC.

ON_TOPIC includes: trains, tickets, stations, schedules, travel by rail, greetings.
OFF_TOPIC includes: politics, sports, cooking, entertainment, unrelated subjects.

User message: "{text}"

Classification (answer ON_TOPIC or OFF_TOPIC only):"""

        messages = [{"role": "user", "content": prompt}]
        response = ""
        try:
            for chunk in ollama_service.chat_stream(model, messages):
                response += chunk
        except Exception as e:
            return True, f"NeMo off-topic check failed (skipped): {str(e)}"

        if "OFF_TOPIC" in response.upper():
            return False, "NeMo Rail: Off-topic detected"
        return True, "NeMo Rail: Topic relevant"

off_topic_guard = OffTopicGuard()
