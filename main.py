import asyncio
import os
import math
import pygame

from constants import (
    COLS, ROWS, FPS, COLORS,
    BG_COLOR, GRID_COLOR, BORDER_COL, WHITE, LGRAY,
    BTN_NORMAL, BTN_PRESSED, BTN_BORDER,
    ACCENT_PURPLE, ACCENT_YELLOW, DIM_BLUE,
)
from game import Game
from effects import StarField, ScanlineOverlay, ParticleSystem, LineFlash, LevelUpBanner
from screens import draw_title_screen, draw_scores_screen, draw_game_over_screen
from scores import load_scores, save_score
from pieces import get_cells

KEY_REPEAT_DELAY = 170
KEY_REPEAT_RATE  = 50

STATE_TITLE    = "title"
STATE_SCORES   = "scores"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"


# ─────────────────────────────────────────────────────────────────────
# Font loader
# ─────────────────────────────────────────────────────────────────────

def load_fonts(base_path: str) -> dict:
    ttf = os.path.join(base_path, "PressStart2P.ttf")
    use_ttf = os.path.isfile(ttf)

    def _f(size):
        if use_ttf:
            return pygame.font.Font(ttf, size)
        return pygame.font.SysFont("monospace", size, bold=True)

    return {
        "title":   _f(36),
        "heading": _f(22),
        "label":   _f(11),
        "score":   _f(14),
        "small":   _f(9),
        "btn":     _f(13),
    }


# ─────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────

