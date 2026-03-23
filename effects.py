"""
effects.py — Visual effects for Sirtet:
  StarField, ScanlineOverlay, ParticleSystem, LineFlash, LevelUpBanner
All classes are frame-rate independent (they consume dt in seconds).
No external assets required.
"""
import math
import random
import pygame
from constants import (
    BG_COLOR, ACCENT_CYAN, ACCENT_YELLOW, ACCENT_PURPLE,
    SCANLINE_ALPHA, WHITE, COLORS,
)

# ─────────────────────────────────────────────────────────────────────
# StarField
# ─────────────────────────────────────────────────────────────────────

_STAR_LAYERS = [
    # (speed px/s, radius, alpha, color)
    (15.0, 1, 80,  (0, 180, 220)),
    (35.0, 1, 150, (0, 220, 255)),
    (70.0, 2, 220, (200, 230, 255)),
]

class StarField:
    def __init__(self, sw: int, sh: int, n_stars: int = 120):
        self.sw = sw
        self.sh = sh
        self._stars = []
        # Pre-bake one tiny Surface per layer for fast blitting
        self._sprites = []
        for speed, radius, alpha, color in _STAR_LAYERS:
            s = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius + 1, radius + 1), radius)
            self._sprites.append(s)
        # Distribute stars across layers
        per_layer = n_stars // len(_STAR_LAYERS)
        for layer_idx in range(len(_STAR_LAYERS)):
            for _ in range(per_layer):
                self._stars.append({
                    "x":     random.uniform(0, sw),
                    "y":     random.uniform(0, sh),
                    "layer": layer_idx,
                })

    def update(self, dt: float):
        for star in self._stars:
            speed = _STAR_LAYERS[star["layer"]][0]
            star["y"] += speed * dt
            if star["y"] > self.sh:
                star["y"] = 0.0
                star["x"] = random.uniform(0, self.sw)

    def draw(self, surf: pygame.Surface):
        for star in self._stars:
            layer = star["layer"]
            radius = _STAR_LAYERS[layer][1]
            spr = self._sprites[layer]
            surf.blit(spr, (int(star["x"]) - radius - 1, int(star["y"]) - radius - 1),
                      special_flags=pygame.BLEND_RGBA_ADD)

    def resize(self, sw: int, sh: int):
        self.sw = sw
        self.sh = sh
        for star in self._stars:
            if star["x"] > sw:
                star["x"] = random.uniform(0, sw)
            if star["y"] > sh:
                star["y"] = random.uniform(0, sh)


# ─────────────────────────────────────────────────────────────────────
# ScanlineOverlay
# ─────────────────────────────────────────────────────────────────────

class ScanlineOverlay:
    def __init__(self, sw: int, sh: int):
        self.sw = sw
        self.sh = sh
        self._surf = None
        self._bake()

    def _bake(self):
        self._surf = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        self._surf.fill((0, 0, 0, 0))
        stripe = pygame.Surface((self.sw, 1), pygame.SRCALPHA)
        stripe.fill((0, 0, 0, SCANLINE_ALPHA))
        for y in range(0, self.sh, 2):
            self._surf.blit(stripe, (0, y))

    def draw(self, surf: pygame.Surface):
        surf.blit(self._surf, (0, 0))

    def resize(self, sw: int, sh: int):
        if sw != self.sw or sh != self.sh:
            self.sw = sw
            self.sh = sh
            self._bake()


# ─────────────────────────────────────────────────────────────────────
# ParticleSystem
# ─────────────────────────────────────────────────────────────────────

_MAX_PARTICLES = 200

class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "radius", "gravity")

