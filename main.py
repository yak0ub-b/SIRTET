import asyncio
import math
import pygame
from constants import (
    COLS, ROWS, FPS, COLORS,
    BG_COLOR, GRID_COLOR, BORDER_COL, WHITE, LGRAY,
    BTN_NORMAL, BTN_PRESSED, BTN_BORDER,
)
from game import Game

KEY_REPEAT_DELAY = 170  # ms before auto-repeat
KEY_REPEAT_RATE  = 50   # ms between repeats

# ─────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────

def compute_layout(sw, sh):
    btn_h  = max(80, sh // 7)
    play_h = sh - btn_h
    cell   = min(sw // (COLS + 2), play_h // ROWS)
    cell   = max(cell, 10)
    board_w = cell * COLS
    board_h = cell * ROWS
    board_x = (sw - board_w) // 2
    board_y = (play_h - board_h) // 2
    return cell, board_x, board_y, btn_h


# ─────────────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────────────

def _clamp_color(c):
    return tuple(max(0, min(255, v)) for v in c)


def draw_cell(surf, color, x, y, size):
    """Draw a 3-D bevel block."""
    if size < 4:
        pygame.draw.rect(surf, color, (x, y, size, size))
        return

    # Main fill (slightly inset)
    pygame.draw.rect(surf, color, (x + 1, y + 1, size - 2, size - 2))

    # Highlight (top + left edges)
    light = _clamp_color((color[0] + 80, color[1] + 80, color[2] + 80))
    pygame.draw.line(surf, light, (x + 1, y + 1), (x + size - 2, y + 1), 2)
    pygame.draw.line(surf, light, (x + 1, y + 1), (x + 1, y + size - 2), 2)

    # Shadow (bottom + right edges)
    dark = _clamp_color((color[0] - 80, color[1] - 80, color[2] - 80))
    pygame.draw.line(surf, dark, (x + 1, y + size - 2), (x + size - 2, y + size - 2), 2)
    pygame.draw.line(surf, dark, (x + size - 2, y + 1),  (x + size - 2, y + size - 2), 2)

    # Bright corner pixel
    pygame.draw.rect(surf, light, (x + 2, y + 2, 3, 3))


def draw_ghost_cell(surf, color, x, y, size):
    """Draw ghost piece as a faint border outline."""
    ghost = _clamp_color((color[0] // 3, color[1] // 3, color[2] // 3))
    pygame.draw.rect(surf, ghost, (x, y, size - 1, size - 1), 1)


def draw_board(surf, game, cell, bx, by):
    # Empty cells
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(surf, GRID_COLOR,
                             (bx + c * cell, by + r * cell, cell - 1, cell - 1))

    # Locked cells
    for r in range(ROWS):
        for c in range(COLS):
            idx = game.board[r][c]
            if idx:
                draw_cell(surf, COLORS[idx],
                          bx + c * cell, by + r * cell, cell - 1)

    # Ghost piece
    ghost_r = game.ghost_row()
    color = COLORS[game.current_color()]
    for gr, gc in game.current_cells():
        sr = ghost_r + (gr - game.piece_row)
        if 0 <= sr < ROWS and sr != gr:   # only show where different from active
            draw_ghost_cell(surf, color,
                            bx + gc * cell, by + sr * cell, cell - 1)

    # Active piece
    for r, c in game.current_cells():
        if 0 <= r < ROWS:
            draw_cell(surf, color,
                      bx + c * cell, by + r * cell, cell - 1)

    # Board border
    pygame.draw.rect(surf, BORDER_COL,
                     (bx - 2, by - 2, COLS * cell + 4, ROWS * cell + 4), 2,
                     border_radius=3)


def draw_hud(surf, game, sw, sh, btn_h, bx, cell, fonts):
    font_label, font_score, font_title = fonts

    # Score panel — left side of board
    panel_w = max(bx - 10, 60)
    panel_x = 6
    panel_y = 10
    panel_h = 70

    if panel_w > 40:
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((20, 20, 55, 200))
        pygame.draw.rect(panel_surf, BORDER_COL, (0, 0, panel_w, panel_h), 2,
                         border_radius=8)
        lbl = font_label.render("SCORE", True, LGRAY)
        panel_surf.blit(lbl, (8, 6))
        sc  = font_score.render(str(game.score), True, WHITE)
        panel_surf.blit(sc, (8, 26))
        surf.blit(panel_surf, (panel_x, panel_y))

    # Title "SIRTET" top-right with glow
    glow_col = (130, 80, 255)
    title_glow = font_title.render("SIRTET", True, glow_col)
    title_main = font_title.render("SIRTET", True, WHITE)
    tr = title_main.get_rect(topright=(sw - 8, 8))
    for off in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        surf.blit(title_glow, (tr.x + off[0], tr.y + off[1]))
    surf.blit(title_main, tr)


def draw_buttons(surf, sw, sh, btn_h, pressed):
    labels = ["◀", "▼", "▶", "↺"]
    bw = sw // 4
    top = sh - btn_h
    font_size = max(28, btn_h // 2)
    font = pygame.font.SysFont(None, font_size)

    for i, lbl in enumerate(labels):
        x   = i * bw
        bg  = BTN_PRESSED if lbl in pressed else BTN_NORMAL
        rect = pygame.Rect(x + 3, top + 4, bw - 6, btn_h - 8)
        pygame.draw.rect(surf, bg, rect, border_radius=14)
        pygame.draw.rect(surf, BTN_BORDER, rect, 2, border_radius=14)
        txt = font.render(lbl, True, WHITE)
        surf.blit(txt, txt.get_rect(center=rect.center))


def draw_game_over(surf, sw, sh, game, fonts, anim_t):
    font_big, font_mid, font_small = fonts

    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 178))
    surf.blit(overlay, (0, 0))

    # Pulsing scale for "GAME OVER"
    scale = 1.0 + 0.04 * math.sin(anim_t * 3.5)
    cx, cy = sw // 2, sh // 2

    txt_go = font_big.render("GAME OVER", True, (255, 60, 60))
    scaled = pygame.transform.smoothscale(
        txt_go, (int(txt_go.get_width() * scale), int(txt_go.get_height() * scale))
    )
    surf.blit(scaled, scaled.get_rect(center=(cx, cy - 50)))

    txt_sc = font_mid.render(f"Score : {game.score}", True, WHITE)
    surf.blit(txt_sc, txt_sc.get_rect(center=(cx, cy + 20)))

    txt_re = font_small.render("Appuie pour rejouer", True, LGRAY)
    surf.blit(txt_re, txt_re.get_rect(center=(cx, cy + 65)))


# ─────────────────────────────────────────────────────────────────────
# Input helper
# ─────────────────────────────────────────────────────────────────────

def _apply_btn(game, lbl):
    if lbl == "◀":
        game.move(-1)
    elif lbl == "▶":
        game.move(1)
    elif lbl == "▼":
        game.soft_drop()
    elif lbl == "↺":
        game.rotate()


def _btn_label_at(mx, sw, sh, btn_h):
    """Return which button label was touched, or None."""
    if my_out_of_range(mx, sw, sh, btn_h):
        return None
    bw  = sw // 4
    idx = mx // bw
    return ["◀", "▼", "▶", "↺"][min(idx, 3)]


def my_out_of_range(mx, sw, sh, btn_h):
    return False   # placeholder (y checked at call site)


# ─────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────

async def main():
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    pygame.display.set_caption("Sirtet")

    clock = pygame.time.Clock()
    game  = Game()

    font_label = pygame.font.SysFont(None, 22)
    font_score = pygame.font.SysFont(None, 40)
    font_title = pygame.font.SysFont(None, 32)
    font_big   = pygame.font.SysFont(None, 72)
    font_mid   = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 28)

    held_keys   = {}
    btn_pressed = set()
    anim_t      = 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        anim_t += dt

        sw, sh = screen.get_size()
        cell, bx, by, btn_h = compute_layout(sw, sh)

        # ── Events ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if game.over:
                    if event.key == pygame.K_r:
                        game.reset()
                else:
                    if event.key == pygame.K_LEFT:
                        game.move(-1);  held_keys[pygame.K_LEFT]  = KEY_REPEAT_DELAY
                    elif event.key == pygame.K_RIGHT:
                        game.move(1);   held_keys[pygame.K_RIGHT] = KEY_REPEAT_DELAY
                    elif event.key == pygame.K_DOWN:
                        game.soft_drop(); held_keys[pygame.K_DOWN] = KEY_REPEAT_DELAY
                    elif event.key in (pygame.K_UP, pygame.K_z, pygame.K_x):
                        game.rotate()

            if event.type == pygame.KEYUP:
                held_keys.pop(event.key, None)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                btn_y_top = sh - btn_h
                if my >= btn_y_top:
                    idx = mx // (sw // 4)
                    lbl = ["◀", "▼", "▶", "↺"][min(idx, 3)]
                    btn_pressed.add(lbl)
                    if not game.over:
                        _apply_btn(game, lbl)
                elif game.over:
                    game.reset()

            if event.type == pygame.MOUSEBUTTONUP:
                btn_pressed.clear()

        # ── Key repeat ───────────────────────────────────────────────
        if not game.over:
            tick_ms = clock.get_time()
            for key in list(held_keys):
                held_keys[key] -= tick_ms
                if held_keys[key] <= 0:
                    held_keys[key] = KEY_REPEAT_RATE
                    if key == pygame.K_LEFT:   game.move(-1)
                    elif key == pygame.K_RIGHT: game.move(1)
                    elif key == pygame.K_DOWN:  game.soft_drop()

        # ── Game logic ───────────────────────────────────────────────
        game.update(dt)

        # ── Render ───────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        draw_board(screen, game, cell, bx, by)
        draw_buttons(screen, sw, sh, btn_h, btn_pressed)
        draw_hud(screen, game, sw, sh, btn_h, bx, cell,
                 (font_label, font_score, font_title))
        if game.over:
            draw_game_over(screen, sw, sh, game,
                           (font_big, font_mid, font_small), anim_t)

        pygame.display.flip()
        await asyncio.sleep(0)


asyncio.run(main())