def compute_layout(sw, sh):
    btn_h   = max(80, sh // 7)
    play_h  = sh - btn_h
    side_w  = max(int(sw * 0.18), 80)
    avail_w = sw - 2 * side_w
    avail_h = play_h
    cell    = min(avail_w // COLS, avail_h // ROWS)
    cell    = max(cell, 10)
    board_w = cell * COLS
    board_h = cell * ROWS
    board_x = (sw - board_w) // 2
    board_y = (play_h - board_h) // 2
    left_rect  = pygame.Rect(0,             0, board_x,                  play_h)
    right_rect = pygame.Rect(board_x + board_w, 0, sw - (board_x + board_w), play_h)
    return cell, board_x, board_y, btn_h, left_rect, right_rect


# ─────────────────────────────────────────────────────────────────────
# Cell drawing
# ─────────────────────────────────────────────────────────────────────

def _clamp(c):
    return tuple(max(0, min(255, v)) for v in c)

def draw_cell(surf, color, x, y, size):
    if size < 4:
        pygame.draw.rect(surf, color, (x, y, size, size))
        return
    pygame.draw.rect(surf, color, (x + 1, y + 1, size - 2, size - 2))
    light = _clamp((color[0] + 80, color[1] + 80, color[2] + 80))
    dark  = _clamp((color[0] - 80, color[1] - 80, color[2] - 80))
    pygame.draw.line(surf, light, (x + 1, y + 1), (x + size - 2, y + 1), 2)
    pygame.draw.line(surf, light, (x + 1, y + 1), (x + 1, y + size - 2), 2)
    pygame.draw.line(surf, dark,  (x + 1, y + size - 2), (x + size - 2, y + size - 2), 2)
    pygame.draw.line(surf, dark,  (x + size - 2, y + 1),  (x + size - 2, y + size - 2), 2)
    pygame.draw.rect(surf, light, (x + 2, y + 2, 3, 3))

def draw_ghost_cell(surf, color, x, y, size):
    ghost = _clamp((color[0] // 3, color[1] // 3, color[2] // 3))
    pygame.draw.rect(surf, ghost, (x, y, size - 1, size - 1), 1)


# ─────────────────────────────────────────────────────────────────────
# Board
# ─────────────────────────────────────────────────────────────────────

def draw_board(surf, game, cell, bx, by):
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(surf, GRID_COLOR,
                             (bx + c * cell, by + r * cell, cell - 1, cell - 1))
    for r in range(ROWS):
        for c in range(COLS):
            idx = game.board[r][c]
            if idx:
                draw_cell(surf, COLORS[idx],
                          bx + c * cell, by + r * cell, cell - 1)
    # Ghost
    ghost_r = game.ghost_row()
    color   = COLORS[game.current_color()]
    for gr, gc in game.current_cells():
        sr = ghost_r + (gr - game.piece_row)
        if 0 <= sr < ROWS and sr != gr:
            draw_ghost_cell(surf, color,
                            bx + gc * cell, by + sr * cell, cell - 1)
    # Active piece
    for r, c in game.current_cells():
        if 0 <= r < ROWS:
            draw_cell(surf, color, bx + c * cell, by + r * cell, cell - 1)
    # Border
    pygame.draw.rect(surf, BORDER_COL,
                     (bx - 2, by - 2, COLS * cell + 4, ROWS * cell + 4), 2,
                     border_radius=3)


# ─────────────────────────────────────────────────────────────────────
# Side panels
# ─────────────────────────────────────────────────────────────────────

def _mini_panel(surf, rect, label_txt, value_txt, font_lbl, font_val, y_top):
    """Draw a small labelled stat box. Returns height used."""
    pw = rect.width - 12
    lbl = font_lbl.render(label_txt, True, LGRAY)
    val = font_val.render(value_txt, True, WHITE)
    total_h = lbl.get_height() + val.get_height() + 10
    box = pygame.Rect(rect.x + 6, y_top, pw, total_h + 10)
    pygame.draw.rect(surf, DIM_BLUE,   box, border_radius=8)
    pygame.draw.rect(surf, BORDER_COL, box, 1, border_radius=8)
    surf.blit(lbl, lbl.get_rect(centerx=rect.centerx, top=y_top + 5))
    surf.blit(val, val.get_rect(centerx=rect.centerx, top=y_top + 5 + lbl.get_height() + 3))
    return total_h + 16


def draw_left_panel(surf, game, rect, fonts):
    if rect.width < 60:
        return
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((15, 15, 40, 160))
    surf.blit(panel, rect.topleft)

    y = 20
    y += _mini_panel(surf, rect, "SCORE", f"{game.score:06d}",
                     fonts["label"], fonts["score"], rect.y + y)
    y += 6
    y += _mini_panel(surf, rect, "LEVEL", str(game.level),
                     fonts["label"], fonts["score"], rect.y + y)
    y += 6
    _mini_panel(surf, rect, "LINES", str(game.lines_cleared),
                fonts["label"], fonts["score"], rect.y + y)

    # SIRTET watermark at bottom
    wm = fonts["small"].render("SIRTET", True, (40, 40, 80))
    surf.blit(wm, wm.get_rect(centerx=rect.centerx, bottom=rect.bottom - 10))


def draw_right_panel(surf, game, rect, cell, fonts):
    if rect.width < 60:
        return
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((15, 15, 40, 160))
    surf.blit(panel, rect.topleft)

    # NEXT label
    lbl = fonts["label"].render("NEXT", True, LGRAY)
    surf.blit(lbl, lbl.get_rect(centerx=rect.centerx, top=rect.y + 12))

    # Preview piece
    preview_cell = min((rect.width - 16) // 4, 22)
    cells        = get_cells(game.next_piece_idx, 0, 0, 0)
    # Centre the 4-wide preview in the panel
    px = rect.x + (rect.width - preview_cell * 4) // 2
    py = rect.y + lbl.get_height() + 22
    color = COLORS[game.next_piece_idx + 1]
    for r, c in cells:
        draw_cell(surf, color,
                  px + c * preview_cell, py + r * preview_cell,
                  preview_cell - 1)
    pygame.draw.rect(surf, BORDER_COL,
                     (px - 2, py - 2, 4 * preview_cell + 4, 4 * preview_cell + 4),
                     1, border_radius=2)


# ─────────────────────────────────────────────────────────────────────
# Mobile buttons
# ─────────────────────────────────────────────────────────────────────

def draw_buttons(surf, sw, sh, btn_h, pressed):
    labels    = ["<", "v", ">", "R"]
    disp      = ["  <  ", "  v  ", "  >  ", "  R  "]
    bw        = sw // 4
    top       = sh - btn_h
    font_size = max(28, btn_h // 2)
    font      = pygame.font.SysFont(None, font_size)
    for i, lbl in enumerate(labels):
        x    = i * bw
        bg   = BTN_PRESSED if lbl in pressed else BTN_NORMAL
        rect = pygame.Rect(x + 3, top + 4, bw - 6, btn_h - 8)
        pygame.draw.rect(surf, bg, rect, border_radius=14)
        pygame.draw.rect(surf, BTN_BORDER, rect, 2, border_radius=14)
        txt = font.render(disp[i].strip(), True, WHITE)
        surf.blit(txt, txt.get_rect(center=rect.center))


# ─────────────────────────────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────────────────────────────

def _apply_btn(game, lbl):
    if lbl == "<":    game.move(-1)
    elif lbl == ">":  game.move(1)
    elif lbl == "v":  game.soft_drop()
    elif lbl == "R":  game.rotate()

def _btn_at(mx, sw, sh, btn_h):
    if mx < 0 or mx >= sw:
        return None
    return ["<", "v", ">", "R"][min(mx // (sw // 4), 3)]


# ─────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────

async def main():
    pygame.init()
    info  = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    pygame.display.set_caption("Sirtet")
    clock  = pygame.time.Clock()

    fonts  = load_fonts(".")

    # Effects (init before game loop)
    stars     = StarField(sw, sh)
    scanlines = ScanlineOverlay(sw, sh)
    particles = ParticleSystem()
    flash     = LineFlash()
    banner    = LevelUpBanner(fonts["heading"])

    best_scores = load_scores()
    game        = Game()

    state        = STATE_TITLE
    hovered_btn  = None   # for title screen
    btn_pressed  = set()  # mobile button labels
    held_keys    = {}
    anim_t       = 0.0
    is_new_high  = False
    title_rects  = {}     # populated each frame in TITLE state
    go_rects     = {}     # game-over buttons

    while True:
        dt     = clock.tick(FPS) / 1000.0
        anim_t += dt
        sw, sh  = screen.get_size()
        cell, bx, by, btn_h, left_rect, right_rect = compute_layout(sw, sh)

        # ── Events ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
                stars.resize(sw, sh)
                scanlines.resize(sw, sh)

            # ── TITLE ────────────────────────────────────────────────
            if state == STATE_TITLE:
                if event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    hovered_btn = None
                    for lbl, r in title_rects.items():
                        if r.collidepoint(mx, my):
                            hovered_btn = lbl
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for lbl, r in title_rects.items():
                        if r.collidepoint(mx, my):
                            if lbl == "JOUER":
                                game.reset()
                                state  = STATE_PLAYING
                                anim_t = 0.0
                            elif lbl == "SCORES":
                                state = STATE_SCORES
                if event.type == pygame.KEYDOWN:
                    game.reset()
                    state  = STATE_PLAYING
                    anim_t = 0.0

            # ── SCORES ───────────────────────────────────────────────
            elif state == STATE_SCORES:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    state = STATE_TITLE

            # ── PLAYING ──────────────────────────────────────────────
            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        game.move(-1);       held_keys[pygame.K_LEFT]  = KEY_REPEAT_DELAY
                    elif event.key == pygame.K_RIGHT:
                        game.move(1);        held_keys[pygame.K_RIGHT] = KEY_REPEAT_DELAY
                    elif event.key == pygame.K_DOWN:
                        game.soft_drop();    held_keys[pygame.K_DOWN]  = KEY_REPEAT_DELAY
                    elif event.key in (pygame.K_UP, pygame.K_z, pygame.K_x):
                        game.rotate()
                    elif event.key == pygame.K_ESCAPE:
                        state = STATE_TITLE

                if event.type == pygame.KEYUP:
                    held_keys.pop(event.key, None)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if my >= sh - btn_h:
                        lbl = _btn_at(mx, sw, sh, btn_h)
                        if lbl:
                            btn_pressed.add(lbl)
                            _apply_btn(game, lbl)

                if event.type == pygame.MOUSEBUTTONUP:
                    btn_pressed.clear()

            # ── GAMEOVER ─────────────────────────────────────────────
            elif state == STATE_GAMEOVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for lbl, r in go_rects.items():
                        if r.collidepoint(mx, my):
                            if lbl == "REJOUER":
                                game.reset()
                                state  = STATE_PLAYING
                                anim_t = 0.0
                            elif lbl == "MENU":
                                best_scores = load_scores()
                                state       = STATE_TITLE
                                anim_t      = 0.0
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game.reset()
                        state  = STATE_PLAYING
                        anim_t = 0.0

        # ── Per-frame updates ─────────────────────────────────────────
        stars.update(dt)

        if state == STATE_PLAYING:
            # Key repeat
            tick_ms = clock.get_time()
            for key in list(held_keys):
                held_keys[key] -= tick_ms
                if held_keys[key] <= 0:
                    held_keys[key] = KEY_REPEAT_RATE
                    if key == pygame.K_LEFT:    game.move(-1)
                    elif key == pygame.K_RIGHT:  game.move(1)
                    elif key == pygame.K_DOWN:   game.soft_drop()

            game.update(dt)

            # React to game events
            if game.event_lines_cleared > 0:
                row_ys = [by + r * cell for r in game.event_cleared_rows]
                flash.trigger(row_ys, bx, COLS * cell, cell)
                for ry in row_ys:
                    particles.emit_line_clear(ry + cell // 2, bx, COLS * cell)

            if game.event_level_up:
                banner.trigger(game.level)
                particles.emit_level_up(bx + COLS * cell // 2,
                                        by + ROWS * cell // 2)

            if game.over:
                best_scores, is_new_high = save_score(game.score)
                state  = STATE_GAMEOVER
                anim_t = 0.0

            particles.update(dt)
            flash.update(dt)
            banner.update(dt)

        # ── Render ────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        stars.draw(screen)

        if state == STATE_TITLE:
            title_rects = draw_title_screen(
                screen, sw, sh, anim_t, best_scores, hovered_btn, fonts
            )

        elif state == STATE_SCORES:
            draw_title_screen(screen, sw, sh, anim_t, best_scores, None, fonts)
            draw_scores_screen(screen, sw, sh, best_scores, anim_t, fonts)

        elif state in (STATE_PLAYING, STATE_GAMEOVER):
            draw_board(screen, game, cell, bx, by)
            draw_left_panel(screen, game, left_rect, fonts)
            draw_right_panel(screen, game, right_rect, cell, fonts)
            draw_buttons(screen, sw, sh, btn_h, btn_pressed)
            particles.draw(screen)
            flash.draw(screen)
            banner.draw(screen, sw, sh)

            if state == STATE_GAMEOVER:
                go_rects = draw_game_over_screen(
                    screen, sw, sh, game.score,
                    is_new_high, best_scores, anim_t, fonts
                )

        scanlines.draw(screen)   # CRT overlay — always last
        pygame.display.flip()
        await asyncio.sleep(0)


asyncio.run(main())
