COLS = 10
ROWS = 20
FPS  = 60

# Fall speed base (cells/s)
BASE_FALL_SPEED = 1.0

# ── Level system ──────────────────────────────────────────────────────
LINES_PER_LEVEL  = 10
MAX_LEVEL        = 15
LEVEL_SPEED_INC  = 0.3     # cells/s added per level
LEVEL_SCORE_MULT = 0.5     # pts *= (1 + 0.5 * level)

# ── Background / UI colors ────────────────────────────────────────────
BG_COLOR   = ( 10,  10,  25)   # deep night blue
GRID_COLOR = ( 18,  18,  42)   # empty cells
BORDER_COL = ( 55,  55, 120)   # board border
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
LGRAY      = ( 90,  90, 130)

# ── Accent colors ─────────────────────────────────────────────────────
ACCENT_PURPLE = (130,  80, 255)   # logo glow, level-up
ACCENT_CYAN   = (  0, 220, 255)   # stars, HUD accents
ACCENT_YELLOW = (255, 220,   0)   # level-up banner, #1 score
DIM_BLUE      = ( 20,  20,  55)   # panel fill

# ── Button colors ─────────────────────────────────────────────────────
BTN_NORMAL  = ( 28,  28,  60)
BTN_PRESSED = ( 75,  75, 165)
BTN_BORDER  = ( 90,  90, 200)

# ── Piece colors (neon palette), index 1-7 ───────────────────────────
COLORS = [
    None,
    (  0, 220, 255),  # 1 – I  cyan
    (255, 220,   0),  # 2 – O  yellow
    (185,   0, 255),  # 3 – T  violet
    (  0, 255, 100),  # 4 – S  green
    (255,  50,  50),  # 5 – Z  red
    ( 50, 110, 255),  # 6 – J  blue
    (255, 145,   0),  # 7 – L  orange
]

# ── Visual effects ────────────────────────────────────────────────────
SCANLINE_ALPHA = 30   # CRT scanline stripe opacity (0-255)

# ── High scores ───────────────────────────────────────────────────────
SCORES_FILE  = "scores.json"
TOP_N_SCORES = 5
