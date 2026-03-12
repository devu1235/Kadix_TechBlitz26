import os

from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "coach@elitesportsacademy.com")


def extract_sport(message):
    """Extract the first supported sport mentioned in the message."""
    message = message.lower()
    sports = [
        "soccer",
        "basketball",
        "tennis",
        "baseball",
        "swimming",
        "golf",
        "volleyball",
    ]

    for sport in sports:
        if sport in message:
            return sport
    return None


def send_welcome_email(lead_data):
    """
    Send a personalized welcome email to a new lead.
    """
    name = lead_data.get("name", "there")
    email = lead_data.get("email")
    sport = extract_sport(lead_data.get("message", ""))

    if not email:
        print("No email address provided")
        return False

    if not SENDGRID_API_KEY:
        print("Missing SENDGRID_API_KEY in .env")
        return False

    if sport:
        sport_text = f" our {sport} program"
    else:
        sport_text = " our academy"

    subject = "Thanks for your interest in Elite Sports Academy!"

    html_content = f"""
    <html>
      <body>
        <h2>Hi {name},</h2>

        <p>Thanks for reaching out to Elite Sports Academy! We're excited to learn more about your interest in{sport_text}.</p>

        <h3>Next Steps:</h3>
        <ul>
          <li>A free trial session at our facility</li>
          <li>Meet our expert coaches</li>
          <li>Tour our facilities</li>
        </ul>

        <p>I'd love to invite you and your athlete for a <strong>free trial session</strong>. We have spots available this Saturday at 10am.</p>

        <p>Just reply to this email or text me at (555) 123-4567 to confirm your spot!</p>

        <p>Best regards,<br>
        Coach Alex<br>
        Elite Sports Academy</p>

        <p><em>P.S. - Check out our success stories here: <a href="https://elitesportsacademy.com/success">https://elitesportsacademy.com/success</a></em></p>
      </body>
    </html>
    """

    text_content = f"""
Hi {name},

Thanks for reaching out to Elite Sports Academy! We're excited to learn more about your interest in{sport_text}.

Next Steps:
- A free trial session at our facility
- Meet our expert coaches
- Tour our facilities

I'd love to invite you and your athlete for a free trial session. We have spots available this Saturday at 10am.

Just reply to this email or text me at (555) 123-4567 to confirm your spot!

Best regards,
Coach Alex
Elite Sports Academy

P.S. - Check out our success stories here: https://elitesportsacademy.com/success
    """

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=subject,
        html_content=html_content,
        plain_text_content=text_content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {email}. Status code: {response.status_code}")
        return True
    except Exception as exc:
        print(f"Error sending email: {exc}")
        return False


if __name__ == "__main__":
    test_lead = {
        "name": "John Smith",
        "email": "devanshi.s2409276201@vcet.edu.in",
        "message": "My son wants soccer training",
    }
    send_welcome_email(test_lead)
