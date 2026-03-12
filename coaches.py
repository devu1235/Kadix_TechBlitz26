from database import Coach, Lead, Session


def assign_lead_to_coach(lead_id):
    db_session = Session()
    lead = db_session.query(Lead).filter_by(id=lead_id).first()
    if not lead:
        db_session.close()
        return None

    if lead.sport:
        coaches = (
            db_session.query(Coach)
            .filter(Coach.sports.contains(lead.sport), Coach.active.is_(True))
            .all()
        )
    else:
        coaches = db_session.query(Coach).filter_by(active=True).all()

    if not coaches:
        coaches = db_session.query(Coach).filter_by(active=True).all()

    if not coaches:
        db_session.close()
        return None

    coach = min(coaches, key=lambda item: item.leads_count or 0)
    lead.coach_id = coach.id
    coach.leads_count = (coach.leads_count or 0) + 1
    db_session.commit()
    db_session.refresh(coach)
    db_session.expunge(coach)
    db_session.close()
    return coach


def get_coach_by_telegram_id(telegram_id):
    db_session = Session()
    coach = db_session.query(Coach).filter_by(telegram_chat_id=str(telegram_id)).first()
    if coach:
        db_session.expunge(coach)
    db_session.close()
    return coach


def register_coach(name, phone, telegram_id, sports, email=None):
    db_session = Session()
    coach = Coach(
        name=name,
        phone=phone,
        telegram_chat_id=str(telegram_id),
        sports=",".join(sports) if isinstance(sports, list) else sports,
        email=email,
        active=True,
        leads_count=0,
    )
    db_session.add(coach)
    db_session.commit()
    coach_id = coach.id
    db_session.close()
    return coach_id
