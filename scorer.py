# Simple lead scoring based on keywords in the message


def score_lead(lead_data):
    """
    Score a lead from 0-100 and return score and category.
    Hot: 70-100, Warm: 40-69, Cold: 0-39
    """
    message = lead_data.get("message", "").lower()
    name = lead_data.get("name", "").lower()

    score = 50

    high_intent_words = [
        "urgent",
        "immediately",
        "asap",
        "right away",
        "desperate",
        "serious",
        "committed",
        "ready to start",
        "sign up",
        "enroll",
        "when can we start",
        "how soon",
        "need now",
    ]

    medium_intent_words = [
        "interested",
        "looking for",
        "considering",
        "maybe",
        "thinking about",
        "exploring",
        "curious",
        "options",
        "want to learn",
        "tell me more",
        "information",
    ]

    low_intent_words = [
        "just browsing",
        "researching",
        "comparing",
        "not sure yet",
        "future reference",
        "later",
        "someday",
        "eventually",
        "price only",
        "cost",
        "cheap",
        "discount",
    ]

    sport_keywords = [
        "soccer",
        "football",
        "basketball",
        "tennis",
        "baseball",
        "swimming",
        "golf",
        "volleyball",
        "hockey",
        "lacrosse",
    ]

    for word in high_intent_words:
        if word in message:
            score += 10
            print(f"  +10 for '{word}'")

    for word in medium_intent_words:
        if word in message:
            score += 5
            print(f"  +5 for '{word}'")

    for word in low_intent_words:
        if word in message:
            score -= 10
            print(f"  -10 for '{word}'")

    for word in sport_keywords:
        if word in message:
            score += 15
            print(f"  +15 for mentioning sport: '{word}'")
            break

    import re

    age_match = re.search(r"(\d+)[-\s]?year[-\s]?old", message)
    if age_match:
        age = int(age_match.group(1))
        if 8 <= age <= 18:
            score += 10
            print(f"  +10 for target age: {age}")

    score = max(0, min(100, score))

    if score >= 70:
        category = "HOT"
    elif score >= 40:
        category = "WARM"
    else:
        category = "COLD"

    return {
        "score": score,
        "category": category,
        "message_analyzed": message[:50] + "..." if len(message) > 50 else message,
    }


if __name__ == "__main__":
    test_leads = [
        {"name": "John", "message": "My son is 14 and wants soccer training urgently"},
        {"name": "Sarah", "message": "Just browsing options for summer camps"},
        {"name": "Mike", "message": "Need tennis coach immediately for 12 year old"},
        {"name": "Lisa", "message": "What are your prices? Maybe later"},
    ]

    for lead in test_leads:
        result = score_lead(lead)
        print(f"\nLead: {lead['name']}")
        print(f"Message: {lead['message']}")
        print(f"Score: {result['score']} - {result['category']}")
