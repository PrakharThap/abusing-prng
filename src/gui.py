import math
import sys
import os
from typing import Optional
import copy

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prng import Flip, MiddleSquare, LCG, SRG, PRNG
from guesser import *

WIDTH = 900
HEIGHT = 960
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
            prng = LCG(params["m"], params["a"], params["c"], seed)
        else:
            prng = LCG(2**31, 1103515245, 12345, seed)
    elif name == "Xorshift":
        if params:
            prng = SRG(seed, params["a"], params["b"], params["c"])
        else:
            prng = SRG(seed)
    else:
        prng = MiddleSquare(seed)

    if params and "interpreter" in params:
        interp = params["interpreter"]
        if interp["type"] == "bit":
            prng.interpreter = partial(Flip.BIT_INTERPRETER, bit=interp["value"])
        else:
            prng.interpreter = partial(
                Flip.THRESHOLD_INTERPRETER, threshold=interp["value"]
            )

    return prng


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
        y0 = 420
        gap = 75
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
        Label("PRNG Abuse", 72, Colors.WHITE, WIDTH // 2, 220).draw(self.screen)
        Label("Coin Flip Game", 28, Colors.GRAY, WIDTH // 2, 275).draw(self.screen)
        for btn in self.buttons:
            btn.draw(self.screen)
        if self.ai_toast > 0:
            Label("Coming soon!", 26, Colors.YELLOW, WIDTH // 2, 700).draw(self.screen)


LCG_PRESETS = [
    {"name": "RANDU", "m": 2**31, "a": 65539, "c": 0},
    {"name": "glibc", "m": 2**31, "a": 1103515245, "c": 12345},
    {"name": "MINSTD", "m": 2**31 - 1, "a": 16807, "c": 0},
    {"name": "MSVC", "m": 2**31, "a": 214013, "c": 2531011},
]


class ConfigScreen:
    def __init__(self, screen):
        self.screen = screen
        cx = WIDTH // 2
        field_w, field_h = 240, 36

        self.type_toggle = Toggle(
            pygame.Rect(cx - 225, 240, 450, 44), ["Middle Square", "LCG", "Xorshift"]
        )

        self.seed_field = InputField(
            pygame.Rect(cx - field_w // 2, 310, field_w, field_h), "Seed", "675248"
        )

        self.interp_toggle = Toggle(
            pygame.Rect(cx - 100, 392, 200, 36), ["Bit", "Threshold"]
        )
        self.interp_field = InputField(
            pygame.Rect(cx - field_w // 2, 470, field_w, field_h),
            "Bit position",
            "30",
        )

        self.m_field = InputField(
            pygame.Rect(cx - field_w // 2, 555, field_w, field_h),
            "Modulus (m)",
            "2147483648",
        )
        self.lcg_a_field = InputField(
            pygame.Rect(cx - field_w // 2, 635, field_w, field_h),
            "Multiplier (a)",
            "1103515245",
        )
        self.lcg_c_field = InputField(
            pygame.Rect(cx - field_w // 2, 715, field_w, field_h),
            "Increment (c)",
            "12345",
        )
        self.srg_a_field = InputField(
            pygame.Rect(cx - field_w // 2, 555, field_w, field_h),
            "Shift a",
            "13",
        )
        self.srg_b_field = InputField(
            pygame.Rect(cx - field_w // 2, 635, field_w, field_h),
            "Shift b",
            "7",
        )
        self.srg_c_field = InputField(
            pygame.Rect(cx - field_w // 2, 715, field_w, field_h),
            "Shift c",
            "17",
        )

        self.error = ""
        self.preset_idx = 1

        preset_count = len(LCG_PRESETS)
        pw, pg = 120, 10
        total_pw = preset_count * pw + (preset_count - 1) * pg
        self.preset_rects = []
        x0 = cx - total_pw // 2
        for i in range(preset_count):
            self.preset_rects.append(pygame.Rect(x0 + i * (pw + pg), 810, pw, 34))

        btn_w, btn_h = 180, 50
        self.start_btn = Button(
            pygame.Rect(cx - btn_w - 15, 885, btn_w, btn_h),
            "Start",
            Colors.GREEN,
            (80, 240, 100),
            Colors.BLACK,
        )
        self.back_btn = Button(
            pygame.Rect(cx + 15, 885, btn_w, btn_h),
            "Back",
            Colors.SURFACE,
            Colors.SURFACE_HOVER,
            Colors.WHITE,
        )

    def _active_fields(self):
        t = self.type_toggle.value()
        fields = [self.seed_field, self.interp_field]
        if t == "LCG":
            fields += [self.m_field, self.lcg_a_field, self.lcg_c_field]
        elif t == "Xorshift":
            fields += [self.srg_a_field, self.srg_b_field, self.srg_c_field]
        return fields

    def _sync_interp_defaults(self):
        t = self.type_toggle.value()
        if self.interp_toggle.value() == "Bit":
            self.interp_field.label = "Bit position"
            if t == "Xorshift":
                self.interp_field.text = "0"
            else:
                self.interp_field.text = "30"
        else:
            self.interp_field.label = "Threshold"
            if t == "Middle Square":
                self.interp_field.text = "500000"
            else:
                self.interp_field.text = "1073741824"

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                return ("quit", None)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                fields = self._active_fields()
                for i, f in enumerate(fields):
                    if f.focused:
                        f.focused = False
                        fields[(i + 1) % len(fields)].focused = True
                        break
            for f in self._active_fields():
                f.handle_event(e)
            if self.type_toggle.handle_event(e) or self.interp_toggle.handle_event(e):
                self._sync_interp_defaults()
            if self.start_btn.handle_event(e):
                return self._try_start()
            if self.back_btn.handle_event(e):
                return ("menu", None)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                return self._try_start()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.type_toggle.value() == "LCG":
                    for i, r in enumerate(self.preset_rects):
                        if r.collidepoint(e.pos):
                            p = LCG_PRESETS[i]
                            self.m_field.text = str(p["m"])
                            self.lcg_a_field.text = str(p["a"])
                            self.lcg_c_field.text = str(p["c"])
                            self.preset_idx = i
        return ("continue", None)

    def _try_start(self):
        seed = self.seed_field.value()
        if seed is None or seed <= 0:
            self.error = "Seed must be a positive integer"
            return ("continue", None)

        prng_type = self.type_toggle.value()
        interp_type = self.interp_toggle.value()
        interp_val = self.interp_field.value()
        if interp_val is None or interp_val < 0:
            self.error = f"{'Bit position' if interp_type == 'Bit' else 'Threshold'} must be a non-negative integer"
            return ("continue", None)
        interpreter = {"type": interp_type.lower(), "value": interp_val}

        params = None
        if prng_type == "LCG":
            m = self.m_field.value()
            a = self.lcg_a_field.value()
            c = self.lcg_c_field.value()
            if m is None or a is None or c is None or m <= 0 or a < 0 or c < 0:
                self.error = "All LCG parameters must be positive integers"
                return ("continue", None)
            params = {"m": m, "a": a, "c": c, "interpreter": interpreter}
        elif prng_type == "Xorshift":
            a = self.srg_a_field.value()
            b = self.srg_b_field.value()
            c = self.srg_c_field.value()
            if a is None or b is None or c is None or a < 0 or b < 0 or c < 0:
                self.error = "All shift values must be non-negative integers"
                return ("continue", None)
            params = {"a": a, "b": b, "c": c, "interpreter": interpreter}
        else:
            params = {"interpreter": interpreter}

        self.error = ""
        return ("start_game", {"type": prng_type, "seed": seed, "params": params})

    def update(self):
        for f in self._active_fields():
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

        Label("Interpretation", 20, Colors.GRAY, WIDTH // 2, 372).draw(self.screen)
        self.interp_toggle.draw(self.screen)
        self.interp_field.draw(self.screen)

        t = self.type_toggle.value()
        if t == "LCG":
            self.m_field.draw(self.screen)
            self.lcg_a_field.draw(self.screen)
            self.lcg_c_field.draw(self.screen)
            Label("Presets", 20, Colors.GRAY, WIDTH // 2, 790).draw(self.screen)
            for i, (p, r) in enumerate(zip(LCG_PRESETS, self.preset_rects)):
                if i == self.preset_idx:
                    pygame.draw.rect(
                        self.screen, Colors.ACCENT_DARK, r, border_radius=6
                    )
                    pygame.draw.rect(self.screen, Colors.ACCENT, r, 2, border_radius=6)
                else:
                    pygame.draw.rect(self.screen, Colors.SURFACE, r, border_radius=6)
                    pygame.draw.rect(self.screen, Colors.DIM, r, 2, border_radius=6)
                f = pygame.font.Font(None, 20)
                c = Colors.WHITE if i == self.preset_idx else Colors.GRAY
                img = f.render(p["name"], True, c)
                self.screen.blit(img, img.get_rect(center=r.center))
        elif t == "Xorshift":
            self.srg_a_field.draw(self.screen)
            self.srg_b_field.draw(self.screen)
            self.srg_c_field.draw(self.screen)
        else:
            Label("No extra parameters needed", 20, Colors.DIM, WIDTH // 2, 620).draw(
                self.screen
            )
            Label("for Middle Square PRNG", 20, Colors.DIM, WIDTH // 2, 645).draw(
                self.screen
            )

        if self.error:
            Label(self.error, 22, Colors.RED, WIDTH // 2, 860).draw(self.screen)

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
        self.skip_buffer = ""
        self.round_skips = 1
        self.last_result: Optional[Flip] = None
        self.last_guess: Optional[Flip] = None
        self.message = ""
        self.won = False
        self.state = "skip_input"

        self.coin = Coin(*COIN_CENTER, COIN_RADIUS)

        avg = avg_flip_until(copy.deepcopy(self.prng), 5)
        print(f"Avg # flips for 5 correct guesses in a row: {avg}")

    def reset(self):
        self.streak = 0
        self.total_flips = 0
        self.skip_buffer = ""
        self.round_skips = 1
        self.last_result = None
        self.last_guess = None
        self.message = ""
        self.won = False
        self.prng.reset(self.seed)
        self.state = "skip_input"

    def _advance_prng(self, n):
        for _ in range(n):
            self.prng.next_value

    def guess(self, side):
        self.last_guess = side
        self._advance_prng(self.round_skips)
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
        if self.won:
            if event.key == pygame.K_r:
                self.reset()
            return ("continue", None)

        if self.state == "skip_input":
            if event.key == pygame.K_RETURN:
                raw = self.skip_buffer.strip()
                self.round_skips = max(1, min(int(raw), 100) if raw else 1)
                self.skip_buffer = ""
                self.state = "guess_input"
            elif event.key == pygame.K_BACKSPACE:
                self.skip_buffer = self.skip_buffer[:-1]
            else:
                ch = event.unicode
                if ch.isdigit():
                    self.skip_buffer += ch
        elif self.state == "guess_input":
            if event.key == pygame.K_h:
                self.guess(Flip.HEADS)
            elif event.key == pygame.K_t:
                self.guess(Flip.TAILS)
        elif self.state == "result":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = "skip_input"

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
            if "m" in self.params:
                info += f"  |  m={self.params['m']} a={self.params['a']} c={self.params['c']}"
            elif "a" in self.params and "b" in self.params:
                info += f"  |  a={self.params['a']} b={self.params['b']} c={self.params['c']}"
            if "interpreter" in self.params:
                i = self.params["interpreter"]
                info += f"  |  {i['type']}={i['value']}"
        Label(info, 22, Colors.GRAY, WIDTH // 2, 78).draw(self.screen)

        c = Colors.GREEN if self.streak > 0 else Colors.WHITE
        Label(f"Streak:  {self.streak} / {TARGET_STREAK}", 38, c, WIDTH // 2, 125).draw(
            self.screen
        )
        Label(
            f"Total Flips:  {self.total_flips}", 22, Colors.GRAY, WIDTH // 2, 155
        ).draw(self.screen)

        self.coin.draw(self.screen)

        if self.state == "skip_input":
            cursor = "▌" if (pygame.time.get_ticks() // 500) % 2 else " "
            hint = f"Iterations to skip (1 - 100):  {self.skip_buffer}{cursor}"
            Label(hint, 28, Colors.YELLOW, WIDTH // 2, 430).draw(self.screen)
            Label(
                "type digits, then press ENTER", 18, Colors.DIM, WIDTH // 2, 460
            ).draw(self.screen)

        elif self.state == "guess_input":
            Label(f"Skip: {self.round_skips}", 28, Colors.YELLOW, WIDTH // 2, 430).draw(
                self.screen
            )
            Label(
                "Press  H  for Heads   |   Press  T  for Tails",
                26,
                Colors.GRAY,
                WIDTH // 2,
                465,
            ).draw(self.screen)

        elif self.state == "result":
            if not self.won:
                Label("Press SPACE to continue", 26, Colors.GRAY, WIDTH // 2, 440).draw(
                    self.screen
                )

        if self.message:
            c = (
                Colors.GREEN
                if ("Correct" in self.message or "win" in self.message)
                else Colors.RED
            )
            Label(self.message, 34, c, WIDTH // 2, 505).draw(self.screen)

        if self.last_result is not None and self.state in ("result", "skip_input"):
            r = "HEADS" if self.last_result == Flip.HEADS else "TAILS"
            g = "HEADS" if self.last_guess == Flip.HEADS else "TAILS"
            Label(
                f"Result: {r}  |  Guess: {g}", 24, Colors.WHITE, WIDTH // 2, 555
            ).draw(self.screen)

        if self.won:
            Label("YOU WIN!", 64, Colors.GREEN, WIDTH // 2, 620).draw(self.screen)

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
