# main.py
import random
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

Window.clearcolor = (0.05, 0.05, 0.1, 1)  # dark blue background

KV = """
ScreenManager:
    MenuScreen:
        name: "menu"
    GameScreen:
        name: "game"
    GameOverScreen:
        name: "gameover"

<MenuScreen>:
    FloatLayout:
        Label:
            text: "DODGE!"
            font_size: "48sp"
            size_hint: None, None
            pos_hint: {"center_x":0.5, "top":0.9}
        Button:
            text: "Start Game"
            size_hint: 0.6, 0.12
            pos_hint: {"center_x":0.5, "center_y":0.6}
            on_release: app.start_game()
        BoxLayout:
            size_hint: 0.6, 0.12
            pos_hint: {"center_x":0.5, "center_y":0.45}
            spacing: 8
            ToggleButton:
                id: autoplay_toggle
                text: "Auto-Play: OFF"
                state: "normal"
                on_state:
                    root.set_autoplay(self.state == "down"); self.text = "Auto-Play: ON" if self.state == "down" else "Auto-Play: OFF"
            Button:
                text: "Exit"
                on_release: app.stop()
        Label:
            text: "Move with touch (or Auto-Play)"
            font_size: "12sp"
            size_hint: None, None
            pos_hint: {"center_x":0.5, "y":0.05}

<GameScreen>:
    FloatLayout:
        id: game_area
        GameField:
            id: gamefield
            size_hint: 1, 1
        Label:
            id: score_label
            text: "Score: 0"
            size_hint: None, None
            pos_hint: {"x":0.02, "top":0.98}
            font_size: "18sp"
        Button:
            id: pause_btn
            text: "Pause"
            size_hint: 0.18, 0.08
            pos_hint: {"right":0.98, "top":0.98}
            on_release: root.toggle_pause()
        ToggleButton:
            id: agent_btn
            text: "Agent: OFF"
            size_hint: 0.28, 0.08
            pos_hint: {"right":0.98, "top":0.88}
            on_state: root.set_autoplay(self.state == "down"); self.text = "Agent: ON" if self.state == "down" else "Agent: OFF"

<GameOverScreen>:
    FloatLayout:
        Label:
            id: final_label
            text: "Game Over"
            font_size: "36sp"
            pos_hint: {"center_x":0.5, "top":0.85}
        Label:
            id: score_final
            text: "Final: 0"
            font_size: "22sp"
            pos_hint: {"center_x":0.5, "top":0.68}
        Button:
            text: "Restart"
            size_hint: 0.6, 0.12
            pos_hint: {"center_x":0.5, "center_y":0.48}
            on_release: app.start_game()
        Button:
            text: "Main Menu"
            size_hint: 0.6, 0.12
            pos_hint: {"center_x":0.5, "center_y":0.32}
            on_release: app.goto_menu()
"""

