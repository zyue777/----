# 📖 MD-Flashcards

**MD-Flashcards** is a terminal-based (TUI) flashcard app that reads your Markdown notes and turns them into spaced-repetition flashcards — powered by the **FSRS** algorithm.

Write your vocabulary or knowledge in a simple Markdown table, put it in a folder, press `s` to sync, and start learning. The app schedules reviews automatically so you study the right cards at the right time.

---

## ✨ Features

- 📂 **Deck-based organization** — each folder in `data/` is a deck
- 📋 **Sub-decks via `##` headings** inside a Markdown file
- 🧠 **FSRS spaced repetition** (state-of-the-art algorithm)
- 🔊 **Auto pronunciation** via edge-tts + mpv (English TTS, cached locally)
- 🖥️ **Pure terminal UI** — no browser, no Electron, just your terminal
- ⌨️ **Keyboard-first** shortcuts (`Space` to flip, `1-4` to rate)
- 🖱️ **Mouse supported** — click to flip, click to rate

---

## 📦 Requirements

| Dependency | Install |
|---|---|
| Python 3.11+ | via [Miniconda](https://docs.conda.io/en/latest/miniconda.html) |
| mpv (audio player) | `sudo apt install mpv` |
| conda env | see below |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/md-flashcards.git
cd md-flashcards
```

### 2. Create the conda environment

```bash
conda create -n md-flashcards python=3.11 -y
conda activate md-flashcards
pip install textual fsrs edge-tts sqlalchemy markdown-it-py
```

### 3. Install mpv (for audio)

```bash
sudo apt install mpv   # Ubuntu / Debian
# or
brew install mpv       # macOS
```

### 4. Run the app

```bash
python tui.py
```

---

## 📁 Adding Your Own Flashcards

The app reads Markdown files from the `data/` directory. Each **subfolder = one Deck**.

### Step 1 — Create a deck folder

```
data/
└── My_English_Words/     ← deck name shown in sidebar
    └── vocab.md
```

### Step 2 — Write your Markdown file

Follow this format (see also `data/standard_template.md` for a copy-paste template):

```markdown
# My Vocabulary Book Title

## Business Terms     ← this becomes a Sub-deck tag

| 英文词汇 | 中文释义 | 商业语境与潜台词 / 备注 |
| --- | --- | --- |
| **Headwind** | 逆风 / 不利因素 | 财报常用：拖累业绩的宏观因素 |
| **Tailwind** | 顺风 / 利好因素 | 财报常用：助推业绩的宏观利好 |

## Finance Terms      ← another Sub-deck

| 英文词汇 | 中文释义 | 商业语境与潜台词 / 备注 |
| --- | --- | --- |
| **Cash Cow** | 现金牛 | 能为公司带来强劲现金流的核心业务 |
```

**Rules:**
- Column 1: English word (bold `**word**` or plain both work)
- Column 2: Chinese translation
- Column 3: Context / notes (can be empty)
- Do **not** change the column headers — the parser recognizes them

### Step 3 — Sync in the app

Press **`s`** inside the app to scan and import all Markdown files from `data/`.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `s` | Sync / import Markdown files from `data/` |
| `Space` or `Enter` | Flip card |
| `1` | Rate: Again (review soon) |
| `2` | Rate: Hard |
| `3` | Rate: Good |
| `4` | Rate: Easy |
| `q` | Quit |

> You can also **click** the card to flip it, and **click** the rating buttons.

---

## 📂 Project File Structure

```
md-flashcards/
├── tui.py                  # Main app entry point
├── fsrs_engine.py          # FSRS scheduling logic
├── database.py             # SQLAlchemy DB models
├── parser.py               # Markdown file parser
├── audio.py                # edge-tts + mpv audio playback
│
├── data/                   # ← Put your decks here
│   ├── standard_template.md    # Copy-paste template for new decks
│   └── YOUR_DECK_FOLDER/       # One folder = one deck
│       └── your_words.md
│
├── .cache/audio/           # ⚠️ Auto-generated — safe to delete
│                           #   (MP3 cache from edge-tts, regenerated on demand)
│
└── data/flashcards.db      # ⚠️ Your review history — DO NOT delete
                            #   unless you want to reset all progress
```

---

## 🗑️ What You Can Safely Delete

| Path | Safe to delete? | Notes |
|---|---|---|
| `.cache/audio/` | ✅ Yes | MP3 cache, auto-regenerated on next run |
| `__pycache__/` | ✅ Yes | Python bytecode, auto-regenerated |
| `data/Crocs_Earnings/` | ✅ Yes | Example deck, can be removed |
| `data/standard_template.md` | ✅ Yes | Just a reference template |
| `data/flashcards.db` | ⚠️ Careful | Deletes **all** your review history & progress |

---

## 🤝 Contributing

PRs and issues are welcome! If you want to add support for new card formats, new TTS engines, or UI improvements, feel free to open an issue first.

---

## 📄 License

MIT License — free to use, modify, and share.
