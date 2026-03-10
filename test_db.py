from database import Card, get_session, init_db
from sqlalchemy import inspect, create_engine
import os
import sys

def test_db():
    print("开始测试数据库...")
    
    # 1. 确保初始化成功
    init_db()
    
    # 2. 检查文件是否存在
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'flashcards.db')
    if not os.path.exists(db_path):
        print(f"失败: 文件未找到 {db_path}")
        sys.exit(1)
    print(f"成功: 找到数据库文件 -> {db_path}")

    # 3. 检查表和列结构
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'cards' not in tables:
        print("失败: 表 'cards' 未创建")
        sys.exit(1)
        
    print("成功: 找到 'cards' 表")

    columns = [col['name'] for col in inspector.get_columns('cards')]
    print("列清单:", columns)
    
    expected_cols = ['id', 'word', 'translation', 'context', 'deck_name', 'sub_deck', 
                     'state', 'step', 'stability', 'difficulty', 'due', 'last_review']
    
    for col in expected_cols:
        if col not in columns:
            print(f"失败: 缺少预期的列 '{col}'")
            sys.exit(1)
            
    print("成功: 所有预期列均已创建")
    
    # 4. 插入一条测试数据
    session = get_session()
    test_word = "test_word_123"
    
    # 清理之前可能存在的残余
    existing = session.query(Card).filter_by(word=test_word).first()
    if existing:
        session.delete(existing)
        session.commit()

    card = Card(
        deck_name="Test Deck",
        sub_deck="Sub",
        word=test_word,
        translation="测试词",
        context="用于测试的代码语境",
    )
    
    session.add(card)
    session.commit()
    
    # 验证是否能读出
    fetched = session.query(Card).filter_by(word=test_word).first()
    if not fetched:
        print("失败: 插入数据未读出")
        sys.exit(1)
        
    print(f"成功: 数据插入并读取测试通过 -> {fetched}")
    print("==============")
    print("数据库测试: 全部通过！")

if __name__ == "__main__":
    test_db()
