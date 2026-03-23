import random
from constants import (
    COLS, ROWS, BASE_FALL_SPEED,
    LINES_PER_LEVEL, MAX_LEVEL, LEVEL_SPEED_INC, LEVEL_SCORE_MULT,
)
from pieces import PIECES, get_cells

LINE_POINTS = {1: 100, 2: 300, 3: 500, 4: 800}


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board             = [[0] * COLS for _ in range(ROWS)]
        self.score             = 0
        self.over              = False
        self.level             = 0
        self.lines_cleared     = 0
        self.lines_to_next     = LINES_PER_LEVEL
        self._fall_accum       = 0.0
        # Events — read by main.py each frame, cleared at start of update()
        self.event_lines_cleared = 0
        self.event_level_up      = False
        self.event_cleared_rows  = []
        # Lookahead
        self._next_piece_idx   = random.randrange(len(PIECES))
        self._spawn_next()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _spawn_next(self):
        self.piece_idx       = self._next_piece_idx
        self._next_piece_idx = random.randrange(len(PIECES))
        self.rotation        = 0
        self.piece_row       = 0
        self.piece_col       = COLS // 2 - 2
        if self._collides(self.piece_row, self.piece_col, self.rotation):
            self.over = True

    def _collides(self, row, col, rot):
        for r, c in get_cells(self.piece_idx, rot, row, col):
            if r < 0 or r >= ROWS or c < 0 or c >= COLS:
                return True
            if self.board[r][c] != 0:
                return True
        return False

    def _lock_piece(self):
        color = self.piece_idx + 1
        for r, c in get_cells(self.piece_idx, self.rotation,
                               self.piece_row, self.piece_col):
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.board[r][c] = color

        lines = self._clear_lines()
        self.event_lines_cleared = lines

        if lines:
            self.lines_cleared += lines
            self.lines_to_next -= lines
            pts = int(LINE_POINTS.get(lines, 0) * (1.0 + LEVEL_SCORE_MULT * self.level))
            self.score += pts
            if self.lines_to_next <= 0:
                self.level         = min(self.level + 1, MAX_LEVEL)
                self.lines_to_next = LINES_PER_LEVEL + self.lines_to_next
                self.event_level_up = True

        self._spawn_next()

    def _clear_lines(self):
        full = [r for r in range(ROWS) if all(self.board[r])]
        self.event_cleared_rows = list(full)   # store indices before deletion
        for r in full:
            del self.board[r]
            self.board.insert(0, [0] * COLS)
        return len(full)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def next_piece_idx(self):
        return self._next_piece_idx

    def fall_speed(self):
        return BASE_FALL_SPEED + LEVEL_SPEED_INC * self.level

    def update(self, dt):
        if self.over:
            return
        # Clear events from previous frame
        self.event_lines_cleared = 0
        self.event_level_up      = False
        self.event_cleared_rows  = []

        self._fall_accum += dt
        interval = 1.0 / self.fall_speed()
        while self._fall_accum >= interval:
            self._fall_accum -= interval
            if not self._collides(self.piece_row + 1, self.piece_col, self.rotation):
                self.piece_row += 1
            else:
                self._lock_piece()
                break

    def move(self, dx):
        if not self.over and not self._collides(
                self.piece_row, self.piece_col + dx, self.rotation):
            self.piece_col += dx

    def soft_drop(self):
        if not self.over:
            if not self._collides(self.piece_row + 1, self.piece_col, self.rotation):
                self.piece_row   += 1
                self._fall_accum  = 0.0
            else:
                self._lock_piece()

    def rotate(self):
        if self.over:
            return
        new_rot = (self.rotation + 1) % 4
        for offset in (0, -1, 1, -2, 2):
            if not self._collides(self.piece_row, self.piece_col + offset, new_rot):
                self.rotation  = new_rot
                self.piece_col += offset
                return

    def current_cells(self):
        return get_cells(self.piece_idx, self.rotation,
                         self.piece_row, self.piece_col)

    def ghost_row(self):
        r = self.piece_row
        while not self._collides(r + 1, self.piece_col, self.rotation):
            r += 1
        return r

    def current_color(self):
        return self.piece_idx + 1
