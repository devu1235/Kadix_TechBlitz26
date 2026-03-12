import asyncio
import os
import re
from datetime import datetime

from flask import Flask, jsonify, request
from dotenv import load_dotenv
from telegram import Bot
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import Gather, VoiceResponse

from ai_personalizer import analyze_sentiment, extract_action_items
from coaches import assign_lead_to_coach
from dashboard import create_dashboard
from database import Interaction, Lead, Session
from enricher import enrich_lead
from google_calendar import create_trial_event
from messaging import send_sms, send_whatsapp
from reports import schedule_daily_reports
from scorer import score_lead

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DEFAULT_COACH_CHAT_ID = os.getenv("DEFAULT_COACH_CHAT_ID", "")


def normalize_phone(value):
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def find_lead_by_phone(db_session, phone):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    leads = db_session.query(Lead).all()
    for lead in leads:
        if normalize_phone(lead.phone) == normalized:
            return lead
    return None


def get_public_url(path):
    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}{path}"
    return path


def notify_chat(chat_id, text):
    async def send_telegram():
        async with Bot(token=BOT_TOKEN) as bot:
            await bot.send_message(chat_id=chat_id, text=text)

    asyncio.run(send_telegram())


def notify_coach(text, coach_chat_id=None):
    target_chat = str(coach_chat_id or DEFAULT_COACH_CHAT_ID)
    notify_chat(target_chat, text)


def notify_positive_reply(lead, body):
    target = lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None
    notify_coach(
        f"Lead #{lead.id} replied positively: {body}\nAction items: {lead.action_items or 'None'}",
        target,
    )


def handle_objection(lead, body, channel):
    target = lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None
    notify_coach(
        f"Lead #{lead.id} may have an objection via {channel}: {body}\nAction items: {lead.action_items or 'None'}",
        target,
    )


def send_channel_confirmation(channel, lead, message_text):
    if channel == "sms":
        return send_sms(lead.phone, message_text)
    return send_whatsapp(lead.phone, message_text)


def process_incoming_reply(channel, from_number, body):
    print(f"Received {channel} reply from {from_number}: {body}")
    db_session = Session()
    lead = find_lead_by_phone(db_session, from_number)

    if not lead:
        db_session.close()
        return

    sentiment = analyze_sentiment(body or "")
    action_items = extract_action_items(body or "")
    lead.sentiment = sentiment.lower()
    lead.last_sentiment = sentiment.lower()
    lead.action_items = action_items
    lead.last_contacted = datetime.now()

    db_session.add(
        Interaction(
            lead_id=lead.id,
            type="incoming_message",
            channel=channel,
            content=body,
            direction="inbound",
            sentiment=sentiment.lower(),
            action_items=action_items,
        )
    )

    lowered = (body or "").lower()
    if sentiment == "POSITIVE":
        lead.status = "interested"
        lead.interest_level = "high"
        notify_positive_reply(lead, body)
    elif sentiment == "NEGATIVE":
        lead.status = "objection"
        lead.interest_level = "low"
        handle_objection(lead, body, channel)
    else:
        lead.interest_level = "medium"
        notify_coach(
            f"Lead #{lead.id} replied via {channel}: {body}\nSentiment: {sentiment}\nAction items: {action_items}",
            lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None,
        )

    if "yes" in lowered or "saturday" in lowered:
        event_link = create_trial_event(lead.name, lead.phone)
        confirmation = (
            "Great! You're scheduled for this Saturday at 10am. "
            "We'll send a reminder. See you then!"
        )
        send_channel_confirmation(channel, lead, confirmation)
        lead.status = "scheduled"
        notify_coach(
            f"Lead #{lead.id} scheduled a trial. Calendar event: {event_link or 'not created'}",
            lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None,
        )

    db_session.commit()
    db_session.close()


@app.route("/", methods=["GET"])
def home():
    return "LeadFlow AI is running!"


