import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from coaches import get_coach_by_telegram_id, register_coach
from channel_selector import get_channel_message, select_best_channel
from database import Interaction, Lead, Session
from email_sender import send_welcome_email
from followups import send_follow_up_email
from messaging import (
    make_voice_call,
    make_voice_call_with_options,
    send_sms,
    send_whatsapp,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DEFAULT_COACH_CHAT_ID = os.getenv("DEFAULT_COACH_CHAT_ID", "")

scheduler = BackgroundScheduler()
scheduler.start()


def is_default_coach(chat_id):
    return str(chat_id) == str(DEFAULT_COACH_CHAT_ID)


def get_scoped_coach(chat_id):
    coach = get_coach_by_telegram_id(chat_id)
    if coach:
        return coach
    if is_default_coach(chat_id):
        return None
    return False


def log_interaction(
    lead_id,
    interaction_type,
    channel,
    content,
    direction="outbound",
    sentiment=None,
    action_items=None,
):
    db_session = Session()
    db_session.add(
        Interaction(
            lead_id=lead_id,
            type=interaction_type,
            channel=channel,
            content=content,
            direction=direction,
            sentiment=sentiment,
            action_items=action_items,
        )
    )
    db_session.commit()
    db_session.close()


def schedule_follow_up(lead_id, days=3):
    run_date = datetime.now() + timedelta(days=days)
    scheduler.add_job(
        func=send_follow_up,
        trigger=DateTrigger(run_date=run_date),
        args=[lead_id],
        id=f"followup_{lead_id}_{days}",
        replace_existing=True,
    )
    print(f"Follow-up scheduled for lead {lead_id} on {run_date}")


def send_follow_up(lead_id):
    print(f"Time to follow up with lead {lead_id}")
    db_session = Session()
    lead = db_session.query(Lead).filter_by(id=lead_id).first()

    if lead and lead.status == "approved":
        lead.follow_up_count = (lead.follow_up_count or 0) + 1
        follow_up_num = lead.follow_up_count

        if follow_up_num <= 2:
            channel = select_best_channel(lead)
            message_type = "followup1" if follow_up_num == 1 else "followup2"
            next_follow_up_days = 3 if follow_up_num == 1 else None
            message_text = get_channel_message(lead, channel, message_type)

            if lead.phone:
                if channel == "sms":
                    result = send_sms(lead.phone, message_text)
                elif channel == "whatsapp":
                    result = send_whatsapp(lead.phone, message_text)
                else:
                    result = make_voice_call_with_options(lead.phone, message_text)

                if result["success"]:
                    log_interaction(lead.id, "outgoing_message", channel, message_text)
                    if next_follow_up_days:
                        schedule_follow_up(lead_id, days=next_follow_up_days)
                    else:
                        lead.status = "followed_up"
            else:
                email_data = {"name": lead.name, "email": lead.email}
                if follow_up_num == 1:
                    if send_follow_up_email(email_data, 1):
                        log_interaction(lead.id, "outgoing_message", "email", "Follow-up email #1")
                        schedule_follow_up(lead_id, days=4)
                else:
                    if send_follow_up_email(email_data, 2):
                        log_interaction(lead.id, "outgoing_message", "email", "Follow-up email #2")
                        lead.status = "followed_up"

        lead.last_contacted = datetime.now()
        db_session.commit()

    db_session.close()


def scoped_leads_query(db_session, coach_or_none):
    query = db_session.query(Lead)
    if coach_or_none:
        query = query.filter_by(coach_id=coach_or_none.id)
    return query


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello Coach! I'm LeadFlow AI. I'll notify you when new leads arrive.\n"
        "Reply YES to contact a lead, or NO to reject."
    )


async def register_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
        sports = context.args[1] if len(context.args) > 1 else ""
    except IndexError:
        await update.message.reply_text('Usage: /register "Your Name" sport1,sport2')
        return

    coach_id = register_coach(name, "Unknown", update.effective_chat.id, sports)
    await update.message.reply_text(f"Registered as coach {name} (ID: {coach_id})")


