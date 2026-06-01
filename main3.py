"""
╔═══════════════════════════════════════╗
║         GUESS IT! v1.0                ║
║   A Number Guessing Game              ║
║   Built with Python & Kivy            ║
║   Ready for Itch.io release           ║
╚═══════════════════════════════════════╝

Install Kivy first:
    pip install kivy

Then run:
    python main.py
"""

import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.progressbar import ProgressBar

Window.clearcolor = (0.04, 0.04, 0.08, 1)

# ── THEME ─────────────────────────────────────────────────────────────────────
T = {
    "bg":       (0.04, 0.04, 0.08, 1),
    "surface":  (0.08, 0.08, 0.16, 1),
    "card":     (0.11, 0.11, 0.22, 1),
    "border":   (0.20, 0.20, 0.35, 1),
    "primary":  (0.18, 0.85, 0.65, 1),   # cyan-mint
    "secondary":(0.98, 0.60, 0.10, 1),   # amber
    "danger":   (0.95, 0.28, 0.35, 1),   # red
    "purple":   (0.60, 0.35, 0.95, 1),   # purple accent
    "white":    (0.96, 0.96, 1.00, 1),
    "muted":    (0.45, 0.47, 0.62, 1),
    "dark_txt": (0.04, 0.04, 0.08, 1),
}

# ── WIDGETS ───────────────────────────────────────────────────────────────────

class GlowButton(Button):
    def __init__(self, bg=None, fg=None, radius=16, **kw):
        super().__init__(**kw)
        self._bg    = bg or T["primary"]
        self._fg    = fg or T["dark_txt"]
        self.radius = radius
        self.background_color  = (0,0,0,0)
        self.background_normal = ""
        self.color  = self._fg
        self.bold   = True
        self.font_size = dp(15)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            # shadow
            Color(0, 0, 0, 0.35)
            RoundedRectangle(
                pos=(self.x + dp(3), self.y - dp(3)),
                size=self.size, radius=[self.radius])
            # fill
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])

    def on_press(self):
        a = Animation(opacity=0.55, duration=0.07) + \
            Animation(opacity=1.00, duration=0.07)
        a.start(self)


class OutlineButton(Button):
    def __init__(self, color=None, radius=16, **kw):
        super().__init__(**kw)
        self._color = color or T["muted"]
        self.radius = radius
        self.background_color  = (0,0,0,0)
        self.background_normal = ""
        self.color  = self._color
        self.font_size = dp(14)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*T["card"])
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])
            Color(*self._color)
            Line(rounded_rectangle=(self.x, self.y,
                 self.width, self.height, self.radius), width=1.2)

    def on_press(self):
        a = Animation(opacity=0.5, duration=0.07) + \
            Animation(opacity=1.0, duration=0.07)
        a.start(self)


class Card(BoxLayout):
    def __init__(self, bg=None, radius=18, border=False, **kw):
        super().__init__(**kw)
        self._bg     = bg or T["card"]
        self._radius = radius
        self._border = border
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self._radius])
            if self._border:
                Color(*T["border"])
                Line(rounded_rectangle=(self.x, self.y,
                     self.width, self.height, self._radius), width=1)


class TryDot(Widget):
    """Single circular try indicator."""
    def __init__(self, filled=True, **kw):
        super().__init__(**kw)
        self.filled = filled
        self.size_hint = (None, None)
        self.size = (dp(14), dp(14))
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            if self.filled:
                Color(*T["primary"])
                Ellipse(pos=self.pos, size=self.size)
            else:
                Color(*T["border"])
                Ellipse(pos=self.pos, size=self.size)
                Color(*T["bg"])
                Ellipse(pos=(self.x+dp(2), self.y+dp(2)),
                        size=(dp(10), dp(10)))

    def set_state(self, filled):
        self.filled = filled
        self._draw()


# ── GAME STATE ────────────────────────────────────────────────────────────────