@app.route("/webhook/website-form", methods=["POST"])
def receive_lead():
    data = request.json or {}
    print("Received lead:", data)

    name = data.get("name", "Unknown")
    email = data.get("email", "No email")
    phone = data.get("phone", "")
    source = data.get("source", "website")
    message = data.get("message", "No message")

    db_session = Session()
    new_lead = Lead(
        name=name,
        email=email,
        phone=phone,
        source=source,
        message=message,
        status="new",
    )
    db_session.add(new_lead)
    db_session.commit()
    print(f"Lead saved to database with ID: {new_lead.id}")

    scoring_result = score_lead({"name": name, "message": message})
    new_lead.score = scoring_result["score"]
    new_lead.category = scoring_result["category"]

    enriched_info = enrich_lead({"message": message, "name": name})
    new_lead.sport = enriched_info["sport"]
    new_lead.age = enriched_info["age"]
    new_lead.position = enriched_info["position"]
    new_lead.goal = enriched_info["goal"]
    new_lead.urgency = enriched_info["urgency"]
    db_session.commit()

    coach = assign_lead_to_coach(new_lead.id)
    db_session.refresh(new_lead)
    assigned_text = f"Assigned coach: {coach.name}" if coach else "Assigned coach: unassigned"

    coach_message = f"""
NEW LEAD #{new_lead.id}
SCORE: {scoring_result['score']} - {scoring_result['category']}

Name: {name}
Email: {email}
Phone: {phone}
Source: {source}
Message: {message}
Sport: {enriched_info['sport'] or 'unknown'}
Age: {enriched_info['age'] or 'unknown'}
Goal: {enriched_info['goal'] or 'unknown'}
Urgency: {enriched_info['urgency']}
{assigned_text}

Reply with YES to contact this lead, or NO to reject.
    """

    notify_coach(coach_message, coach.telegram_chat_id if coach else None)
    print("Telegram message sent to coach!")
    db_session.close()

    return jsonify({"status": "received", "lead_id": new_lead.id})


@app.route("/twilio/sms-reply", methods=["POST"])
def sms_reply():
    process_incoming_reply("sms", request.form.get("From"), request.form.get("Body"))
    return str(MessagingResponse())


@app.route("/twilio/whatsapp-reply", methods=["POST"])
def whatsapp_reply():
    from_number = (request.form.get("From") or "").replace("whatsapp:", "")
    process_incoming_reply("whatsapp", from_number, request.form.get("Body"))
    return str(MessagingResponse())


@app.route("/voice-response", methods=["POST"])
def voice_response():
    digits = request.form.get("Digits")
    from_number = request.form.get("From")
    print(f"Voice response from {from_number}: pressed {digits}")

    db_session = Session()
    lead = find_lead_by_phone(db_session, from_number)
    if lead:
        db_session.add(
            Interaction(
                lead_id=lead.id,
                type="incoming_message",
                channel="voice",
                content=f"Pressed {digits or 'none'}",
                direction="inbound",
                sentiment="positive" if digits in {"1", "2"} else "neutral",
                action_items="Speak with coach" if digits == "1" else "Schedule trial" if digits == "2" else "No action items",
            )
        )
        if digits in {"1", "2"}:
            lead.status = "interested" if digits == "1" else "scheduled"
            lead.interest_level = "high"
            lead.last_contacted = datetime.now()
            if digits == "2":
                event_link = create_trial_event(lead.name, lead.phone)
                notify_coach(
                    f"Lead #{lead.id} scheduled a trial from voice response. Event: {event_link or 'not created'}",
                    lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None,
                )
        db_session.commit()
        notify_coach(
            f"Lead #{lead.id} responded on voice call with option {digits}",
            lead.coach.telegram_chat_id if lead.coach and lead.coach.telegram_chat_id else None,
        )
    db_session.close()

    response = VoiceResponse()
    if digits == "1":
        response.say("A coach will follow up with you shortly. Thank you!", voice="alice", language="en-US")
    elif digits == "2":
        response.say(
            "Great! We have noted your trial request and will confirm by message.",
            voice="alice",
            language="en-US",
        )
    elif digits == "3":
        gather = Gather(num_digits=1, action=get_public_url("/voice-response"), method="POST")
        gather.say(
            "Press 1 to speak with a coach. Press 2 to schedule a trial. Press 3 to hear this again.",
            voice="alice",
            language="en-US",
        )
        response.append(gather)
    else:
        response.say("Sorry, I didn't understand. Goodbye!", voice="alice", language="en-US")

    return str(response)


create_dashboard(app)
schedule_daily_reports(BOT_TOKEN)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, port=port)
