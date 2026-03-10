import os
import re
import glob
from database import Card, get_session

def parse_markdown_table_row(line):
    line = line.strip()
    # Must start and end with '|'
    if not line.startswith('|') or not line.endswith('|'):
        return None
    
    # Split, clean up empty leading/trailing artifacts from '|'
    parts = [p.strip() for p in line.split('|')][1:-1]
    
    if len(parts) >= 2:
        # Strip bold from word, e.g., "**GAAP**" -> "GAAP"
        word = re.sub(r'\*\*(.*?)\*\*', r'\1', parts[0]).strip()
        translation = parts[1]
        context = parts[2] if len(parts) > 2 else ""
        return word, translation, context
    return None

def process_file(filepath, session):
    # deck_name taken from the parent folder (e.g., data/Crocs_Earnings/xxx.md -> Crocs_Earnings)
    deck_name = os.path.basename(os.path.dirname(filepath))
    current_sub_deck = None
    
    added = 0
    skipped = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Capture Markdown H2 as sub_deck topic
            if line.startswith('## '):
                current_sub_deck = line[3:].strip()
                continue
                
            # Skip the table header and separator rows
            if '英文词汇' in line and '中文释义' in line:
                continue
            if re.match(r'^\|\s*---', line):
                continue
                
            parsed = parse_markdown_table_row(line)
            if parsed:
                word, translation, context = parsed
                if not word: 
                    continue
                
                # Incremental Check
                existing = session.query(Card).filter_by(word=word).first()
                if not existing:
                    card = Card(
                        deck_name=deck_name,
                        sub_deck=current_sub_deck,
                        word=word,
                        translation=translation,
                        context=context
                    )
                    session.add(card)
                    added += 1
                else:
                    skipped += 1
                    
    session.commit()
    return added, skipped

def sync_data(data_dir=None):
    if not data_dir:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    session = get_session()
    
    # Glob for markdown files in subfolders inside "data"
    md_files = glob.glob(os.path.join(data_dir, '*', '*.md'))
    if not md_files:
        print(f"在 {data_dir} 子目录中未找到任何 markdown (必须放在分类文件夹下)。")
        return
        
    print("====== 数据同步开始 ======")
    total_added = 0
    total_skipped = 0
    
    for file in md_files:
        added, skipped = process_file(file, session)
        print(f"[解析] {os.path.basename(file)} | 分类: {os.path.basename(os.path.dirname(file))}")
        print(f"  -> 新增: {added} 张, 跳过重复: {skipped} 张")
        total_added += added
        total_skipped += skipped
        
    print(f"====== 同步完成! 共新增 {total_added} 张卡片，跳过 {total_skipped} 张。======")

if __name__ == '__main__':
    sync_data()