class ParticleSystem:
    def __init__(self):
        self._pool: list[_Particle] = []

    def _emit(self, x, y, vx, vy, life, color, radius, gravity=300.0):
        if len(self._pool) >= _MAX_PARTICLES:
            return
        p = _Particle()
        p.x, p.y = x, y
        p.vx, p.vy = vx, vy
        p.life = life
        p.max_life = life
        p.color = color
        p.radius = radius
        p.gravity = gravity
        self._pool.append(p)

    def emit_line_clear(self, row_y: float, board_x: float,
                        board_w: float, n: int = 18):
        for _ in range(n):
            color = COLORS[random.randint(1, 7)]
            self._emit(
                x      = random.uniform(board_x, board_x + board_w),
                y      = row_y,
                vx     = random.uniform(-120, 120),
                vy     = random.uniform(-200, -50),
                life   = random.uniform(0.4, 0.7),
                color  = color,
                radius = random.uniform(2.0, 5.0),
                gravity= 300.0,
            )

    def emit_level_up(self, cx: float, cy: float, n: int = 40):
        for i in range(n):
            angle = i / n * 2 * math.pi
            speed = random.uniform(80, 220)
            color = COLORS[(i % 7) + 1]
            self._emit(
                x      = cx,
                y      = cy,
                vx     = math.cos(angle) * speed,
                vy     = math.sin(angle) * speed,
                life   = random.uniform(0.8, 1.2),
                color  = color,
                radius = random.uniform(3.0, 6.0),
                gravity= 0.0,   # fan outward, no gravity
            )

    def update(self, dt: float):
        alive = []
        for p in self._pool:
            p.life -= dt
            if p.life > 0:
                p.x  += p.vx * dt
                p.y  += p.vy * dt
                p.vy += p.gravity * dt
                alive.append(p)
        self._pool = alive

    def draw(self, surf: pygame.Surface):
        for p in self._pool:
            alpha = int(255 * (p.life / p.max_life))
            r = max(1, int(p.radius))
            tmp = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*p.color, alpha), (r + 1, r + 1), r)
            surf.blit(tmp, (int(p.x) - r - 1, int(p.y) - r - 1))


# ─────────────────────────────────────────────────────────────────────
# LineFlash
# ─────────────────────────────────────────────────────────────────────

_FLASH_DURATION = 0.22

class LineFlash:
    def __init__(self):
        self._rows: list[float] = []
        self._bx   = 0.0
        self._bw   = 0.0
        self._cell = 1
        self._t    = 0.0

    def trigger(self, row_ys: list, board_x: float, board_w: float, cell: int):
        self._rows = list(row_ys)
        self._bx   = board_x
        self._bw   = board_w
        self._cell = cell
        self._t    = _FLASH_DURATION

    def update(self, dt: float):
        if self._t > 0:
            self._t = max(0.0, self._t - dt)

    def is_active(self) -> bool:
        return self._t > 0

    def draw(self, surf: pygame.Surface):
        if not self.is_active():
            return
        alpha = int(255 * (self._t / _FLASH_DURATION))
        for ry in self._rows:
            tmp = pygame.Surface((int(self._bw), self._cell), pygame.SRCALPHA)
            tmp.fill((255, 255, 255, alpha))
            surf.blit(tmp, (int(self._bx), int(ry)))


# ─────────────────────────────────────────────────────────────────────
# LevelUpBanner
# ─────────────────────────────────────────────────────────────────────

_BANNER_SLIDE_IN  = 0.3
_BANNER_HOLD_END  = 1.1
_BANNER_DURATION  = 1.4

class LevelUpBanner:
    def __init__(self, font: pygame.font.Font):
        self._font  = font
        self._t     = 0.0
        self._level = 1
        self._active = False

    def trigger(self, level: int):
        self._level  = level
        self._t      = _BANNER_DURATION
        self._active = True

    def update(self, dt: float):
        if self._active:
            self._t = max(0.0, self._t - dt)
            if self._t <= 0:
                self._active = False

    def is_active(self) -> bool:
        return self._active

    def draw(self, surf: pygame.Surface, sw: int, sh: int):
        if not self._active:
            return

        elapsed = _BANNER_DURATION - self._t
        # Compute y offset based on phase
        banner_h = 60
        center_y = sh // 2 - banner_h // 2

        if elapsed < _BANNER_SLIDE_IN:
            progress = elapsed / _BANNER_SLIDE_IN
            y = int(-banner_h + (center_y + banner_h) * progress)
        elif elapsed < _BANNER_HOLD_END:
            y = center_y
        else:
            progress = (elapsed - _BANNER_HOLD_END) / (_BANNER_DURATION - _BANNER_HOLD_END)
            y = int(center_y - (center_y + banner_h) * progress)

        text = f"LEVEL {self._level}!"
        glow = self._font.render(text, True, ACCENT_PURPLE)
        main = self._font.render(text, True, ACCENT_YELLOW)
        cx   = sw // 2
        for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            surf.blit(glow, glow.get_rect(centerx=cx + dx, top=y + dy))
        surf.blit(main, main.get_rect(centerx=cx, top=y))
