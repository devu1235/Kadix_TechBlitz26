import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

from database import Coach, Lead, Session

_reports_scheduler = None


async def send_daily_summary(bot_token):
    bot = Bot(token=bot_token)
    db_session = Session()
    coaches = db_session.query(Coach).filter_by(active=True).all()
    yesterday = datetime.now() - timedelta(days=1)

    for coach in coaches:
        leads = db_session.query(Lead).filter_by(coach_id=coach.id).all()
        total = len(leads)
        new_today = sum(1 for lead in leads if lead.created_at >= yesterday)
        interested = sum(1 for lead in leads if lead.status == "interested")
        scheduled = sum(1 for lead in leads if lead.status == "scheduled")
        hot = sum(1 for lead in leads if (lead.score or 0) >= 70)
        top_leads = (
            db_session.query(Lead)
            .filter_by(coach_id=coach.id, status="approved")
            .order_by(Lead.score.desc())
            .limit(3)
            .all()
        )

        message = f"""
DAILY SUMMARY for {coach.name}
Date: {datetime.now().strftime('%B %d, %Y')}

Your leads:
- Total active: {total}
- New today: {new_today}
- Interested: {interested}
- Trials scheduled: {scheduled}
- Hot leads: {hot}

Today's priorities:
        """
        for index, lead in enumerate(top_leads, 1):
            message += f"\n{index}. {lead.name} - {lead.sport or '?'} (Score: {lead.score or 0})"
        message += "\n\nReply /pipeline to see all leads."

        if coach.telegram_chat_id:
            try:
                await bot.send_message(chat_id=coach.telegram_chat_id, text=message)
                print(f"Daily summary sent to {coach.name}")
            except Exception as exc:
                print(f"Error sending daily summary to {coach.name}: {exc}")

    db_session.close()


def schedule_daily_reports(bot_token):
    global _reports_scheduler
    if _reports_scheduler:
        return _reports_scheduler

    scheduler = BackgroundScheduler()

    def send_reports():
        asyncio.run(send_daily_summary(bot_token))

    scheduler.add_job(send_reports, "cron", hour=8, minute=0)
    scheduler.start()
    _reports_scheduler = scheduler
    print("Daily reports scheduled for 8am")
    return scheduler
