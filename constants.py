COLS = 10
ROWS = 20
FPS  = 60

# Fall speed: cells per second (increases with score)
BASE_FALL_SPEED = 1.0

# ── Background / UI colors ────────────────────────────────────────────
BG_COLOR   = ( 10,  10,  25)   # deep night blue
GRID_COLOR = ( 18,  18,  42)   # empty cells
BORDER_COL = ( 55,  55, 120)   # board border
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
LGRAY      = ( 90,  90, 130)

# ── Button colors ─────────────────────────────────────────────────────
BTN_NORMAL  = ( 28,  28,  60)
BTN_PRESSED = ( 75,  75, 165)
BTN_BORDER  = ( 90,  90, 200)

# ── Piece colors (neon palette), index 1-7 (0 = empty) ───────────────
COLORS = [
    None,
    (  0, 220, 255),  # 1 – I  cyan électrique
    (255, 220,   0),  # 2 – O  jaune vif
    (185,   0, 255),  # 3 – T  violet neon
    (  0, 255, 100),  # 4 – S  vert neon
    (255,  50,  50),  # 5 – Z  rouge vif
    ( 50, 110, 255),  # 6 – J  bleu électrique
    (255, 145,   0),  # 7 – L  orange vif
]
