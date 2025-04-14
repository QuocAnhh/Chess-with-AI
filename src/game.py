import chess
from enum import Enum, auto
from src.learning_chess_ai import ChessAI

class GameMode(Enum):
    PLAYER_VS_PLAYER = auto()
    PLAYER_VS_AI = auto()
    AI_VS_AI = auto()
    AI_TRAINING = auto()

class GameState(Enum):
    ACTIVE = auto()
    CHECK = auto()
    CHECKMATE = auto()
    STALEMATE = auto()
    DRAW = auto()
    RESIGNED = auto()
    ONGOING = auto() 

class ChessGame:
    def __init__(self, mode=GameMode.PLAYER_VS_AI, difficulty=2, ai=None):
        self.board = chess.Board()
        self.mode = mode
        self.game_mode = "pvp" if mode == GameMode.PLAYER_VS_PLAYER else "pve"
        self.current_player = True  # True = White, False = Black
        self.winner = None
        self.game_state = GameState.ACTIVE
        self.move_history = []
        self.captured_pieces = []
        
        self.ai = ai if ai else ChessAI(difficulty=difficulty)
        self.ai_thinking = False
        
    def get_legal_moves(self):
        return list(self.board.legal_moves)
    
    def make_move(self, move):
        """Thực hiện nước đi và cập nhật trạng thái game"""

        if self.is_game_over():
            print("Game is already over, move rejected")
            return False
            
        # Check nếu nước đi hợp lệ
        if move in self.board.legal_moves:
            print(f"Making move: {move.uci()}")
            # Lưu quân bị bắt
            to_square = move.to_square
            if self.board.piece_at(to_square):
                self.captured_pieces.append((self.board.piece_at(to_square), self.current_player))
            
            self.board.push(move)
            
            self.move_history.append(move.uci())
            
            self.current_player = not self.current_player
            
            self.update_game_state()
            
            return True
        else:
            print(f"Move {move} is not legal")
            
        return False
    
    def update_game_state(self):
        """Cập nhật trạng thái game sau mỗi nước đi"""
        if self.board.is_checkmate():
            print("Game state: CHECKMATE")
            self.game_state = GameState.CHECKMATE
            self.winner = "white" if not self.current_player else "black"
        elif self.board.is_stalemate():
            print("Game state: STALEMATE")
            self.game_state = GameState.STALEMATE
        elif self.board.is_insufficient_material() or self.board.is_fifty_moves():
            print("Game state: DRAW")
            self.game_state = GameState.DRAW
        elif self.board.is_check():
            print("Game state: CHECK")
            self.game_state = GameState.CHECK
        else:
            self.game_state = GameState.ACTIVE
    
    def is_game_over(self):
        """Kiểm tra xem game đã kết thúc chưa"""
        return self.game_state in [GameState.CHECKMATE, GameState.STALEMATE, GameState.DRAW]
    
    def get_state(self):
        """Trả về trạng thái hiện tại của game"""
        if self.board.is_checkmate():
            return GameState.CHECKMATE
        elif self.board.is_stalemate():
            return GameState.STALEMATE
        elif self.board.is_insufficient_material():
            return GameState.DRAW
        elif self.is_game_over():
            return GameState.DRAW
        return GameState.ONGOING
    
    def undo_move(self):
        """Đi lại nước đi trước đó"""
        if len(self.board.move_stack) > 0:
            self.board.pop()
            self.current_player = not self.current_player
            if self.move_history:
                self.move_history.pop()
            self.update_game_state()
            return True
        return False
    
    def game_over_learn(self):
        """Gọi sau khi trò chơi kết thúc để AI học từ ván đấu"""
        if self.mode != GameMode.PLAYER_VS_AI or not hasattr(self.ai, 'learn_from_game'):
            return
                
        result = "1/2-1/2"  # Huề
        
        if self.get_state() == GameState.CHECKMATE:
            result = "1-0" if not self.current_player else "0-1"
        elif self.get_state() == GameState.RESIGNED:
            # Nếu 1 bên đã đầu hàng
            result = "0-1" if self.current_player else "1-0"
        
        if hasattr(self.ai, 'learning_enabled') and self.ai.learning_enabled:
            print(f"AI đang học từ ván đấu với {len(self.move_history)} nước đi, kết quả: {result}")
            self.ai.learn_from_game(self.move_history, result)
            print("AI đã học xong!")
        else:
            print("Tính năng học đã bị tắt - AI không học từ ván đấu")