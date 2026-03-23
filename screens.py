"""
screens.py — Title, scores, and game-over screen drawing functions.
All functions are pure: they take a surface + state, draw, and return
button Rect dicts so that main.py can do hit-testing.
"""
import math
import pygame
from constants import (
    WHITE, LGRAY, BG_COLOR, BORDER_COL,
    ACCENT_PURPLE, ACCENT_CYAN, ACCENT_YELLOW, DIM_BLUE,
    BTN_NORMAL, BTN_BORDER,
)


# ─────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────

def _draw_glow_text(surf, font, text, color_glow, color_main, cx, y, offsets=2):
    glow = font.render(text, True, color_glow)
    main = font.render(text, True, color_main)
    for dx in (-offsets, offsets):
        for dy in (-offsets, offsets):
            surf.blit(glow, glow.get_rect(centerx=cx + dx, top=y + dy))
    surf.blit(main, main.get_rect(centerx=cx, top=y))
    return main.get_height()


def _draw_button(surf, rect, label, font, hovered=False):
    bg     = (60, 60, 140) if hovered else BTN_NORMAL
    border = WHITE         if hovered else BTN_BORDER
    pygame.draw.rect(surf, bg,     rect, border_radius=12)
    pygame.draw.rect(surf, border, rect, 2, border_radius=12)
    txt = font.render(label, True, WHITE)
    surf.blit(txt, txt.get_rect(center=rect.center))


# ─────────────────────────────────────────────────────────────────────
# Title screen
# ─────────────────────────────────────────────────────────────────────

