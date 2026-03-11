from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label, ListItem, ListView
from textual.reactive import reactive
from textual.binding import Binding

from fsrs_engine import FSRSEngine
from audio import play_audio
from database import Card
import parser

class FlashcardMain(Vertical):
    """显示单词正面和背面的组件"""
    card_state = reactive("front")  # "front", "back", "empty"
    current_card = None
    
    def compose(self) -> ComposeResult:
        yield Static("请在左侧选择一个牌组开始...", id="card-content")
        with Horizontal(id="rating-buttons", classes="hidden"):
            yield Button("1 (Again)", id="rate_1", variant="error")
            yield Button("2 (Hard)", id="rate_2", variant="warning")
            yield Button("3 (Good)", id="rate_3", variant="primary")
            yield Button("4 (Easy)", id="rate_4", variant="success")

    def show_empty(self, msg="[b]🎉 当前牌组已空！[/b]\n\n没有需要复习的卡片了。"):
        self.card_state = "empty"
        self.current_card = None
        content = self.query_one("#card-content", Static)
        content.update(msg)
        self.query_one("#rating-buttons").add_class("hidden")

    def show_card(self, card: Card):
        self.current_card = card
        self.card_state = "front"
        play_audio(card.word)
        content = self.query_one("#card-content", Static)
        content.update(f"[b]{card.word}[/b]")
        self.query_one("#rating-buttons").add_class("hidden")

    def flip_card(self):
        if self.card_state == "front" and self.current_card:
            self.card_state = "back"
            content = self.query_one("#card-content", Static)
            md_text = f"# {self.current_card.word}\n\n"
            md_text += f"**释义:** {self.current_card.translation}\n\n"
            if self.current_card.context:
                md_text += f"**语境:** {self.current_card.context}\n"
            content.update(md_text)
            self.query_one("#rating-buttons").remove_class("hidden")
            play_audio(self.current_card.word)

class MDFlashcardsApp(App):
    """MD-Flashcards 终端应用主体"""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 35;
        dock: left;
        background: $panel;
        border-right: solid $primary;
        padding: 1;
    }
    #main-area {
        width: 1fr;
        padding: 2;
        align: center middle;
    }
    #card-content {
        width: 100%;
        height: 1fr;
        content-align: center middle;
        padding: 2;
        border: round $secondary;
        background: $surface;
    }
    #rating-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    Button { margin: 0 1; }
    .hidden { display: none; }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("space", "flip", "翻转卡片"),
        Binding("enter", "flip", "翻转卡片", show=False),
        Binding("s", "sync", "扫描 data/ 本地笔记同步库"),
        Binding("1", "rate(1)", "重来", show=False),
        Binding("2", "rate(2)", "困难", show=False),
        Binding("3", "rate(3)", "良好", show=False),
        Binding("4", "rate(4)", "容易", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.engine = FSRSEngine()
        self.due_queue = []
        self.current_deck = None  # 当前选中的牌组

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="sidebar"):
            yield Label("📚 [b]Decks[/b]", classes="p-1")
            yield ListView(id="deck-list")
        with Container(id="main-area"):
            yield FlashcardMain(id="flashcard-main")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_deck_list()

    def refresh_deck_list(self):
        """刷新侧边栏的牌组列表并获取所有牌组"""
        deck_list = self.query_one("#deck-list", ListView)
        deck_list.clear()
        
        decks_info = self.engine.get_all_decks_info()
        if not decks_info:
            deck_list.append(ListItem(Label("未找到任何牌组。请将 md 放入 data/ 文件夹后按 s 扫描。"), id="empty-deck"))
        else:
            for deck_name, count, due in decks_info:
                due_count = int(due) if due is not None else 0
                label_text = f"📂 {deck_name}\n(总:{count} | 待复习:[bold red]{due_count}[/])" if due_count > 0 else f"📂 {deck_name}\n(总:{count} | 待复习:[green]0[/])"
                deck_list.append(ListItem(Label(label_text), name=deck_name))

    def on_list_view_selected(self, event: ListView.Selected):
        """当用户在侧边栏点击或回车选中某个牌组时触发"""
        if event.item.id == "empty-deck":
            return
            
        self.current_deck = getattr(event.item, 'name', None)
        if self.current_deck:
            self.notify(f"已选中牌组: {self.current_deck}", severity="information")
            self.load_due_queue()

    def load_due_queue(self):
        """加载已选中牌组到期的卡片"""
        if not self.current_deck:
            return
            
        self.due_queue = self.engine.get_due_cards(limit=50, deck_name=self.current_deck)
        main_view = self.query_one("#flashcard-main", FlashcardMain)
        
        if self.due_queue:
            main_view.show_card(self.due_queue[0])
        else:
            main_view.show_empty()

    def action_flip(self) -> None:
        main_view = self.query_one("#flashcard-main", FlashcardMain)
        if main_view.card_state == "front":
            main_view.flip_card()

    def on_static_clicked(self, event) -> None:
        """点击卡片内容区域时翻转或重新发音"""
        if event.widget.id == "card-content":
            main_view = self.query_one("#flashcard-main", FlashcardMain)
            if main_view.card_state == "front":
                self.action_flip()
            elif main_view.card_state == "back" and main_view.current_card:
                play_audio(main_view.current_card.word)

    def action_sync(self) -> None:
        self.notify("正在扫描 data/ 目录的新 md 文件...", title="同步中", severity="information")
        parser.sync_data()
        self.notify("解析完毕！请在左侧重新选中牌组刷新加载", title="成功", severity="information")
        self.refresh_deck_list()

    def action_rate(self, rating: int) -> None:
        main_view = self.query_one("#flashcard-main", FlashcardMain)
        if main_view.card_state != "back" or not main_view.current_card:
            return
            
        self.engine.review_card(main_view.current_card, rating)
        
        if self.due_queue:
            self.due_queue.pop(0)
            
        if self.due_queue:
            main_view.show_card(self.due_queue[0])
        else:
            self.load_due_queue()
            
        # 评分完成后，刷新侧边栏的待复习数字
        self.refresh_deck_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理鼠标点击评分按钮的事件"""
        button_id = event.button.id
        if button_id and button_id.startswith("rate_"):
            rating = int(button_id.split("_")[1])
            self.action_rate(rating)

if __name__ == "__main__":
    app = MDFlashcardsApp()
    app.run()
