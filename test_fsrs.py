from fsrs_engine import FSRSEngine
from database import Card

engine = FSRSEngine()
due_cards = engine.get_due_cards(limit=1)

if not due_cards:
    print("没有到期的卡片")
else:
    card = due_cards[0]
    print(f"当前复习卡片: {card.word}")
    print(f"原到期时间: {card.due}")
    print(f"状态: {card.state}, Step: {card.step}")
    
    # 模拟用户点击 3 (Good)
    print(">>> 模拟评分: 3 (Good)")
    updated_card = engine.review_card(card, 3)
    
    print(f"新到期时间: {updated_card.due}")
    print(f"新状态: {updated_card.state}, Step: {updated_card.step}")
