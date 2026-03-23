"""
Run this script once to generate PWA icons:
    python pwa/generate_icons.py
Produces pwa/icon-192.png and pwa/icon-512.png
"""
import os
import pygame

def make_icon(size, out_path):
    pygame.init()
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Background circle
    bg = (10, 10, 25)
    surf.fill(bg)
    cx, cy, r = size // 2, size // 2, size // 2 - 2
    pygame.draw.circle(surf, (28, 28, 70), (cx, cy), r)
    pygame.draw.circle(surf, (90, 90, 200), (cx, cy), r, max(2, size // 64))

    # Draw "S" in the centre
    font_size = int(size * 0.62)
    font = pygame.font.SysFont("Arial Black", font_size, bold=True)
    if not font:
        font = pygame.font.SysFont(None, font_size)

    # Glow layer
    glow_col = (180, 80, 255)
    glow = font.render("S", True, glow_col)
    gr   = glow.get_rect(center=(cx, cy))
    for dx, dy in ((-2,-2),(2,-2),(-2,2),(2,2),(0,-3),(0,3),(-3,0),(3,0)):
        surf.blit(glow, (gr.x + dx, gr.y + dy))

    # Main letter
    txt = font.render("S", True, (255, 255, 255))
    surf.blit(txt, txt.get_rect(center=(cx, cy)))

    pygame.image.save(surf, out_path)
    print(f"Saved {out_path}")

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    make_icon(192, os.path.join(out_dir, "icon-192.png"))
    make_icon(512, os.path.join(out_dir, "icon-512.png"))
    pygame.quit()
