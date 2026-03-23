import random
from constants import COLS, ROWS, BASE_FALL_SPEED
from pieces import PIECES, get_cells

# Score table: lines cleared at once → points
LINE_POINTS = {1: 10, 2: 25, 3: 50, 4: 100}


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        # Board: 2D list, 0 = empty, 1-7 = piece color index
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.over  = False
        self._fall_accum = 0.0   # accumulated fall time (seconds)
        self._spawn_next()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _spawn_next(self):
        self.piece_idx = random.randrange(len(PIECES))
        self.rotation  = 0
        self.piece_row = 0
        self.piece_col = COLS // 2 - 2   # roughly centred

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
        color = self.piece_idx + 1  # color index 1-7
        for r, c in get_cells(self.piece_idx, self.rotation,
                               self.piece_row, self.piece_col):
            if 0 <= r < ROWS and 0 <= c < COLS:
                self.board[r][c] = color
        lines = self._clear_lines()
        self.score += LINE_POINTS.get(lines, 0)
        self._spawn_next()

    def _clear_lines(self):
        full = [r for r in range(ROWS) if all(self.board[r])]
        for r in full:
            del self.board[r]
            self.board.insert(0, [0] * COLS)
        return len(full)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fall_speed(self):
        """Cells per second, increases gradually with score."""
        return BASE_FALL_SPEED + self.score / 200.0

    def update(self, dt):
        """Call every frame with elapsed time in seconds."""
        if self.over:
            return
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
        """Move piece left (dx=-1) or right (dx=+1)."""
        if not self.over and not self._collides(
                self.piece_row, self.piece_col + dx, self.rotation):
            self.piece_col += dx

    def soft_drop(self):
        """Move piece one cell down immediately."""
        if not self.over:
            if not self._collides(self.piece_row + 1, self.piece_col, self.rotation):
                self.piece_row += 1
                self._fall_accum = 0.0
            else:
                self._lock_piece()

    def rotate(self):
        """Rotate piece clockwise with simple wall-kick."""
        if self.over:
            return
        new_rot = (self.rotation + 1) % 4
        # Try current position, then offsets -1, +1, -2, +2
        for offset in (0, -1, 1, -2, 2):
            if not self._collides(self.piece_row, self.piece_col + offset, new_rot):
                self.rotation  = new_rot
                self.piece_col += offset
                return

    def current_cells(self):
        """Return list of (row, col) for the active piece."""
        return get_cells(self.piece_idx, self.rotation,
                         self.piece_row, self.piece_col)

    def ghost_row(self):
        """Row where the piece would land if dropped now."""
        r = self.piece_row
        while not self._collides(r + 1, self.piece_col, self.rotation):
            r += 1
        return r

    def current_color(self):
        return self.piece_idx + 1
