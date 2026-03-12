import os
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    if not os.path.exists("credentials.json"):
        print("Google Calendar credentials.json not found")
        return None

    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


def create_trial_event(lead_name, lead_phone, preferred_time=None):
    service = get_calendar_service()
    if not service:
        return None

    if not preferred_time:
        today = datetime.now()
        days_ahead = 5 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_saturday = today + timedelta(days=days_ahead)
        start_time = next_saturday.replace(hour=10, minute=0, second=0, microsecond=0)
    else:
        start_time = preferred_time

    end_time = start_time + timedelta(hours=1)
    timezone = os.getenv("CALENDAR_TIMEZONE", "America/New_York")
    event = {
        "summary": f"Trial Session - {lead_name}",
        "description": f"Phone: {lead_phone}",
        "start": {"dateTime": start_time.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_time.isoformat(), "timeZone": timezone},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    print(f'Event created: {created.get("htmlLink")}')
    return created.get("htmlLink")
