from .constants import *

class Othello:
    __slots__ = ['board', 'current_player']

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        mid = BOARD_SIZE // 2
        self.board[mid-1][mid-1] = WHITE;  self.board[mid][mid]   = WHITE
        self.board[mid-1][mid]   = BLACK;  self.board[mid][mid-1] = BLACK

    def copy(self):
        g = Othello.__new__(Othello)
        g.board = [row[:] for row in self.board]
        g.current_player = self.current_player
        return g

    def is_on_board(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get_flips(self, row, col):
        if self.board[row][col] != EMPTY:
            return []
        flips = []; opp = -self.current_player; cp = self.current_player; board = self.board
        for dr, dc in DIRECTIONS:
            r, c = row+dr, col+dc; temp = []
            while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==opp:
                temp.append((r,c)); r+=dr; c+=dc
            if temp and 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==cp:
                flips.extend(temp)
        return flips

    def valid_moves(self):
        moves = []; board = self.board; cp = self.current_player; opp = -cp
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != EMPTY: continue
                for dr, dc in DIRECTIONS:
                    nr, nc = r+dr, c+dc
                    if not (0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==opp):
                        continue
                    nr+=dr; nc+=dc
                    while 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==opp:
                        nr+=dr; nc+=dc
                    if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==cp:
                        moves.append((r,c)); break
        return moves

    def make_move(self, row, col):
        flips = self.get_flips(row, col)
        if not flips: return False
        self.board[row][col] = self.current_player
        for r, c in flips: self.board[r][c] = self.current_player
        self.current_player *= -1
        return True

    def game_over(self):
        if self.valid_moves(): return False
        self.current_player *= -1
        has = bool(self.valid_moves())
        self.current_player *= -1
        return not has

    def score(self):
        b = w = 0
        for row in self.board:
            for cell in row:
                if cell == BLACK: b += 1
                elif cell == WHITE: w += 1
        return b, w

    def empty_count(self):
        return sum(row.count(EMPTY) for row in self.board)
