import math
import sys
import os
from typing import Optional

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prng import *

WIDTH = 900
HEIGHT = 700
FPS = 60
TARGET_STREAK = 5
COIN_RADIUS = 85
COIN_CENTER = (WIDTH // 2, 280)


class Colors:
    BG = (28, 28, 38)
    SURFACE = (40, 40, 55)
    SURFACE_HOVER = (55, 55, 72)
    WHITE = (245, 245, 245)
    BLACK = (20, 20, 20)
    GOLD = (255, 215, 0)
    GOLD_SHADOW = (180, 150, 0)
    SILVER = (210, 210, 215)
    SILVER_SHADOW = (150, 150, 155)
    GREEN = (60, 220, 80)
    RED = (230, 60, 60)
    GRAY = (130, 130, 145)
    DIM = (80, 80, 95)
    ACCENT = (100, 160, 255)
    ACCENT_DARK = (60, 110, 200)
    YELLOW = (255, 230, 80)
    INPUT_BG = (25, 25, 35)


def make_prng(name: str, seed: int, params: Optional[dict] = None) -> PRNG:
    if name == "LCG":
        if params:
            return LCG(params["m"], params["a"], params["c"], seed)
        return LCG(2**31, 1103515245, 12345, seed)
    return MiddleSquare(seed)


def _parse_int(text: str) -> Optional[int]:
    try:
        return int(text)
    except ValueError:
        return None


class Label:
    def __init__(
        self, text: str, size: int, color, x: int, y: int, center: bool = True
    ):
        self.text = text
        self.size = size
        self.color = color
        self.x = x
        self.y = y
        self.center = center

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.Font(None, self.size)
        img = font.render(self.text, True, self.color)
        rect = img.get_rect()
        if self.center:
            rect.center = (self.x, self.y)
        else:
            rect.topleft = (self.x, self.y)
        surface.blit(img, rect)


class Button:
    def __init__(self, rect, text, color=None, hover_color=None, text_color=None):
        self.rect = rect
        self.text = text
        self.color = color or Colors.SURFACE
        self.hover_color = hover_color or Colors.SURFACE_HOVER
        self.text_color = text_color or Colors.WHITE
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        c = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        pygame.draw.rect(surface, Colors.DIM, self.rect, 2, border_radius=8)
        font = pygame.font.Font(None, 30)
        img = font.render(self.text, True, self.text_color)
        surface.blit(img, img.get_rect(center=self.rect.center))


class InputField:
    def __init__(self, rect, label, default="", numeric=True):
        self.rect = rect
        self.label = label
        self.text = str(default)
        self.numeric = numeric
        self.focused = False
        self.cursor_timer = 0
        self.cursor_visible = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                self.focused = False
            else:
                char = event.unicode
                if self.numeric:
                    if char.isdigit():
                        self.text += char
                elif char.isprintable():
                    self.text += char

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface):
        font = pygame.font.Font(None, 22)
        label_img = font.render(self.label, True, Colors.GRAY)
        surface.blit(label_img, (self.rect.x, self.rect.y - 26))

        pygame.draw.rect(surface, Colors.INPUT_BG, self.rect, border_radius=4)
        border_color = Colors.ACCENT if self.focused else Colors.DIM
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=4)

        font2 = pygame.font.Font(None, 28)
        text_img = font2.render(self.text, True, Colors.WHITE)
        text_rect = text_img.get_rect(midleft=(self.rect.x + 8, self.rect.centery))
        surface.blit(text_img, text_rect)

        if self.focused and self.cursor_visible:
            cx = text_rect.right + 2
            pygame.draw.line(
                surface,
                Colors.WHITE,
                (cx, self.rect.y + 6),
                (cx, self.rect.bottom - 6),
                2,
            )

    def value(self):
        return _parse_int(self.text)


class Toggle:
    def __init__(self, rect, options, default=0):
        self.rect = rect
        self.options = options
        self.selected = default
        self.btn_w = rect.width // len(options)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.options)):
                r = pygame.Rect(
                    self.rect.x + i * self.btn_w,
                    self.rect.y,
                    self.btn_w,
                    self.rect.height,
                )
                if r.collidepoint(event.pos):
                    self.selected = i
                    return True
        return False

    def draw(self, surface):
        for i in range(len(self.options)):
            r = pygame.Rect(
                self.rect.x + i * self.btn_w, self.rect.y, self.btn_w, self.rect.height
            )
            if i == self.selected:
                pygame.draw.rect(surface, Colors.ACCENT_DARK, r, border_radius=8)
                pygame.draw.rect(surface, Colors.ACCENT, r, 2, border_radius=8)
            else:
                pygame.draw.rect(surface, Colors.SURFACE, r, border_radius=8)
                pygame.draw.rect(surface, Colors.DIM, r, 2, border_radius=8)

            font = pygame.font.Font(None, 26)
            c = Colors.WHITE if i == self.selected else Colors.GRAY
            img = font.render(self.options[i], True, c)
            surface.blit(img, img.get_rect(center=r.center))

    def value(self):
        return self.options[self.selected]