# ---------- Game widgets ----------
class Player(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 1, 0)  # green
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class Enemy(Widget):
    speed = NumericProperty(3)
    color_val = ListProperty([1, 0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(*self.color_val)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def move(self):
        self.y -= self.speed

class GameField(Widget):
    player = None
    enemies = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Player
        self.player = Player(size=(60, 60))
        self.player.center_x = self.width / 2
        self.player.y = 20
        self.add_widget(self.player)

    def on_size(self, *args):
        if self.player:
            if self.player.center_x == 0:
                self.player.center_x = self.center_x
            self.player.y = 20

    def spawn_enemy(self):
        w = random.randint(40, 80)
        e = Enemy(size=(w, w), color_val=[random.random(), random.random(), random.random()])
        e.x = random.randint(0, int(self.width - w))
        e.y = self.height + 10
        self.add_widget(e)
        self.enemies.append(e)
        return e

    def clear_enemies(self):
        for e in list(self.enemies):
            if e.parent:
                self.remove_widget(e)
        self.enemies = []

# ---------- Screens ----------
class MenuScreen(Screen):
    def set_autoplay(self, enabled):
        App.get_running_app().auto_play_default = enabled

class GameScreen(Screen):
    score = NumericProperty(0)
    running = BooleanProperty(False)
    auto_play = BooleanProperty(False)

    def on_enter(self):
        gf = self.ids.gamefield
        gf.clear_enemies()
        gf.player.size = (60, 60)
        gf.player.center_x = gf.center_x
        gf.player.y = 20
        self.score = 0
        self.ids.score_label.text = f"Score: {self.score}"
        self.running = True
        self.auto_play = App.get_running_app().auto_play_default
        self.ids.agent_btn.state = "down" if self.auto_play else "normal"
        self._update_event = Clock.schedule_interval(self.update, 1/60)
        self._spawn_event = Clock.schedule_interval(self._spawn_loop, 1.2)
        Clock.schedule_once(lambda dt: self._maybe_spawn_initial(), 0.2)

    def _maybe_spawn_initial(self):
        for _ in range(random.randint(1,2)):
            e = self.ids.gamefield.spawn_enemy()
            e.speed = random.uniform(2.5, 4.0)

    def on_leave(self):
        if hasattr(self, "_update_event"): self._update_event.cancel()
        if hasattr(self, "_spawn_event"): self._spawn_event.cancel()

    def _spawn_loop(self, dt):
        gf = self.ids.gamefield
        e = gf.spawn_enemy()
        base = 2.5 + min(6.0, self.score / 10.0)
        e.speed = random.uniform(base, base + 2.0)

    def toggle_pause(self):
        if not self.running:
            return
        if getattr(self, "_paused", False):
            self._update_event = Clock.schedule_interval(self.update, 1/60)
            self._spawn_event = Clock.schedule_interval(self._spawn_loop, 1.2)
            self._paused = False
            self.ids.pause_btn.text = "Pause"
        else:
            self._update_event.cancel()
            self._spawn_event.cancel()
            self._paused = True
            self.ids.pause_btn.text = "Resume"

    def set_autoplay(self, enabled):
        self.auto_play = enabled

    def update(self, dt):
        gf = self.ids.gamefield
        for e in list(gf.enemies):
            e.move()
            if e.y < -e.height - 20:
                if e.parent: gf.remove_widget(e)
                if e in gf.enemies: gf.enemies.remove(e)
                self.score += 1
                self.ids.score_label.text = f"Score: {self.score}"

        if self.auto_play:
            self._agent_move(dt)

        for e in list(gf.enemies):
            if gf.player.collide_widget(e):
                self.game_over()
                return

    def _agent_move(self, dt):
        gf = self.ids.gamefield
        player = gf.player
        if not gf.enemies: return
        threat = min(gf.enemies, key=lambda en: en.y)
        if threat.speed <= 0: return
        time_to_player = (threat.y - player.y) / threat.speed if threat.y > player.y else 0
        horiz_dist = threat.center_x - player.center_x
        danger = abs(horiz_dist) < (player.width / 2 + threat.width / 2 + 15) and 0 < time_to_player < 2.5
        step = max(6.0, (10.0 + self.score * 0.1) * dt * 60)
        if danger:
            if horiz_dist > 0:
                player.center_x = max(player.width/2, player.center_x - step)
            else:
                player.center_x = min(gf.width - player.width/2, player.center_x + step)
        else:
            center = gf.width / 2
            if abs(player.center_x - center) > 6:
                if player.center_x < center:
                    player.center_x = min(center, player.center_x + step)
                else:
                    player.center_x = max(center, player.center_x - step)

    def on_touch_move(self, touch):
        if self.auto_play: return
        gf = self.ids.gamefield
        if gf.collide_point(*touch.pos):
            pf = gf.player
            pf.center_x = max(pf.width/2, min(gf.width - pf.width/2, touch.x))

    def game_over(self):
        self.running = False
        if hasattr(self, "_update_event"): self._update_event.cancel()
        if hasattr(self, "_spawn_event"): self._spawn_event.cancel()
        gs = self.manager.get_screen("gameover")
        gs.ids.score_final.text = f"Final: {self.score}"
        self.manager.current = "gameover"

class GameOverScreen(Screen):
    pass

# ---------- App ----------
class DodgeApp(App):
    auto_play_default = False

    def build(self):
        sm = Builder.load_string(KV)
        return sm

    def start_game(self):
        self.root.current = "game"

    def goto_menu(self):
        self.root.current = "menu"

if __name__ == "__main__":
    DodgeApp().run()