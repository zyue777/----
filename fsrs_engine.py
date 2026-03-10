from datetime import datetime, timezone
from fsrs import Scheduler, Card as FSRSCard, Rating, State
from database import Card as DBCard, get_session

class FSRSEngine:
    def __init__(self):
        self.scheduler = Scheduler()
        self.session = get_session()
        
    def _db_to_fsrs(self, db_card: DBCard) -> FSRSCard:
        """Convert SQLAlchemy DB model to FSRS Card model."""
        c = FSRSCard()
        # fsrs v6 State enum: Learning=1, Review=2, Relearning=3 (no 0/New)
        # New cards stored with state=0 in DB -> treat as Learning to start scheduling
        raw_state = db_card.state if db_card.state in (1, 2, 3) else 1
        c.state = State(raw_state)
        c.step = db_card.step
        c.due = db_card.due
        if db_card.stability is not None:
            c.stability = db_card.stability
        if db_card.difficulty is not None:
            c.difficulty = db_card.difficulty
        if db_card.last_review is not None:
            c.last_review = db_card.last_review
        return c
        
    def _fsrs_to_db(self, fsrs_card: FSRSCard, db_card: DBCard):
        """Update SQLAlchemy DB model with FSRS Card model values."""
        db_card.state = fsrs_card.state.value
        # step can be None for Review-state cards in fsrs v6; default to 0
        db_card.step = fsrs_card.step if fsrs_card.step is not None else 0
        db_card.due = fsrs_card.due
        db_card.stability = getattr(fsrs_card, 'stability', None)
        db_card.difficulty = getattr(fsrs_card, 'difficulty', None)
        db_card.last_review = getattr(fsrs_card, 'last_review', None)

    def get_all_decks_info(self):
        """获取数据库中所有存在的牌组名称及其下的卡片总数和今日待复习数"""
        from sqlalchemy import func, case
        now = datetime.now(timezone.utc)
        
        is_due = case((DBCard.due <= now, 1), else_=0)
        
        results = self.session.query(
            DBCard.deck_name, 
            func.count(DBCard.id),
            func.sum(is_due)
        ).group_by(DBCard.deck_name).all()
        return results

    def get_due_cards(self, limit=50, deck_name=None):
        """
        获取当前待复习的卡片 (due <= 当前时间 utc)
        如果指定了 deck_name，则只返回该牌组的卡片
        """
        now = datetime.now(timezone.utc)
        query = self.session.query(DBCard).filter(DBCard.due <= now)
        
        if deck_name:
            query = query.filter(DBCard.deck_name == deck_name)
            
        cards = query.order_by(DBCard.due.asc()).limit(limit).all()
        return cards
        
    def review_card(self, db_card: DBCard, rating_val: int):
        """
        根据用户的评分 (1-Again, 2-Hard, 3-Good, 4-Easy) 更新卡片状态
        """
        if rating_val not in [1, 2, 3, 4]:
            raise ValueError("Rating 必须是 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)")
            
        rating = Rating(rating_val)
        fsrs_card = self._db_to_fsrs(db_card)
        now = datetime.now(timezone.utc)
        
        # v6 API: Scheduler.review_card(card, rating, now) 返回 (Card, ReviewLog)
        next_card, review_log = self.scheduler.review_card(fsrs_card, rating, now)
        
        self._fsrs_to_db(next_card, db_card)
        self.session.commit()
        return db_card