async def pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach = get_scoped_coach(update.effective_chat.id)
    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    total = query.count()
    new = query.filter_by(status="new").count()
    approved = query.filter_by(status="approved").count()
    rejected = query.filter_by(status="rejected").count()
    interested = query.filter_by(status="interested").count()
    hot = query.filter(Lead.score >= 70).count()
    db_session.close()

    await update.message.reply_text(
        f"""
PIPELINE SUMMARY
Total Leads: {total}
New: {new}
Approved: {approved}
Interested: {interested}
Rejected: {rejected}
Hot Leads: {hot}
        """
    )


async def hot_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach = get_scoped_coach(update.effective_chat.id)
    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    leads = query.filter_by(status="approved").order_by(Lead.score.desc()).limit(5).all()
    db_session.close()

    if not leads:
        await update.message.reply_text("No hot leads right now.")
        return

    message = "HOT LEADS:\n\n"
    for lead in leads:
        message += f"#{lead.id}: {lead.name} - {lead.sport or '?'} - Score {lead.score or 0}\n"
    await update.message.reply_text(message)


async def lead_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach = get_scoped_coach(update.effective_chat.id)
    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    try:
        lead_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /lead [lead_id]")
        return

    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    lead = query.filter_by(id=lead_id).first()
    db_session.close()

    if not lead:
        await update.message.reply_text(f"Lead #{lead_id} not found.")
        return

    await update.message.reply_text(
        f"""
LEAD #{lead.id}
Name: {lead.name}
Email: {lead.email}
Phone: {lead.phone or 'N/A'}
Sport: {lead.sport or 'Unknown'}
Age: {lead.age or 'Unknown'}
Goal: {lead.goal or 'Unknown'}
Status: {lead.status}
Score: {lead.score or 0} - {lead.category or 'Unknown'}
Sentiment: {lead.last_sentiment or 'Unknown'}
Actions: {lead.action_items or 'None'}
Created: {lead.created_at.strftime('%Y-%m-%d %H:%M')}
        """
    )


async def interactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach = get_scoped_coach(update.effective_chat.id)
    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    try:
        lead_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /interactions [lead_id]")
        return

    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    lead = query.filter_by(id=lead_id).first()
    if not lead:
        db_session.close()
        await update.message.reply_text(f"No interactions found for lead #{lead_id}")
        return

    recent = (
        db_session.query(Interaction)
        .filter_by(lead_id=lead_id)
        .order_by(Interaction.created_at.desc())
        .limit(5)
        .all()
    )
    db_session.close()

    if not recent:
        await update.message.reply_text(f"No interactions found for lead #{lead_id}")
        return

    message = f"Recent interactions for lead #{lead_id}:\n\n"
    for item in recent:
        marker = "OUT" if item.direction == "outbound" else "IN"
        preview = (item.content or "")[:50]
        sentiment = f" [{item.sentiment}]" if item.sentiment else ""
        message += (
            f"{marker} {item.channel.upper()}{sentiment} "
            f"({item.created_at.strftime('%m/%d %H:%M')}):\n{preview}...\n\n"
        )
    await update.message.reply_text(message)


