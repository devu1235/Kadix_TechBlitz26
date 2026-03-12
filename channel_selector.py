from ai_personalizer import generate_personalized_message, sanitize_for_voice


def select_best_channel(lead):
    score = getattr(lead, "score", 50) or 50
    age = getattr(lead, "age", None)
    urgency = getattr(lead, "urgency", "low") or "low"

    channel = "sms"
    if score >= 80:
        channel = "voice" if urgency == "high" else "whatsapp"
    elif score >= 50:
        channel = "whatsapp"

    if age and age < 16 and channel == "voice":
        channel = "whatsapp"

    return channel


def get_channel_message(lead, channel, message_type="welcome"):
    ai_message = generate_personalized_message(lead, message_type)
    if channel == "sms" and len(ai_message) > 160:
        return ai_message[:157] + "..."
    if channel == "voice":
        return sanitize_for_voice(ai_message)
    return ai_message
