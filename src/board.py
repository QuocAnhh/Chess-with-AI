import chess
import pygame
class ChessBoard:
    def __init__(self):
        self.board = chess.Board()
        # Tăng độ mượt của animation
        pygame.display.set_caption("Chess Master 2025")
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION])
    def get_legal_moves(self):
        return list(self.board.legal_moves)
    
    def make_move(self, move):
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False
    
    def is_game_over(self):
        return self.board.is_game_over()
    
    def get_game_result(self):
        if not self.is_game_over(): 
            return None
        if self.board.is_checkmate():
            return "checkmate"
        if self.board.is_stalemate():
            return "stalemate"
        if self.board.is_insufficient_material():
            return "insufficient material"
        if self.board.is_fifty_moves():
            return "fifty-move rule"
        if self.board.is_repetition():
            return "repetition"
        return "game over"
    
    def get_board_state(self):
        return self.board.fen()
    
    def set_board_state(self, fen):
        self.board.set_fen(fen)
    
    def is_check(self):
        return self.board.is_check()