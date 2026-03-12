import re


def enrich_lead(lead_data):
    """
    Extract useful information from a lead message.
    """
    message = lead_data.get("message", "").lower()

    enriched = {
        "sport": None,
        "age": None,
        "position": None,
        "goal": None,
        "urgency": "low",
    }

    sports = {
        "soccer": ["soccer", "football"],
        "basketball": ["basketball", "hoops"],
        "tennis": ["tennis"],
        "baseball": ["baseball", "softball"],
        "swimming": ["swim", "swimming"],
        "golf": ["golf"],
        "volleyball": ["volleyball"],
    }

    for sport, keywords in sports.items():
        for keyword in keywords:
            if keyword in message:
                enriched["sport"] = sport
                break
        if enriched["sport"]:
            break

    age_patterns = [
        r"(\d+)[-\s]?year[-\s]?old",
        r"age[:\s](\d+)",
        r"(\d+)[-\s]?yr[-\s]?old",
        r"my[-\s]?(\d+)[-\s]?year[-\s]?old",
    ]

    for pattern in age_patterns:
        match = re.search(pattern, message)
        if match:
            enriched["age"] = int(match.group(1))
            break

    positions = {
        "forward": ["forward", "striker", "attacker"],
        "midfielder": ["midfield", "midfielder"],
        "defender": ["defender", "defense"],
        "goalkeeper": ["goalie", "goalkeeper", "keeper"],
    }

    for position, keywords in positions.items():
        for keyword in keywords:
            if keyword in message:
                enriched["position"] = position
                break
        if enriched["position"]:
            break

    goal_keywords = {
        "college": ["college", "scholarship", "university", "ncaa"],
        "competitive": ["competitive", "travel team", "select", "elite"],
        "fun": ["fun", "enjoy", "recreational", "rec"],
        "improve": ["improve", "get better", "develop", "skills"],
    }

    for goal, keywords in goal_keywords.items():
        for keyword in keywords:
            if keyword in message:
                enriched["goal"] = goal
                break
        if enriched["goal"]:
            break

    urgency_words = [
        "urgent",
        "immediately",
        "asap",
        "as soon as possible",
        "right away",
        "quick",
    ]
    for word in urgency_words:
        if word in message:
            enriched["urgency"] = "high"
            break

    return enriched


if __name__ == "__main__":
    test_messages = [
        "My 14 year old son wants soccer training, he plays forward and wants to play in college",
        "Looking for basketball for my 12 year old daughter, just for fun",
        "Urgent: Need tennis coach immediately for 16 year old",
    ]

    for msg in test_messages:
        result = enrich_lead({"message": msg})
        print(f"\nMessage: {msg}")
        print(f"Enriched: {result}")