class State:
    DIFFICULTIES = {
        "Easy":   (20,  10),
        "Medium": (50,   7),
        "Hard":   (100,  5),
    }

    def __init__(self):
        self.total_score = 0
        self.rounds      = 0
        self.high_score  = 0
        self.reset()

    def reset(self, diff="Medium"):
        self.diff        = diff
        self.max_num, self.max_tries = self.DIFFICULTIES[diff]
        self.secret      = random.randint(1, self.max_num)
        self.tries       = 0
        self.history     = []
        self.won         = False

    def guess(self, n):
        self.tries += 1
        self.history.append(n)
        if n == self.secret:
            self.won   = True
            score      = max(100, 1000 - (self.tries-1)*(1000//self.max_tries))
            self.total_score += score
            self.rounds      += 1
            if score > self.high_score:
                self.high_score = score
            return "correct", score
        return ("low" if n < self.secret else "high"), 0

    @property
    def remaining(self):
        return self.max_tries - self.tries

    def proximity(self, n):
        d = abs(n - self.secret)
        if d == 0:          return "exact"
        if d <= self.max_num//10: return "hot"
        if d <= self.max_num//4:  return "warm"
        return "cold"


# ── SCREENS ───────────────────────────────────────────────────────────────────

class SplashScreen(Screen):
    """Animated splash / title screen."""
    def __init__(self, state, **kw):
        super().__init__(**kw)
        self.state = state
        self._build()

    def _build(self):
        root = FloatLayout()

        # BG grid lines decoration
        with root.canvas.before:
            Color(*T["border"], 0.3)

        content = BoxLayout(
            orientation='vertical',
            padding=(dp(40), dp(60)),
            spacing=dp(18),
            size_hint=(1, 1),
        )

        content.add_widget(Widget(size_hint_y=0.12))

        # Logo area
        logo = Label(
            text="🎯",
            font_size=dp(72),
            size_hint_y=None,
            height=dp(90),
        )
        content.add_widget(logo)

        title = Label(
            text="GUESS IT",
            font_size=dp(48),
            bold=True,
            color=T["primary"],
            size_hint_y=None,
            height=dp(60),
        )
        content.add_widget(title)

        tagline = Label(
            text="How sharp is your intuition?",
            font_size=dp(15),
            color=T["muted"],
            size_hint_y=None,
            height=dp(28),
        )
        content.add_widget(tagline)

        # version badge
        ver = Label(
            text="v 1.0",
            font_size=dp(11),
            color=T["border"],
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(ver)

        content.add_widget(Widget(size_hint_y=0.08))

        # Play button
        play_btn = GlowButton(
            text="▶   PLAY",
            bg=T["primary"],
            fg=T["dark_txt"],
            size_hint_y=None,
            height=dp(56),
            font_size=dp(18),
        )
        play_btn.bind(on_release=self._play)
        content.add_widget(play_btn)

        content.add_widget(Widget(size_hint_y=0.04))

        # Stats row
        self.stats_lbl = Label(
            text=self._stats_text(),
            font_size=dp(12),
            color=T["muted"],
            size_hint_y=None,
            height=dp(28),
        )
        content.add_widget(self.stats_lbl)
        content.add_widget(Widget(size_hint_y=0.1))

        # Credits
        credits = Label(
            text="Made with Python & Kivy",
            font_size=dp(11),
            color=T["border"],
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(credits)

        root.add_widget(content)
        self.add_widget(root)

        # Animate logo on load
        Clock.schedule_once(lambda dt: self._animate_logo(logo), 0.2)

    def _animate_logo(self, logo):
        a = (Animation(font_size=dp(80), duration=0.4) +
             Animation(font_size=dp(72), duration=0.3))
        a.repeat = False
        a.start(logo)

    def _stats_text(self):
        s = self.state
        if s.rounds == 0:
            return "No games played yet"
        avg = s.total_score // s.rounds
        return f"Best: {s.high_score} pts  •  Rounds: {s.rounds}  •  Avg: {avg}"

    def _play(self, *_):
        self.manager.transition = FadeTransition(duration=0.3)
        self.manager.current    = 'select'

    def on_pre_enter(self):
        self.stats_lbl.text = self._stats_text()


class SelectScreen(Screen):
    """Difficulty selection."""
    def __init__(self, state, **kw):
        super().__init__(**kw)
        self.state = state
        self._build()

    def _build(self):
        root = BoxLayout(
            orientation='vertical',
            padding=(dp(24), dp(30)),
            spacing=dp(14),
        )

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(44))
        back = OutlineButton(
            text="← Back",
            color=T["muted"],
            size_hint_x=None, width=dp(80),
        )
        back.bind(on_release=self._back)
        title = Label(
            text="SELECT DIFFICULTY",
            font_size=dp(13),
            bold=True,
            color=T["muted"],
        )
        hdr.add_widget(back)
        hdr.add_widget(title)
        root.add_widget(hdr)
        root.add_widget(Widget(size_hint_y=None, height=dp(10)))

        diffs = [
            ("🌿", "EASY",   "1 – 20",  "10 tries", T["primary"],  "Easy"),
            ("⚡", "MEDIUM", "1 – 50",  " 7 tries", T["secondary"],"Medium"),
            ("🔥", "HARD",   "1 – 100", " 5 tries", T["danger"],   "Hard"),
        ]

        for icon, name, rng, tries, color, key in diffs:
            card = self._diff_card(icon, name, rng, tries, color, key)
            root.add_widget(card)

        root.add_widget(Widget())

        tip = Label(
            text="💡 Fewer tries = higher score",
            font_size=dp(12),
            color=T["muted"],
            size_hint_y=None,
            height=dp(30),
        )
        root.add_widget(tip)
        self.add_widget(root)

    def _diff_card(self, icon, name, rng, tries, color, key):
        card = Card(
            orientation='horizontal',
            size_hint_y=None, height=dp(88),
            padding=(dp(18), dp(12)),
            spacing=dp(14),
            border=True,
        )

        # Icon
        ico = Label(
            text=icon,
            font_size=dp(32),
            size_hint_x=None,
            width=dp(44),
        )

        # Text block
        txt = BoxLayout(orientation='vertical', spacing=dp(4))
        nm  = Label(text=name, font_size=dp(18), bold=True,
                    color=color, halign='left')
        nm.bind(size=nm.setter('text_size'))
        sub = Label(text=f"{rng}  •  {tries}", font_size=dp(12),
                    color=T["muted"], halign='left')
        sub.bind(size=sub.setter('text_size'))
        txt.add_widget(nm)
        txt.add_widget(sub)

        # Arrow
        arr = Label(
            text="›",
            font_size=dp(28),
            color=color,
            size_hint_x=None,
            width=dp(28),
        )

        card.add_widget(ico)
        card.add_widget(txt)
        card.add_widget(arr)

        # Make whole card tappable
        btn = Button(
            background_color=(0,0,0,0),
            background_normal='',
        )
        btn.bind(on_release=lambda b, k=key: self._start(k))
        card.add_widget(btn)
        return card

    def _start(self, key):
        self.state.reset(key)
        self.manager.transition = FadeTransition(duration=0.25)
        self.manager.current    = 'game'

    def _back(self, *_):
        self.manager.transition = FadeTransition(duration=0.25)
        self.manager.current    = 'splash'


class GameScreen(Screen):
    def __init__(self, state, **kw):
        super().__init__(**kw)
        self.state = state
        self._build()

    def _build(self):
        root = BoxLayout(
            orientation='vertical',
            padding=(dp(20), dp(16)),
            spacing=dp(10),
        )

        # ── Top bar ──
        top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        back = OutlineButton(
            text="✕",
            color=T["muted"],
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            radius=21,
        )
        back.bind(on_release=self._quit)

        self.level_lbl = Label(
            text="",
            font_size=dp(13),
            bold=True,
            color=T["primary"],
        )
        self.score_lbl = Label(
            text="",
            font_size=dp(12),
            color=T["muted"],
            size_hint_x=None,
            width=dp(80),
            halign='right',
        )
        self.score_lbl.bind(size=self.score_lbl.setter('text_size'))
        top.add_widget(back)
        top.add_widget(self.level_lbl)
        top.add_widget(self.score_lbl)
        root.add_widget(top)

        # ── Range label ──
        self.range_lbl = Label(
            text="",
            font_size=dp(13),
            color=T["muted"],
            size_hint_y=None,
            height=dp(22),
        )
        root.add_widget(self.range_lbl)

        # ── Try dots ──
        self.dots_box = BoxLayout(
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8),
        )
        self.dots = []
        root.add_widget(self.dots_box)

        # ── Main feedback card ──
        fb_card = Card(
            orientation='vertical',
            size_hint_y=None,
            height=dp(130),
            padding=(dp(16), dp(12)),
            spacing=dp(6),
        )
        self.feedback_lbl = Label(
            text="Make your\nfirst guess!",
            font_size=dp(22),
            bold=True,
            color=T["white"],
            halign='center',
        )
        self.feedback_lbl.bind(size=self.feedback_lbl.setter('text_size'))

        self.prox_lbl = Label(
            text="",
            font_size=dp(26),
            size_hint_y=None,
            height=dp(40),
        )
        fb_card.add_widget(self.feedback_lbl)
        fb_card.add_widget(self.prox_lbl)
        root.add_widget(fb_card)

        # ── Input ──
        self.num_input = TextInput(
            hint_text="Type your guess here...",
            input_filter='int',
            font_size=dp(24),
            multiline=False,
            halign='center',
            background_color=T["card"],
            foreground_color=T["white"],
            hint_text_color=list(T["muted"]),
            cursor_color=list(T["primary"]),
            size_hint_y=None,
            height=dp(56),
            padding=(dp(12), dp(14)),
        )
        self.num_input.bind(on_text_validate=self._submit)
        root.add_widget(self.num_input)

        # ── Guess button ──
        self.guess_btn = GlowButton(
            text="GUESS  🎯",
            bg=T["primary"],
            fg=T["dark_txt"],
            size_hint_y=None,
            height=dp(52),
            font_size=dp(17),
        )
        self.guess_btn.bind(on_release=self._submit)
        root.add_widget(self.guess_btn)

        # ── History ──
        self.history_lbl = Label(
            text="",
            font_size=dp(11),
            color=T["muted"],
            size_hint_y=None,
            height=dp(24),
        )
        root.add_widget(self.history_lbl)

        root.add_widget(Widget())
        self.add_widget(root)

    def _rebuild_dots(self):
        self.dots_box.clear_widgets()
        self.dots = []
        s = self.state
        wrap = BoxLayout(
            size_hint_x=None,
            spacing=dp(8),
        )
        wrap.width = (dp(14) + dp(8)) * s.max_tries
        for i in range(s.max_tries):
            d = TryDot(filled=(i < s.remaining))
            self.dots.append(d)
            wrap.add_widget(d)
        # center it
        left  = Widget()
        right = Widget()
        self.dots_box.add_widget(left)
        self.dots_box.add_widget(wrap)
        self.dots_box.add_widget(right)

    def _update_dots(self):
        remaining = self.state.remaining
        for i, d in enumerate(self.dots):
            d.set_state(i < remaining)

    def on_pre_enter(self):
        s = self.state
        self.level_lbl.text  = f"🎮 {s.diff}"
        self.range_lbl.text  = f"Guess a number from 1 to {s.max_num}"
        self.score_lbl.text  = f"🏆 {s.total_score}"
        self.feedback_lbl.text = "Make your\nfirst guess!"
        self.feedback_lbl.color = T["white"]
        self.prox_lbl.text   = ""
        self.num_input.text  = ""
        self.history_lbl.text = ""
        self._rebuild_dots()

    def _submit(self, *_):
        txt = self.num_input.text.strip()
        if not txt:
            return
        try:
            n = int(txt)
        except ValueError:
            self._flash("Numbers only!", T["danger"])
            return

        s = self.state
        if n < 1 or n > s.max_num:
            self._flash(f"Stay between 1 and {s.max_num}!", T["danger"])
            return

        result, score = s.guess(n)
        self.num_input.text = ""
        self._update_dots()

        prox_map = {
            "exact": "🎯 Perfect!",
            "hot":   "🔥🔥 So close!",
            "warm":  "🌡️  Getting warm",
            "cold":  "🧊 Ice cold",
        }
        self.prox_lbl.text = prox_map.get(s.proximity(n), "")

        hist = "  ›  ".join(str(h) for h in s.history[-7:])
        self.history_lbl.text = hist

        if result == "correct":
            self.manager.get_screen('result').prepare(True, score)
            self.manager.transition = FadeTransition(duration=0.3)
            self.manager.current    = 'result'
        elif result == "low":
            self._flash(f"{n}  ▲  Higher!", T["primary"])
            if s.remaining == 0: self._end()
        else:
            self._flash(f"{n}  ▼  Lower!", T["secondary"])
            if s.remaining == 0: self._end()

    def _flash(self, text, color):
        self.feedback_lbl.text  = text
        self.feedback_lbl.color = color
        a = Animation(opacity=0.4, duration=0.1) + \
            Animation(opacity=1.0, duration=0.1)
        a.start(self.feedback_lbl)

    def _end(self):
        self.manager.get_screen('result').prepare(False, 0)
        self.manager.transition = FadeTransition(duration=0.3)
        self.manager.current    = 'result'

    def _quit(self, *_):
        self.manager.transition = FadeTransition(duration=0.25)
        self.manager.current    = 'splash'


class ResultScreen(Screen):
    def __init__(self, state, **kw):
        super().__init__(**kw)
        self.state = state
        self._build()

    def _build(self):
        root = BoxLayout(
            orientation='vertical',
            padding=(dp(30), dp(40)),
            spacing=dp(16),
        )

        self.emoji_lbl = Label(
            text="", font_size=dp(72),
            size_hint_y=None, height=dp(90),
        )
        self.title_lbl = Label(
            text="", font_size=dp(32), bold=True,
            color=T["white"],
            size_hint_y=None, height=dp(50),
        )
        self.secret_lbl = Label(
            text="", font_size=dp(14),
            color=T["muted"],
            size_hint_y=None, height=dp(26),
        )

        # Score card
        score_card = Card(
            orientation='vertical',
            size_hint_y=None, height=dp(100),
            padding=(dp(16), dp(10)),
            spacing=dp(4),
        )
        score_hdr = Label(
            text="SCORE EARNED",
            font_size=dp(11),
            bold=True,
            color=T["muted"],
            size_hint_y=None,
            height=dp(22),
        )
        self.score_lbl = Label(
            text="", font_size=dp(42), bold=True,
            color=T["primary"],
        )
        score_card.add_widget(score_hdr)
        score_card.add_widget(self.score_lbl)

        self.stats_lbl = Label(
            text="", font_size=dp(12),
            color=T["muted"],
            size_hint_y=None, height=dp(26),
        )

        root.add_widget(Widget(size_hint_y=0.04))
        root.add_widget(self.emoji_lbl)
        root.add_widget(self.title_lbl)
        root.add_widget(self.secret_lbl)
        root.add_widget(Widget(size_hint_y=None, height=dp(8)))
        root.add_widget(score_card)
        root.add_widget(self.stats_lbl)
        root.add_widget(Widget())

        # Buttons
        again_btn = GlowButton(
            text="🔄  PLAY AGAIN",
            bg=T["primary"], fg=T["dark_txt"],
            size_hint_y=None, height=dp(54),
            font_size=dp(16),
        )
        again_btn.bind(on_release=self._again)

        menu_btn = OutlineButton(
            text="🏠  MAIN MENU",
            color=T["muted"],
            size_hint_y=None, height=dp(48),
        )
        menu_btn.bind(on_release=self._menu)

        root.add_widget(again_btn)
        root.add_widget(Widget(size_hint_y=None, height=dp(8)))
        root.add_widget(menu_btn)
        root.add_widget(Widget(size_hint_y=0.04))

        self.add_widget(root)

    def prepare(self, won, score):
        s = self.state
        if won:
            self.emoji_lbl.text  = "🏆"
            self.title_lbl.text  = "YOU GOT IT!"
            self.title_lbl.color = T["primary"]
            self.secret_lbl.text = (
                f"The number was {s.secret}  •  "
                f"{s.tries} {'try' if s.tries==1 else 'tries'}"
            )
            self.score_lbl.text  = f"+{score}"
            self.score_lbl.color = T["primary"]
        else:
            self.emoji_lbl.text  = "💀"
            self.title_lbl.text  = "GAME OVER"
            self.title_lbl.color = T["danger"]
            self.secret_lbl.text = f"The number was {s.secret}"
            self.score_lbl.text  = "+0"
            self.score_lbl.color = T["danger"]

        avg = s.total_score // s.rounds if s.rounds else 0
        self.stats_lbl.text = (
            f"Total: {s.total_score} pts  •  "
            f"Best: {s.high_score} pts  •  "
            f"Rounds: {s.rounds}"
        )

    def _again(self, *_):
        s = self.state
        s.reset(s.diff)
        self.manager.transition = FadeTransition(duration=0.25)
        self.manager.current    = 'game'

    def _menu(self, *_):
        self.manager.transition = FadeTransition(duration=0.25)
        self.manager.current    = 'splash'


# ── APP ───────────────────────────────────────────────────────────────────────

class GuessItApp(App):
    def build(self):
        self.title = "Guess It!"
        state = State()
        sm    = ScreenManager()
        sm.add_widget(SplashScreen(state,  name='splash'))
        sm.add_widget(SelectScreen(state,  name='select'))
        sm.add_widget(GameScreen(state,    name='game'))
        sm.add_widget(ResultScreen(state,  name='result'))
        return sm


if __name__ == "__main__":
    GuessItApp().run()
