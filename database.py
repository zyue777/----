from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import enum
import os

Base = declarative_base()

class FSRSState(enum.IntEnum):
    """
    FSRS states:
    0: New
    1: Learning
    2: Review
    3: Relearning
    """
    New = 0
    Learning = 1
    Review = 2
    Relearning = 3

class Card(Base):
    """
    Database model matching the expected structure of a flashcard + FSRS algorithm.
    """
    __tablename__ = 'cards'

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    deck_name = Column(String(255), nullable=False, index=True) # E.g., folder name
    sub_deck = Column(String(255), nullable=True, index=True)   # E.g., Markdown header (H2)
    word = Column(String(255), unique=True, nullable=False, index=True)
    translation = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    
    # FSRS core algorithm fields (based on fsrs.models.Card)
    state = Column(Integer, default=FSRSState.New.value, nullable=False) # Maps to fsrs State enum
    step = Column(Integer, default=0, nullable=False)
    
    # Optional/Null prior to review
    stability = Column(Float, nullable=True)
    difficulty = Column(Float, nullable=True)
    
    # Next review time
    due = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Previous review time
    last_review = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Card(id={self.id}, word='{self.word}', deck='{self.deck_name}', due={self.due})>"

# Database configuration logic
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "flashcards.db")

def get_engine():
    # Make sure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return create_engine(f'sqlite:///{DB_PATH}', echo=False)

def init_db():
    """Create all tables if they don't exist"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"数据库初始化成功: {DB_PATH}")

def get_session():
    """Get a new database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

if __name__ == "__main__":
    init_db()