async def manual_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coach = get_scoped_coach(update.effective_chat.id)
    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    try:
        lead_id = int(context.args[0])
        message_text = " ".join(context.args[1:])
        if not message_text:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /msg [lead_id] "Your message"')
        return

    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    lead = query.filter_by(id=lead_id).first()
    db_session.close()

    if not lead or not lead.phone:
        await update.message.reply_text(f"Lead #{lead_id} not found or has no phone number")
        return

    context.user_data["pending_message"] = {"lead_id": lead_id, "text": message_text}
    await update.message.reply_text(
        f"Send to {lead.name} via:\n1. SMS\n2. WhatsApp\n3. Voice Call\nReply with 1, 2, or 3"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    coach = get_scoped_coach(chat_id)

    if coach is False:
        await update.message.reply_text("You're not registered as a coach. Please contact admin.")
        return

    pending = context.user_data.get("pending_message")
    if pending:
        if text == "1":
            channel = "sms"
        elif text == "2":
            channel = "whatsapp"
        elif text == "3":
            channel = "voice"
        else:
            await update.message.reply_text("Please reply with 1, 2, or 3")
            return

        db_session = Session()
        query = scoped_leads_query(db_session, coach)
        lead = query.filter_by(id=pending["lead_id"]).first()
        db_session.close()

        if lead:
            if channel == "sms":
                result = send_sms(lead.phone, pending["text"])
            elif channel == "whatsapp":
                result = send_whatsapp(lead.phone, pending["text"])
            else:
                result = make_voice_call(lead.phone, pending["text"])

            if result["success"]:
                log_interaction(lead.id, "outgoing_message", channel, pending["text"])
                await update.message.reply_text(f"Message sent via {channel}")
            else:
                await update.message.reply_text(f"Failed: {result.get('error', 'Unknown error')}")

        context.user_data.pop("pending_message", None)
        return

    response = text.upper()
    db_session = Session()
    query = scoped_leads_query(db_session, coach)
    latest_lead = query.filter_by(status="new").order_by(Lead.id.desc()).first()

    if response == "YES":
        if latest_lead:
            latest_lead.status = "approved"
            latest_lead.follow_up_count = 0
            db_session.commit()
            await update.message.reply_text(f"Great! Lead #{latest_lead.id} ({latest_lead.name}) approved.")

            if latest_lead.phone:
                channel = select_best_channel(latest_lead)
                message_text = get_channel_message(latest_lead, channel, "welcome")

                if channel == "sms":
                    result = send_sms(latest_lead.phone, message_text)
                elif channel == "whatsapp":
                    result = send_whatsapp(latest_lead.phone, message_text)
                else:
                    result = make_voice_call_with_options(latest_lead.phone, message_text)

                if result["success"]:
                    log_interaction(latest_lead.id, "outgoing_message", channel, message_text)
                    latest_lead.last_contacted = datetime.now()
                    db_session.commit()
                    if channel == "voice":
                        schedule_follow_up(latest_lead.id, days=2)
                        await update.message.reply_text(f"Voice call initiated to {latest_lead.phone}")
                    elif channel == "whatsapp":
                        schedule_follow_up(latest_lead.id, days=3)
                        await update.message.reply_text(f"WhatsApp sent to {latest_lead.phone}")
                    else:
                        schedule_follow_up(latest_lead.id, days=3)
                        await update.message.reply_text(f"SMS sent to {latest_lead.phone}")
                else:
                    await update.message.reply_text(
                        f"Channel send failed: {result.get('error', 'Unknown error')}"
                    )
            else:
                await update.message.reply_text("No phone number for this lead. Sending email only.")
                lead_data = {
                    "name": latest_lead.name,
                    "email": latest_lead.email,
                    "message": latest_lead.message,
                }
                if send_welcome_email(lead_data):
                    log_interaction(latest_lead.id, "outgoing_message", "email", "Welcome email sent")
                    latest_lead.last_contacted = datetime.now()
                    db_session.commit()
                    await update.message.reply_text(f"Welcome email sent to {latest_lead.email}")
                else:
                    await update.message.reply_text(f"Could not send email to {latest_lead.email}")
        else:
            await update.message.reply_text("No new leads to approve.")
    elif response == "NO":
        if latest_lead:
            latest_lead.status = "rejected"
            db_session.commit()
            await update.message.reply_text(
                f"OK, lead #{latest_lead.id} ({latest_lead.name}) marked as rejected."
            )
        else:
            await update.message.reply_text("No new leads to reject.")
    else:
        await update.message.reply_text("I didn't understand. Please reply with YES or NO.")

    db_session.close()


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register_me))
    app.add_handler(CommandHandler("pipeline", pipeline))
    app.add_handler(CommandHandler("hot", hot_leads))
    app.add_handler(CommandHandler("lead", lead_detail))
    app.add_handler(CommandHandler("interactions", interactions))
    app.add_handler(CommandHandler("msg", manual_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is listening for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
