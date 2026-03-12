import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_fallback_message(lead, message_type):
    name = lead.name.split()[0] if getattr(lead, "name", None) else "there"
    sport = getattr(lead, "sport", None) or "training"
    templates = {
        "welcome": (
            f"Hi {name}! Thanks for your interest in {sport} at Elite Sports Academy. "
            "We'd love to invite you for a free trial this Saturday at 10am. Just reply YES to confirm. - Coach Alex"
        ),
        "followup1": (
            f"Hi {name}, just checking in! Still interested in our {sport} program? "
            "We have free trials this Saturday at 10am. Let me know. - Coach Alex"
        ),
        "followup2": (
            f"Hi {name}, last chance for this Saturday's free trial. "
            "If this week doesn't work, reply and we can look at next week instead. - Coach Alex"
        ),
        "objection_handling": (
            f"Hi {name}, thanks for sharing that. I'm happy to help with any questions about our {sport} program "
            "and find an option that fits your family. - Coach Alex"
        ),
    }
    return templates.get(message_type, templates["welcome"])


def call_model(instructions, prompt, max_output_tokens=180):
    client = get_client()
    if not client:
        raise RuntimeError("Missing OPENAI_API_KEY")

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )
    return (response.output_text or "").strip()


def generate_personalized_message(lead, message_type="welcome"):
    name = lead.name.split()[0] if getattr(lead, "name", None) else "there"
    sport = getattr(lead, "sport", None) or "sports"
    age = getattr(lead, "age", None) or "school-age"
    goal = getattr(lead, "goal", None) or "improve their skills"
    message = getattr(lead, "message", None) or "interested in training"

    prompts = {
        "welcome": f"""
Write a warm, friendly welcome message to a parent.

Parent name: {name}
Athlete age: {age}
Sport: {sport}
Their goal: {goal}
Their original message: "{message}"

Write a short personal message, maximum 3 sentences, that:
1. Thanks them for reaching out
2. Shows you read their message
3. Invites them for a free trial this Saturday at 10am

Sound human, warm, and helpful. Sign with "- Coach Alex".
""",
        "followup1": f"""
Write a gentle follow-up message to a parent who has not replied yet.

Parent name: {name}
Athlete age: {age}
Sport: {sport}
Their goal: {goal}

Maximum 2 sentences. Mention their specific situation and ask if they have questions.
Sign with "- Coach Alex".
""",
        "followup2": f"""
Write a final reminder message to a parent.

Parent name: {name}
Sport: {sport}

Maximum 2 sentences. Mention this is the last chance for this week's free trial
and invite them to reply if next week works better.
Sign with "- Coach Alex".
""",
        "objection_handling": f"""
Write an empathetic response to a parent concern.

Parent name: {name}
Their concern: "{message}"

Acknowledge their concern, offer helpful information, and keep the conversation open.
Sign with "- Coach Alex".
""",
    }

    try:
        return call_model(
            "You are Coach Alex, a friendly and helpful youth sports coach writing warm, personal messages to parents.",
            prompts.get(message_type, prompts["welcome"]),
        )
    except Exception as exc:
        print(f"Error calling OpenAI for message generation: {exc}")
        return get_fallback_message(lead, message_type)


def analyze_sentiment(message):
    try:
        result = call_model(
            "You analyze message sentiment. Return only POSITIVE, NEUTRAL, or NEGATIVE.",
            f'Analyze the sentiment of this message:\n"{message}"',
            max_output_tokens=16,
        ).upper()
        if result not in {"POSITIVE", "NEUTRAL", "NEGATIVE"}:
            return "NEUTRAL"
        return result
    except Exception as exc:
        print(f"Error analyzing sentiment: {exc}")
        lowered = (message or "").lower()
        if any(word in lowered for word in ["yes", "great", "love", "interested"]):
            return "POSITIVE"
        if any(word in lowered for word in ["stop", "not interested", "no thanks", "angry"]):
            return "NEGATIVE"
        return "NEUTRAL"


def extract_action_items(message):
    try:
        result = call_model(
            "Extract action items from messages. Be concise. If none, return 'No action items'.",
            f'Extract action items from this parent message:\n"{message}"',
            max_output_tokens=80,
        )
        return result or "No action items"
    except Exception as exc:
        print(f"Error extracting action items: {exc}")
        lowered = (message or "").lower()
        items = []
        if "call me" in lowered:
            items.append("Call me")
        if "price" in lowered or "pricing" in lowered:
            items.append("Send pricing")
        if "trial" in lowered or "schedule" in lowered:
            items.append("Schedule trial")
        return ", ".join(items) if items else "No action items"


def sanitize_for_voice(text):
    return re.sub(r"[^\w\s.,!?-]", "", text or "")
