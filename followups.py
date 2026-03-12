import os

from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "coach@elitesportsacademy.com")


def send_follow_up_email(lead_data, follow_up_number=1):
    """
    Send a follow-up email to a lead.
    """
    name = lead_data.get("name", "there")
    email = lead_data.get("email")

    if not email or not SENDGRID_API_KEY:
        return False

    if follow_up_number == 1:
        subject = "Still thinking about training?"
        html_content = f"""
        <html>
          <body>
            <h2>Hi {name},</h2>

            <p>Just checking in! I wanted to make sure you received my previous email about our training programs at Elite Sports Academy.</p>

            <p>We have some exciting updates:</p>
            <ul>
              <li>New sessions starting next week</li>
              <li>Limited spots available in our elite training groups</li>
              <li>Special discount for first-time students</li>
            </ul>

            <p>Would you like to schedule a free trial? We have spots this Saturday at 10am.</p>

            <p>Just reply to this email or call me at (555) 123-4567.</p>

            <p>Best regards,<br>
            Coach Alex</p>
          </body>
        </html>
        """
    else:
        subject = "Last chance for free trial!"
        html_content = f"""
        <html>
          <body>
            <h2>Hi {name},</h2>

            <p>This is your last chance to claim your <strong>free trial session</strong> at Elite Sports Academy!</p>

            <p>Our next session starts soon and spots are filling up fast. Don't miss this opportunity to:</p>
            <ul>
              <li>Train with professional coaches</li>
              <li>Meet other dedicated athletes</li>
              <li>See our world-class facilities</li>
            </ul>

            <p><strong>Reply now</strong> to schedule your free trial, or call us at (555) 123-4567.</p>

            <p>Hope to see you on the field!<br>
            Coach Alex</p>
          </body>
        </html>
        """

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"Follow-up {follow_up_number} sent to {email}")
        return True
    except Exception as exc:
        print(f"Error sending follow-up: {exc}")
        return False
