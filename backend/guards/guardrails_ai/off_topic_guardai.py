"""
Guardrails AI — Off-Topic Detection Guard
Uses the main chat model to classify if the query is SRT-related.
"""
from typing import Tuple
from backend.ollama_service import ollama_service

class OffTopicGuard:
    def check(self, text: str, model: str) -> Tuple[bool, str]:
        prompt = f"""You are a topic classifier for the State Railway of Thailand (SRT).
Determine if the user's query is related to:
1. Trains, Schedules, Tickets, Railway stations
2. Travel in Thailand by train
3. General greetings or politeness
4. Questions about the bot itself

User Query: "{text}"

Is this query relevant to SRT or general assistance? Answer only YES or NO."""

        messages = [{"role": "user", "content": prompt}]
        response = ""
        try:
            for chunk in ollama_service.chat_stream(model, messages):
                response += chunk
        except Exception as e:
            return True, f"Off-topic check failed (skipped): {str(e)}"

        if "N" in response.upper() and "Y" not in response.upper():
            return False, "Off-topic detected: Query is not related to SRT/Travel."
        return True, "Topic relevant"

off_topic_guard = OffTopicGuard()
