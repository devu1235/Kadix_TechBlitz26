from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

engine = create_engine("sqlite:///leads.db", echo=True)
Base = declarative_base()


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    phone = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    sports = Column(String(200), nullable=True)
    active = Column(Boolean, default=True)
    leads_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    leads = relationship("Lead", back_populates="coach")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=True)
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(50), nullable=True)
    source = Column(String(50), default="website")
    message = Column(Text)
    score = Column(Integer, default=50)
    category = Column(String(20), default="WARM")
    sport = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    position = Column(String(50), nullable=True)
    goal = Column(String(50), nullable=True)
    urgency = Column(String(20), default="low")
    sentiment = Column(String(20), nullable=True)
    interest_level = Column(String(20), default="medium")
    last_sentiment = Column(String(20), nullable=True)
    action_items = Column(Text, nullable=True)
    status = Column(String(20), default="new")
    follow_up_count = Column(Integer, default=0)
    last_contacted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    coach = relationship("Coach", back_populates="leads")
    interactions = relationship("Interaction", back_populates="lead")

    def __repr__(self):
        return f"<Lead {self.name} - {self.status}>"


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    type = Column(String(50))
    channel = Column(String(50))
    content = Column(Text)
    direction = Column(String(20))
    sentiment = Column(String(20), nullable=True)
    action_items = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    lead = relationship("Lead", back_populates="interactions")


Base.metadata.create_all(engine)


def ensure_table_columns(table_name, required_columns):
    inspector = inspect(engine)
    if table_name not in set(inspector.get_table_names()):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    with engine.begin() as connection:
        for column_name, ddl in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(ddl))


def ensure_schema():
    ensure_table_columns(
        "leads",
        {
            "coach_id": "ALTER TABLE leads ADD COLUMN coach_id INTEGER",
            "source": "ALTER TABLE leads ADD COLUMN source VARCHAR(50)",
            "score": "ALTER TABLE leads ADD COLUMN score INTEGER",
            "category": "ALTER TABLE leads ADD COLUMN category VARCHAR(20)",
            "sport": "ALTER TABLE leads ADD COLUMN sport VARCHAR(50)",
            "age": "ALTER TABLE leads ADD COLUMN age INTEGER",
            "position": "ALTER TABLE leads ADD COLUMN position VARCHAR(50)",
            "goal": "ALTER TABLE leads ADD COLUMN goal VARCHAR(50)",
            "urgency": "ALTER TABLE leads ADD COLUMN urgency VARCHAR(20)",
            "sentiment": "ALTER TABLE leads ADD COLUMN sentiment VARCHAR(20)",
            "interest_level": "ALTER TABLE leads ADD COLUMN interest_level VARCHAR(20)",
            "last_sentiment": "ALTER TABLE leads ADD COLUMN last_sentiment VARCHAR(20)",
            "action_items": "ALTER TABLE leads ADD COLUMN action_items TEXT",
            "follow_up_count": (
                "ALTER TABLE leads ADD COLUMN follow_up_count INTEGER DEFAULT 0"
            ),
            "last_contacted": "ALTER TABLE leads ADD COLUMN last_contacted DATETIME",
        },
    )
    ensure_table_columns(
        "interactions",
        {
            "sentiment": "ALTER TABLE interactions ADD COLUMN sentiment VARCHAR(20)",
            "action_items": "ALTER TABLE interactions ADD COLUMN action_items TEXT",
        },
    )
    Base.metadata.create_all(engine)


ensure_schema()

Session = sessionmaker(bind=engine)