def draw_title_screen(surf, sw, sh, anim_t, best_scores, hovered_btn, fonts):
    """
    Draw the full title screen.
    Returns {"JOUER": Rect, "SCORES": Rect}
    """
    cx = sw // 2

    # Animated glow color
    t   = anim_t * 2.0
    gr  = int(ACCENT_PURPLE[0] + (ACCENT_CYAN[0] - ACCENT_PURPLE[0]) * (0.5 + 0.5 * math.sin(t)))
    gg  = int(ACCENT_PURPLE[1] + (ACCENT_CYAN[1] - ACCENT_PURPLE[1]) * (0.5 + 0.5 * math.sin(t)))
    gb  = int(ACCENT_PURPLE[2] + (ACCENT_CYAN[2] - ACCENT_PURPLE[2]) * (0.5 + 0.5 * math.sin(t)))
    glow_color = (gr, gg, gb)

    # ── SIRTET logo ───────────────────────────────────────────────────
    logo_y = int(sh * 0.20)
    h = _draw_glow_text(surf, fonts["title"], "SIRTET",
                         glow_color, WHITE, cx, logo_y, offsets=3)

    # Subtitle
    sub_y = logo_y + h + 8
    sub   = fonts["small"].render("TETRIS A L'ENVERS", True, LGRAY)
    surf.blit(sub, sub.get_rect(centerx=cx, top=sub_y))

    # Best score
    best_y = sub_y + sub.get_height() + 14
    if best_scores:
        bs = fonts["score"].render(f"BEST: {best_scores[0]:06d}", True, ACCENT_YELLOW)
        surf.blit(bs, bs.get_rect(centerx=cx, top=best_y))
        btn_top = best_y + bs.get_height() + 28
    else:
        btn_top = best_y + 20

    # ── Buttons ───────────────────────────────────────────────────────
    btn_w  = min(200, sw - 40)
    btn_h  = 44
    btn_gap = 14

    jouer_rect  = pygame.Rect(cx - btn_w // 2, btn_top, btn_w, btn_h)
    scores_rect = pygame.Rect(cx - btn_w // 2, btn_top + btn_h + btn_gap, btn_w, btn_h)

    _draw_button(surf, jouer_rect,  "JOUER",   fonts["btn"], hovered=(hovered_btn == "JOUER"))
    _draw_button(surf, scores_rect, "SCORES",  fonts["btn"], hovered=(hovered_btn == "SCORES"))

    # Blinking "PRESS ANY KEY" hint at bottom
    if int(anim_t * 2) % 2 == 0:
        hint = fonts["small"].render("APPUIE N'IMPORTE OU", True, LGRAY)
        surf.blit(hint, hint.get_rect(centerx=cx, bottom=sh - 20))

    return {"JOUER": jouer_rect, "SCORES": scores_rect}


# ─────────────────────────────────────────────────────────────────────
# Scores screen
# ─────────────────────────────────────────────────────────────────────

def draw_scores_screen(surf, sw, sh, scores, anim_t, fonts):
    """
    Draw top-5 high scores overlay.
    Returns back_btn_rect.
    """
    # Semi-transparent overlay
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surf.blit(overlay, (0, 0))

    cx     = sw // 2
    panel_w = min(320, sw - 40)
    panel_h = 300
    panel_x = cx - panel_w // 2
    panel_y = sh // 2 - panel_h // 2

    # Panel background
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((15, 15, 45, 230))
    pygame.draw.rect(panel, BORDER_COL, (0, 0, panel_w, panel_h), 2, border_radius=12)
    surf.blit(panel, (panel_x, panel_y))

    # Heading
    y = panel_y + 18
    h = _draw_glow_text(surf, fonts["label"], "TOP SCORES",
                         ACCENT_PURPLE, ACCENT_YELLOW, cx, y)
    y += h + 18

    if scores:
        for i, sc in enumerate(scores):
            color = ACCENT_YELLOW if i == 0 else WHITE
            line  = fonts["score"].render(f"#{i+1}   {sc:06d}", True, color)
            surf.blit(line, line.get_rect(centerx=cx, top=y))
            y += line.get_height() + 8
    else:
        no = fonts["score"].render("AUCUN SCORE", True, LGRAY)
        surf.blit(no, no.get_rect(centerx=cx, top=y))

    # BACK button
    btn_w   = 140
    btn_h   = 38
    back_rect = pygame.Rect(cx - btn_w // 2,
                             panel_y + panel_h - btn_h - 14,
                             btn_w, btn_h)
    _draw_button(surf, back_rect, "RETOUR", fonts["btn"])
    return back_rect


# ─────────────────────────────────────────────────────────────────────
# Game-over screen
# ─────────────────────────────────────────────────────────────────────

def draw_game_over_screen(surf, sw, sh, score, is_new_high, best_scores, anim_t, fonts):
    """
    Draw game-over overlay.
    Returns {"REJOUER": Rect, "MENU": Rect}
    """
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surf.blit(overlay, (0, 0))

    cx = sw // 2
    cy = sh // 2

    # Pulsing "GAME OVER"
    scale = 1.0 + 0.04 * math.sin(anim_t * 3.5)
    raw   = fonts["heading"].render("GAME OVER", True, (255, 60, 60))
    scaled = pygame.transform.smoothscale(
        raw, (int(raw.get_width() * scale), int(raw.get_height() * scale))
    )
    surf.blit(scaled, scaled.get_rect(centerx=cx, centery=cy - 70))

    # New high score flash
    if is_new_high and int(anim_t * 3) % 2 == 0:
        nh = fonts["label"].render("NOUVEAU RECORD !", True, ACCENT_YELLOW)
        surf.blit(nh, nh.get_rect(centerx=cx, centery=cy - 28))

    # Score
    sc_txt = fonts["score"].render(f"SCORE: {score:06d}", True, WHITE)
    surf.blit(sc_txt, sc_txt.get_rect(centerx=cx, centery=cy + 10))

    # Rank
    if best_scores:
        try:
            rank = sorted(best_scores + [score], reverse=True).index(score) + 1
        except ValueError:
            rank = None
        if rank:
            rk = fonts["small"].render(f"#{rank} AU CLASSEMENT", True, LGRAY)
            surf.blit(rk, rk.get_rect(centerx=cx, centery=cy + 40))

    # Buttons
    btn_w   = 150
    btn_h   = 40
    btn_gap = 14
    rejouer_rect = pygame.Rect(cx - btn_w - btn_gap // 2,
                                cy + 65, btn_w, btn_h)
    menu_rect    = pygame.Rect(cx + btn_gap // 2,
                                cy + 65, btn_w, btn_h)
    _draw_button(surf, rejouer_rect, "REJOUER", fonts["btn"])
    _draw_button(surf, menu_rect,    "MENU",    fonts["btn"])

    return {"REJOUER": rejouer_rect, "MENU": menu_rect}
