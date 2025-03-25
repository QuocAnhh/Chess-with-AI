# NOTE: This file is deprecated. Please use src.learning_chess_ai.ChessAI instead.
# The code below is kept for reference but should not be used directly.

import chess
import random
import time

class ChessAI:
    def __init__(self, difficulty=1):
        self.difficulty = difficulty  # 1: Easy, 2: Medium, 3: Hard
        self.PIECE_VALUES = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # Bảng giá trị vị trí cho các quân cờ
        self.POSITION_VALUES = {
            # Tốt
            chess.PAWN: [
                0, 0, 0, 0, 0, 0, 0, 0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5, 5, 10, 25, 25, 10, 5, 5,
                0, 0, 0, 20, 20, 0, 0, 0,
                5, -5, -10, 0, 0, -10, -5, 5,
                5, 10, 10, -20, -20, 10, 10, 5,
                0, 0, 0, 0, 0, 0, 0, 0
            ],
            # Mã
            chess.KNIGHT: [
                -50, -40, -30, -30, -30, -30, -40, -50,
                -40, -20, 0, 0, 0, 0, -20, -40,
                -30, 0, 10, 15, 15, 10, 0, -30,
                -30, 5, 15, 20, 20, 15, 5, -30,
                -30, 0, 15, 20, 20, 15, 0, -30,
                -30, 5, 10, 15, 15, 10, 5, -30,
                -40, -20, 0, 5, 5, 0, -20, -40,
                -50, -40, -30, -30, -30, -30, -40, -50
            ],
            # Tượng
            chess.BISHOP: [
                -20, -10, -10, -10, -10, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 10, 10, 10, 10, 0, -10,
                -10, 5, 5, 10, 10, 5, 5, -10,
                -10, 0, 5, 10, 10, 5, 0, -10,
                -10, 5, 5, 5, 5, 5, 5, -10,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -20, -10, -10, -10, -10, -10, -10, -20
            ],
            # Xe
            chess.ROOK: [
                0, 0, 0, 0, 0, 0, 0, 0,
                5, 10, 10, 10, 10, 10, 10, 5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                -5, 0, 0, 0, 0, 0, 0, -5,
                0, 0, 0, 5, 5, 0, 0, 0
            ],
            # Hậu
            chess.QUEEN: [
                -20, -10, -10, -5, -5, -10, -10, -20,
                -10, 0, 0, 0, 0, 0, 0, -10,
                -10, 0, 5, 5, 5, 5, 0, -10,
                -5, 0, 5, 5, 5, 5, 0, -5,
                0, 0, 5, 5, 5, 5, 0, -5,
                -10, 5, 5, 5, 5, 5, 0, -10,
                -10, 0, 5, 0, 0, 0, 0, -10,
                -20, -10, -10, -5, -5, -10, -10, -20
            ],
            # Vua
            chess.KING: [
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -30, -40, -40, -50, -50, -40, -40, -30,
                -20, -30, -30, -40, -40, -30, -30, -20,
                -10, -20, -20, -20, -20, -20, -20, -10,
                20, 20, 0, 0, 0, 0, 20, 20,
                20, 30, 10, 0, 0, 10, 30, 20
            ]
        }
    
    def get_move(self, board):
        """Enhanced move selection with check handling"""
        print(f"AI difficulty: {self.difficulty}, board turn: {board.turn}")
        
        # First, check if we're in check - if so, prioritize getting out of check
        if board.is_check():
            print("AI is in check - finding escape move")
            return self.get_check_escape_move(board)
            
        # Otherwise use standard difficulty-based move selection
        if self.difficulty == 1:
            return self.get_random_move(board)
        elif self.difficulty == 2:
            return self.get_smart_move(board, depth=3)
        else:
            return self.get_smart_move(board, depth=4)
    
    def get_check_escape_move(self, board):
        """Prioritize moves that escape check"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            print("No legal moves available!")
            return None
            
        # Try capture checking piece first
        checking_squares = []
        for move in legal_moves:
            board.push(move)
            if not board.is_check():
                # This move escapes check - evaluate its quality
                move_score = self.evaluate_board(board)
                board.pop()
                print(f"Found check escape move: {move}, score: {move_score}")
                return move
            board.pop()
            
        # If we get here, no special good check escape was found
        # Just take the first legal move
        print(f"No good check escape found, using default move: {legal_moves[0]}")
        return legal_moves[0]
    
    def get_random_move(self, board):
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None
    
    def get_smart_move(self, board, depth=2):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Khuyến khích đa dạng loại quân cờ sử dụng
        piece_type_diversity_score = {}
    
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
    
        for move in legal_moves:
            # Lấy thông tin về quân cờ được di chuyển
            from_square = move.from_square
            piece = board.piece_at(from_square)
        
            board.push(move)
            value = -self.minimax(board, depth - 1, -beta, -alpha, not board.turn)
        
            # Thêm khuyến khích sử dụng đa dạng quân cờ
            if piece and piece.piece_type in piece_type_diversity_score:
                # Nếu quân này đã được sử dụng nhiều, giảm giá trị nước đi
                value -= piece_type_diversity_score[piece.piece_type] * 5
        
            board.pop()
        
            if value > best_value:
                best_value = value
                best_move = move
            
                #  Ghi nhận đã sử dụng loại quân này
                if piece:
                    if piece.piece_type not in piece_type_diversity_score:
                        piece_type_diversity_score[piece.piece_type] = 1
                    else:
                        piece_type_diversity_score[piece.piece_type] += 1
                    
            alpha = max(alpha, value)
    
        return best_move
    
    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board)
        
        legal_moves = list(board.legal_moves)
        
        if maximizing:
            value = float('-inf')
            for move in legal_moves:
                board.push(move)
                value = max(value, self.minimax(board, depth - 1, alpha, beta, False))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in legal_moves:
                board.push(move)
                value = min(value, self.minimax(board, depth - 1, alpha, beta, True))
                board.pop()
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
    
    def evaluate_board(self, board):
        if board.is_game_over():
            if board.is_checkmate():
                return -10000 if board.turn else 10000
            else:
                return 0
    
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.PIECE_VALUES[piece.piece_type]
                position_value = 0
            
                if piece.piece_type in self.POSITION_VALUES:
                    position = square
                    if not piece.color:
                        # Đảo vị trí đối với quân đen
                        position = 63 - position
                    position_value = self.POSITION_VALUES[piece.piece_type][position]
            
                # Giảm tỷ trọng đánh giá vị trí
                position_value *= 0.7
            
                # Thêm yếu tố ngẫu nhiên nhỏ để tăng tính đa dạng trong nước đi
                diversity_factor = random.uniform(0.95, 1.05)
            
                if piece.color == chess.WHITE:
                    score += (value + position_value) * diversity_factor
                else:
                    score -= (value + position_value) * diversity_factor
    
        return score