class Coin:
    def __init__(self, x: int, y: int, radius: int):
        self.x = x
        self.y = y
        self.radius = radius
        self.face: Flip = Flip.HEADS
        self.scale_x: float = 1.0
        self.animating: bool = False
        self.frame: int = 0
        self.duration: int = 45
        self.result_face: Flip = Flip.HEADS

    def start_flip(self, result: Flip) -> None:
        self.result_face = result
        self.face = Flip.HEADS
        self.scale_x = 1.0
        self.animating = True
        self.frame = 0

    def update(self) -> None:
        if not self.animating:
            return
        self.frame += 1
        t = self.frame / self.duration
        cos_a = math.cos(t * math.pi * 7)
        self.scale_x = abs(cos_a)
        self.face = Flip.HEADS if cos_a >= 0 else Flip.TAILS
        if self.frame >= self.duration:
            self.animating = False
            self.scale_x = 1.0
            self.face = self.result_face

    def draw(self, surface: pygame.Surface) -> None:
        r = self.radius
        w = max(2, int(r * 2 * self.scale_x))
        h = r * 2
        rect = pygame.Rect(self.x - w // 2, self.y - h // 2, w, h)

        color = Colors.GOLD if self.face == Flip.HEADS else Colors.SILVER
        border = Colors.GOLD_SHADOW if self.face == Flip.HEADS else Colors.SILVER_SHADOW

        shadow = pygame.Rect(self.x - w // 2 + 5, self.y - h // 2 + 5, w, h)
        pygame.draw.ellipse(surface, (0, 0, 0, 60), shadow)

        pygame.draw.ellipse(surface, color, rect)
        pygame.draw.ellipse(surface, border, rect, 3)
        inner = rect.inflate(-12, -12)
        if inner.width > 4 and inner.height > 4:
            pygame.draw.ellipse(surface, border, inner, 2)

        if w > 24:
            fs = max(20, min(72, int(r * 0.75)))
            font = pygame.font.Font(None, fs)
            label = "H" if self.face == Flip.HEADS else "T"
            img = font.render(label, True, Colors.BLACK)
            if self.animating:
                tw = max(1, int(img.get_width() * self.scale_x))
                img = pygame.transform.scale(img, (tw, img.get_height()))
            surface.blit(img, img.get_rect(center=(self.x, self.y)))


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        cx = WIDTH // 2
        btn_w, btn_h = 260, 55
        y0 = 300
        gap = 70
        self.buttons = [
            Button(pygame.Rect(cx - btn_w // 2, y0, btn_w, btn_h), "Play"),
            Button(
                pygame.Rect(cx - btn_w // 2, y0 + gap, btn_w, btn_h),
                "AI Play",
                text_color=Colors.GRAY,
            ),
            Button(pygame.Rect(cx - btn_w // 2, y0 + gap * 2, btn_w, btn_h), "Quit"),
        ]
        self.ai_toast = 0

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                return ("quit", None)
            for i, btn in enumerate(self.buttons):
                if btn.handle_event(e):
                    if i == 0:
                        return ("config", None)
                    if i == 1:
                        self.ai_toast = 90
                    if i == 2:
                        return ("quit", None)
        return ("continue", None)

    def update(self):
        if self.ai_toast > 0:
            self.ai_toast -= 1

    def draw(self):
        self.screen.fill(Colors.BG)
        Label("PRNG Abuse", 72, Colors.WHITE, WIDTH // 2, 180).draw(self.screen)
        Label("Coin Flip Game", 28, Colors.GRAY, WIDTH // 2, 230).draw(self.screen)
        for btn in self.buttons:
            btn.draw(self.screen)
        if self.ai_toast > 0:
            Label("Coming soon!", 26, Colors.YELLOW, WIDTH // 2, 560).draw(self.screen)


class ConfigScreen:
    def __init__(self, screen):
        self.screen = screen
        cx = WIDTH // 2
        field_w, field_h = 240, 36

        self.type_toggle = Toggle(
            pygame.Rect(cx - 160, 240, 320, 44), ["Middle Square", "LCG"]
        )

        self.seed_field = InputField(
            pygame.Rect(cx - field_w // 2, 310, field_w, field_h), "Seed", "675248"
        )
        self.m_field = InputField(
            pygame.Rect(cx - field_w // 2, 390, field_w, field_h),
            "Modulus (m)",
            "2147483648",
        )
        self.a_field = InputField(
            pygame.Rect(cx - field_w // 2, 450, field_w, field_h),
            "Multiplier (a)",
            "1103515245",
        )
        self.c_field = InputField(
            pygame.Rect(cx - field_w // 2, 510, field_w, field_h),
            "Increment (c)",
            "12345",
        )
        self.fields = [self.seed_field, self.m_field, self.a_field, self.c_field]
        self.error = ""

        btn_w, btn_h = 180, 50
        self.start_btn = Button(
            pygame.Rect(cx - btn_w - 15, 590, btn_w, btn_h),
            "Start",
            Colors.GREEN,
            (80, 240, 100),
            Colors.BLACK,
        )
        self.back_btn = Button(
            pygame.Rect(cx + 15, 590, btn_w, btn_h),
            "Back",
            Colors.SURFACE,
            Colors.SURFACE_HOVER,
            Colors.WHITE,
        )

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                return ("quit", None)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                for i, f in enumerate(self.fields):
                    if f.focused:
                        f.focused = False
                        self.fields[(i + 1) % len(self.fields)].focused = True
                        break
            for f in self.fields:
                f.handle_event(e)
            self.type_toggle.handle_event(e)
            if self.start_btn.handle_event(e):
                return self._try_start()
            if self.back_btn.handle_event(e):
                return ("menu", None)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                return self._try_start()
        return ("continue", None)

    def _try_start(self):
        seed = self.seed_field.value()
        if seed is None or seed <= 0:
            self.error = "Seed must be a positive integer"
            return ("continue", None)
        prng_type = self.type_toggle.value()
        params = None
        if prng_type == "LCG":
            m = self.m_field.value()
            a = self.a_field.value()
            c = self.c_field.value()
            if m is None or a is None or c is None or m <= 0 or a <= 0 or c <= 0:
                self.error = "All LCG parameters must be positive integers"
                return ("continue", None)
            params = {"m": m, "a": a, "c": c}
        self.error = ""
        return ("start_game", {"type": prng_type, "seed": seed, "params": params})

    def update(self):
        for f in self.fields:
            f.update()

    def draw(self):
        self.screen.fill(Colors.BG)

        panel = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
        pygame.draw.rect(self.screen, Colors.SURFACE, panel, border_radius=12)
        pygame.draw.rect(self.screen, Colors.DIM, panel, 2, border_radius=12)

        Label("Configure PRNG", 48, Colors.WHITE, WIDTH // 2, 65).draw(self.screen)
        Label("PRNG Type", 24, Colors.GRAY, WIDTH // 2, 210).draw(self.screen)
        self.type_toggle.draw(self.screen)
        self.seed_field.draw(self.screen)

        is_lcg = self.type_toggle.value() == "LCG"
        if is_lcg:
            self.m_field.draw(self.screen)
            self.a_field.draw(self.screen)
            self.c_field.draw(self.screen)
        else:
            y = 400
            Label("LCG-specific fields not needed", 20, Colors.DIM, WIDTH // 2, y).draw(
                self.screen
            )
            Label("for Middle Square PRNG", 20, Colors.DIM, WIDTH // 2, y + 25).draw(
                self.screen
            )

        if self.error:
            Label(self.error, 22, Colors.RED, WIDTH // 2, 560).draw(self.screen)

        self.start_btn.draw(self.screen)
        self.back_btn.draw(self.screen)


class Game:
    def __init__(self, screen, clock, prng_type, seed, params=None):
        self.screen = screen
        self.clock = clock
        self.prng = make_prng(prng_type, seed, params)
        self.prng_name = prng_type
        self.seed = seed
        self.params = params

        self.streak = 0
        self.total_flips = 0
        self.skip_count = 0
        self.last_result: Optional[Flip] = None
        self.last_guess: Optional[Flip] = None
        self.message = ""
        self.won = False
        self.state = "idle"

        self.coin = Coin(*COIN_CENTER, COIN_RADIUS)

    def reset(self):
        self.streak = 0
        self.total_flips = 0
        self.skip_count = 0
        self.last_result = None
        self.last_guess = None
        self.message = ""
        self.won = False
        self.prng.reset(self.seed)
        self.state = "idle"

    def _advance_prng(self, n):
        for _ in range(n):
            self.prng.next_value

    def guess(self, side):
        self.last_guess = side
        self._advance_prng(self.skip_count)
        result = self.prng.current_flip
        print(self.prng.current_seed)
        self.last_result = result
        self.coin.start_flip(result)
        self.state = "flipping"

    def handle(self, event):
        if event.type == pygame.QUIT:
            return ("quit", None)
        if event.type != pygame.KEYDOWN:
            return ("continue", None)
        if event.key == pygame.K_ESCAPE and self.state != "flipping":
            return ("menu", None)
        if self.state == "flipping":
            return ("continue", None)
        if event.key == pygame.K_r and self.won:
            self.reset()
            return ("continue", None)
        if self.won:
            return ("continue", None)
        if event.key == pygame.K_h:
            self.guess(Flip.HEADS)
        elif event.key == pygame.K_t:
            self.guess(Flip.TAILS)
        elif event.key == pygame.K_UP:
            self.skip_count += 1
        elif event.key == pygame.K_DOWN:
            self.skip_count = max(0, self.skip_count - 1)
        return ("continue", None)

    def update(self):
        self.coin.update()
        if self.state == "flipping" and not self.coin.animating:
            if self.last_guess == self.last_result:
                self.streak += 1
                self.message = "Correct!"
                if self.streak >= TARGET_STREAK:
                    self.won = True
                    self.message = "You win!  Press R to restart"
            else:
                self.streak = 0
                self.message = "Wrong!"
            self.total_flips += 1
            self.state = "result"

    def draw(self):
        self.screen.fill(Colors.BG)

        panel = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
        pygame.draw.rect(self.screen, Colors.SURFACE, panel, border_radius=12)
        pygame.draw.rect(self.screen, Colors.DIM, panel, 2, border_radius=12)

        Label("PRNG Coin Flip", 50, Colors.WHITE, WIDTH // 2, 45).draw(self.screen)
        info = f"{self.prng_name}  |  Seed: {self.seed}"
        if self.params:
            info += (
                f"  |  m={self.params['m']} a={self.params['a']} c={self.params['c']}"
            )
        Label(info, 22, Colors.GRAY, WIDTH // 2, 78).draw(self.screen)

        c = Colors.GREEN if self.streak > 0 else Colors.WHITE
        Label(f"Streak:  {self.streak} / {TARGET_STREAK}", 38, c, WIDTH // 2, 125).draw(
            self.screen
        )
        Label(
            f"Total Flips:  {self.total_flips}", 22, Colors.GRAY, WIDTH // 2, 155
        ).draw(self.screen)

        self.coin.draw(self.screen)

        c = Colors.YELLOW if self.skip_count > 0 else Colors.GRAY
        Label(f"Iteration Skips:  {self.skip_count}", 28, c, WIDTH // 2, 430).draw(
            self.screen
        )
        Label("(UP / DOWN to adjust)", 18, Colors.DIM, WIDTH // 2, 458).draw(
            self.screen
        )

        if self.message:
            c = (
                Colors.GREEN
                if ("Correct" in self.message or "win" in self.message)
                else Colors.RED
            )
            Label(self.message, 34, c, WIDTH // 2, 505).draw(self.screen)

        if self.state != "flipping" and not self.won:
            Label(
                "Press  H  for Heads   |   Press  T  for Tails",
                26,
                Colors.GRAY,
                WIDTH // 2,
                555,
            ).draw(self.screen)

        if self.last_result is not None:
            r = "HEADS" if self.last_result == Flip.HEADS else "TAILS"
            g = "HEADS" if self.last_guess == Flip.HEADS else "TAILS"
            Label(
                f"Result: {r}  |  Guess: {g}", 24, Colors.WHITE, WIDTH // 2, 595
            ).draw(self.screen)

        if self.won:
            Label("YOU WIN!", 64, Colors.GREEN, WIDTH // 2, 660).draw(self.screen)

        Label(
            "ESC to return to menu", 18, Colors.DIM, 20, HEIGHT - 35, center=False
        ).draw(self.screen)


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("PRNG Abuse — Coin Flip Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.menu = MainMenu(self.screen)
        self.config: Optional[ConfigScreen] = None
        self.game: Optional[Game] = None
        self.current = "menu"

    def run(self):
        while self.running:
            events = pygame.event.get()

            if self.current == "menu":
                action = self.menu.handle_events(events)
                self.menu.update()
                self.menu.draw()
                if action[0] == "config":
                    self.config = ConfigScreen(self.screen)
                    self.current = "config"
                elif action[0] == "quit":
                    self.running = False

            elif self.current == "config":
                action = self.config.handle_events(events)
                self.config.update()
                self.config.draw()
                if action[0] == "start_game":
                    cfg = action[1]
                    self.game = Game(
                        self.screen, self.clock, cfg["type"], cfg["seed"], cfg["params"]
                    )
                    self.current = "game"
                elif action[0] == "menu":
                    self.current = "menu"
                elif action[0] == "quit":
                    self.running = False

            elif self.current == "game":
                for e in events:
                    action = self.game.handle(e)
                    if action[0] == "menu":
                        self.current = "menu"
                        break
                    elif action[0] == "quit":
                        self.running = False
                        break
                else:
                    self.game.update()
                    self.game.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()
