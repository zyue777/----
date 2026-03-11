"""
MD-Flashcards GUI
独立窗口版本 — 可拖动、可最小化、完全独立于终端
"""

import tkinter as tk
from tkinter import font as tkfont
import threading

from fsrs_engine import FSRSEngine
from audio import play_audio
import parser as md_parser

# ─────────────── Color Palette ───────────────
BG_DARK       = "#0f1117"   # main background
BG_CARD       = "#1a1d2e"   # card surface
BG_SIDEBAR    = "#12141f"   # sidebar
BG_SIDEBAR_SEL= "#2a2d45"   # selected deck
BG_HEADER     = "#0d0f1a"   # top bar
ACCENT        = "#6c63ff"   # purple accent
ACCENT2       = "#00d4ff"   # cyan accent
TEXT_PRIMARY  = "#e8e6f0"
TEXT_SECONDARY= "#8f8daa"
TEXT_DIM      = "#555470"

BTN_AGAIN     = "#c0392b"
BTN_HARD      = "#d68910"
BTN_GOOD      = "#2471a3"
BTN_EASY      = "#1e8449"
BTN_TEXT      = "#ffffff"


class MDFlashcardsGUI:
    def __init__(self):
        self.engine = FSRSEngine()
        self.due_queue = []
        self.current_deck = None
        self.card_flipped = False

        # ─── Root Window ───
        self.root = tk.Tk()
        self.root.title("MD Flashcards")
        self.root.geometry("820x560")
        self.root.minsize(700, 480)
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        self._setup_fonts()
        self._build_layout()
        self._load_decks()

        # bind keyboard shortcuts
        self.root.bind("<space>",   lambda e: self._flip_card())
        self.root.bind("<Return>",  lambda e: self._flip_card())
        self.root.bind("1",         lambda e: self._rate(1))
        self.root.bind("2",         lambda e: self._rate(2))
        self.root.bind("3",         lambda e: self._rate(3))
        self.root.bind("4",         lambda e: self._rate(4))
        self.root.bind("s",         lambda e: self._sync())
        self.root.bind("<q>",       lambda e: self.root.quit())

    # ─────────────── Fonts ───────────────
    def _setup_fonts(self):
        # Use 'song ti' which is explicitly listed in tkinter.font.families() on this system
        f_name = "song ti"
        self.font_title   = tkfont.Font(family=f_name, size=13, weight="bold")
        self.font_word    = tkfont.Font(family=f_name, size=28, weight="bold")
        self.font_def     = tkfont.Font(family=f_name, size=13)
        self.font_context = tkfont.Font(family=f_name, size=11)
        self.font_btn     = tkfont.Font(family=f_name, size=10, weight="bold")
        self.font_deck    = tkfont.Font(family=f_name, size=11)
        self.font_small   = tkfont.Font(family=f_name, size=9)
        self.font_header  = tkfont.Font(family=f_name, size=12, weight="bold")

    # ─────────────── Layout ───────────────
    def _build_layout(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=BG_HEADER, height=48)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text="MD Flashcards",
                 bg=BG_HEADER, fg=ACCENT2,
                 font=self.font_header).pack(side=tk.LEFT, padx=16, pady=10)

        self.lbl_status = tk.Label(header, text="", bg=BG_HEADER,
                                   fg=TEXT_SECONDARY, font=self.font_small)
        self.lbl_status.pack(side=tk.RIGHT, padx=16)

        # sync button in header
        tk.Button(header, text="Sync", bg=ACCENT, fg=BTN_TEXT,
                  font=self.font_small, relief="flat", cursor="hand2",
                  padx=10, pady=4,
                  command=self._sync).pack(side=tk.RIGHT, padx=8, pady=8)

        # ── Main area (sidebar + card) ──
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ──
        sidebar = tk.Frame(main, bg=BG_SIDEBAR, width=260)
        sidebar.pack(fill=tk.Y, side=tk.LEFT)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Decks", bg=BG_SIDEBAR,
                 fg=TEXT_SECONDARY, font=self.font_small).pack(
                     anchor="w", padx=12, pady=(12, 4))

        # scrollable deck list
        list_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6)

        # scrollbar setup
        self.v_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                       bg=BG_SIDEBAR, troughcolor=BG_SIDEBAR,
                                       activebackground=ACCENT)
        self.h_scrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL,
                                       bg=BG_SIDEBAR, troughcolor=BG_SIDEBAR,
                                       activebackground=ACCENT)
        
        self.deck_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            bg=BG_SIDEBAR, fg=TEXT_PRIMARY,
            selectbackground=BG_SIDEBAR_SEL, selectforeground=ACCENT2,
            relief="flat", bd=0,
            font=self.font_deck,
            activestyle="none",
            highlightthickness=0,
            cursor="hand2"
        )
        self.v_scrollbar.config(command=self.deck_listbox.yview)
        self.h_scrollbar.config(command=self.deck_listbox.xview)
        
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.deck_listbox.pack(fill=tk.BOTH, expand=True)
        
        self.deck_listbox.bind("<<ListboxSelect>>", self._on_deck_selected)
        # Bind mouse wheel for better scrolling experience
        self.deck_listbox.bind("<MouseWheel>", self._on_mousewheel)
        self.deck_listbox.bind("<Button-4>", self._on_mousewheel)
        self.deck_listbox.bind("<Button-5>", self._on_mousewheel)

        # keyboard hint at bottom of sidebar
        hint = ("Space / Enter: flip\n"
                "1 Again  2 Hard\n"
                "3 Good   4 Easy\n"
                "s: sync  q: quit")
        tk.Label(sidebar, text=hint, bg=BG_SIDEBAR, fg=TEXT_DIM,
                 font=self.font_small, justify="left").pack(
                     anchor="w", padx=12, pady=(0, 12))

        # ── Card area ──
        card_area = tk.Frame(main, bg=BG_DARK)
        card_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Card face (clickable)
        self.card_frame = tk.Frame(card_area, bg=BG_CARD,
                                   highlightthickness=2,
                                   highlightbackground=ACCENT)
        self.card_frame.pack(fill=tk.BOTH, expand=True)
        self.card_frame.bind("<Button-1>", lambda e: self._on_card_click())

        self.lbl_card_word = tk.Label(
            self.card_frame,
            text="← 选择左侧牌组开始",
            bg=BG_CARD, fg=TEXT_PRIMARY,
            font=self.font_word,
            wraplength=500,
            justify="center",
            cursor="hand2"
        )
        self.lbl_card_word.pack(expand=True, pady=(40, 8))
        self.lbl_card_word.bind("<Button-1>", lambda e: self._on_card_click())

        self.lbl_card_def = tk.Label(
            self.card_frame,
            text="",
            bg=BG_CARD, fg=ACCENT2,
            font=self.font_def,
            wraplength=500,
            justify="center"
        )
        self.lbl_card_def.pack(expand=False)
        self.lbl_card_def.bind("<Button-1>", lambda e: self._on_card_click())

        self.lbl_card_ctx = tk.Label(
            self.card_frame,
            text="",
            bg=BG_CARD, fg=TEXT_SECONDARY,
            font=self.font_context,
            wraplength=480,
            justify="center"
        )
        self.lbl_card_ctx.pack(expand=False, pady=(6, 40))
        self.lbl_card_ctx.bind("<Button-1>", lambda e: self._on_card_click())

        self.lbl_flip_hint = tk.Label(
            self.card_frame,
            text="点击卡片 或 按 Space 翻转",
            bg=BG_CARD, fg=TEXT_DIM,
            font=self.font_small
        )
        self.lbl_flip_hint.pack(side=tk.BOTTOM, pady=10)
        self.lbl_flip_hint.bind("<Button-1>", lambda e: self._on_card_click())

        # ── Rating buttons row ──
        self.btn_frame = tk.Frame(card_area, bg=BG_DARK)
        self.btn_frame.pack(fill=tk.X, pady=(10, 0))

        btn_cfg = [
            ("1  Again", BTN_AGAIN, 1),
            ("2  Hard",  BTN_HARD,  2),
            ("3  Good",  BTN_GOOD,  3),
            ("4  Easy",  BTN_EASY,  4),
        ]
        for label, color, rating in btn_cfg:
            tk.Button(
                self.btn_frame,
                text=label,
                bg=color, fg=BTN_TEXT,
                font=self.font_btn,
                relief="flat",
                cursor="hand2",
                padx=20, pady=10,
                activebackground=color,
                activeforeground=BTN_TEXT,
                command=lambda r=rating: self._rate(r)
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        self._show_rating_buttons(False)

    # ─────────────── Deck loading ───────────────
    def _load_decks(self):
        self.deck_listbox.delete(0, tk.END)
        self._deck_names = []

        decks_info = self.engine.get_all_decks_info()
        if not decks_info:
            self.deck_listbox.insert(tk.END, "  (未找到牌组)")
            self.deck_listbox.insert(tk.END, "  请按 s 扫描 data/")
            return

        for deck_name, total, due in decks_info:
            due_count = int(due) if due else 0
            # 使用中文明确表示“待复习”，符合科学记忆曲线概念
            badge = f"待复习: {due_count}" if due_count > 0 else "已完成"
            self.deck_listbox.insert(
                tk.END,
                f"  {deck_name}  [{badge}]"
            )
            self._deck_names.append(deck_name)

    def _on_deck_selected(self, event):
        sel = self.deck_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._deck_names):
            return
        self.current_deck = self._deck_names[idx]
        self._update_status(f"已选中: {self.current_deck}")
        self._load_due_queue()

    # ─────────────── Card loading ───────────────
    def _load_due_queue(self):
        if not self.current_deck:
            return
        self.due_queue = self.engine.get_due_cards(limit=50, deck_name=self.current_deck)
        if self.due_queue:
            self._show_card_front(self.due_queue[0])
        else:
            self._show_empty()

    def _show_card_front(self, card):
        self.card_flipped = False
        self.lbl_card_word.config(text=card.word, fg=TEXT_PRIMARY)
        self.lbl_card_def.config(text="")
        self.lbl_card_ctx.config(text="")
        self.lbl_flip_hint.config(text="点击卡片 或 按 Space 翻转")
        self.card_frame.config(highlightbackground=ACCENT)
        self._show_rating_buttons(False)

        # play audio in background thread (non-blocking)
        threading.Thread(target=play_audio, args=(card.word,), daemon=True).start()

    def _flip_card(self):
        if not self.due_queue or self.card_flipped:
            return
        card = self.due_queue[0]
        self.card_flipped = True

        threading.Thread(target=play_audio, args=(card.word,), daemon=True).start()

        # Normalize text to replace full-width punctuation with half-width for better font compatibility
        def normalize(t):
            if not t: return ""
            return t.replace("：", ":").replace("“", "\"").replace("”", "\"").replace("（", "(").replace("）", ")")

        self.lbl_card_word.config(text=card.word, fg=ACCENT2)
        
        # Add "Definition" and "Context" headers just like in the TUI
        def_text = f"释义: {normalize(card.translation)}" if card.translation else ""
        self.lbl_card_def.config(text=def_text)
        
        ctx_text = f"语境:\n{normalize(card.context)}" if card.context else ""
        self.lbl_card_ctx.config(text=ctx_text)
        
        self.lbl_flip_hint.config(text="")
        self.card_frame.config(highlightbackground=ACCENT2)
        self._show_rating_buttons(True)

    def _on_card_click(self):
        if not self.due_queue:
            return
        if not self.card_flipped:
            self._flip_card()
        else:
            card = self.due_queue[0]
            threading.Thread(target=play_audio, args=(card.word,), daemon=True).start()

    def _show_empty(self):
        self.card_flipped = False
        self.lbl_card_word.config(
            text="Completed!\n已全部复习完！", fg=BTN_EASY
        )
        self.lbl_card_def.config(text="")
        self.lbl_card_ctx.config(text="任务完成了，明天继续")
        self.lbl_flip_hint.config(text="")
        self.card_frame.config(highlightbackground=BTN_EASY)
        self._show_rating_buttons(False)

    # ─────────────── Rating ───────────────
    def _rate(self, rating: int):
        if not self.due_queue or not self.card_flipped:
            return
        card = self.due_queue[0]
        self.engine.review_card(card, rating)
        self.due_queue.pop(0)

        if self.due_queue:
            self._show_card_front(self.due_queue[0])
        else:
            self._load_due_queue()

        self._load_decks()  # refresh due counts

    # ─────────────── Sync ───────────────
    def _sync(self):
        self._update_status("正在同步 data/ 目录...")
        def do_sync():
            md_parser.sync_data()
            self.root.after(0, self._after_sync)
        threading.Thread(target=do_sync, daemon=True).start()

    def _after_sync(self):
        self._load_decks()
        self._update_status("同步完成！")

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        if event.num == 4:
            self.deck_listbox.yview_scroll(-1, "units")
        elif event.num == 5:
            self.deck_listbox.yview_scroll(1, "units")
        else:
            self.deck_listbox.yview_scroll(int(-1*(event.delta/120)), "units")

    # ─────────────── Helpers ───────────────
    def _show_rating_buttons(self, visible: bool):
        if visible:
            self.btn_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.btn_frame.pack_forget()

    def _update_status(self, msg: str):
        self.lbl_status.config(text=msg)

    # ─────────────── Run ───────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MDFlashcardsGUI()
    app.run()
