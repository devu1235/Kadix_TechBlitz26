import os

from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse

load_dotenv()


def get_public_url(path):
    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}{path}"
    return path


def get_client():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise ValueError("Missing Twilio credentials in .env")
    return Client(account_sid, auth_token)


def send_sms(to_phone, message_text):
    try:
        client = get_client()
        message = client.messages.create(
            body=message_text,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_phone,
        )
        print(f"SMS sent to {to_phone}. SID: {message.sid}")
        return {"success": True, "sid": message.sid, "status": message.status}
    except Exception as exc:
        print(f"Error sending SMS: {exc}")
        return {"success": False, "error": str(exc)}


def send_whatsapp(to_phone, message_text):
    try:
        client = get_client()
        message = client.messages.create(
            body=message_text,
            from_=f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
            to=f"whatsapp:{to_phone}",
        )
        print(f"WhatsApp sent to {to_phone}. SID: {message.sid}")
        return {"success": True, "sid": message.sid, "status": message.status}
    except Exception as exc:
        print(f"Error sending WhatsApp: {exc}")
        return {"success": False, "error": str(exc)}


def make_voice_call(to_phone, message_text):
    try:
        client = get_client()
        response = VoiceResponse()
        response.say(message_text, voice="alice", language="en-US")
        call = client.calls.create(
            twiml=str(response),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_phone,
        )
        print(f"Voice call initiated to {to_phone}. SID: {call.sid}")
        return {"success": True, "sid": call.sid, "status": call.status}
    except Exception as exc:
        print(f"Error making voice call: {exc}")
        return {"success": False, "error": str(exc)}


def make_voice_call_with_options(to_phone, message_text, callback_url=None):
    try:
        client = get_client()
        response = VoiceResponse()
        response.say(
            "Hello! This is an automated message from Elite Sports Academy.",
            voice="alice",
            language="en-US",
        )
        response.say(message_text, voice="alice", language="en-US")
        gather = Gather(
            num_digits=1,
            action=callback_url or get_public_url("/voice-response"),
            method="POST",
        )
        gather.say(
            "Press 1 to speak with a coach. Press 2 to schedule a trial. Press 3 to hear this again.",
            voice="alice",
            language="en-US",
        )
        response.append(gather)
        response.say(
            "We'll send you a text message instead. Goodbye!",
            voice="alice",
            language="en-US",
        )

        call = client.calls.create(
            twiml=str(response),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_phone,
        )
        print(f"Interactive voice call initiated to {to_phone}")
        return {"success": True, "sid": call.sid, "status": call.status}
    except Exception as exc:
        print(f"Error making interactive call: {exc}")
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    test_phone = "+1234567890"
    print(send_sms(test_phone, "Hello from LeadFlow AI! This is a test message."))
