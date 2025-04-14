import chess
import random
import time
import os
import chess.pgn
import pickle


class ChessAI:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty 
        self.PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 300,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
        }
        self.learning_rate = 0.1
        self.memory = {}  
        self.positions_seen = 0  
        self.trained_games = 0  
        self.learning_enabled = True  
        
        self.memory_dir = os.path.join('data', 'memory')
        os.makedirs(self.memory_dir, exist_ok=True)
        
        self.load_memory()
    
    def learn_from_pgn_file(self, pgn_file_path):
        """Học từ file PGN chứa nhiều ván cờ"""
        try:
            
            with open(pgn_file_path, "r") as pgn_file:
                games_learned = 0
                
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None: # Đã đọc hết
                        break
                    
                    result = game.headers.get("Result", "*")
                    if result == "*":  # Bỏ qua ván đấu chưa có kết quả
                        continue
                    
                    moves = []
                    board = game.board()
                    for move in game.mainline_moves():
                        moves.append(move.uci())
                        board.push(move)
                    
                    self.learn_from_game(moves, result)
                    games_learned += 1
                    
                    # in thông tin sau 10 ván đáu
                    if games_learned % 10 == 0:
                        print(f"Đã học từ {games_learned} ván đấu...")
                
                print(f"Hoàn thành! Đã học từ {games_learned} ván đấu.")
                
                if not hasattr(self, 'trained_games'):
                    self.trained_games = 0
                self.trained_games += games_learned
                
                self.save_memory()
                
                return games_learned
                
        except Exception as e:
            print(f"Lỗi khi học từ file PGN: {str(e)}")
            raise e
        
    def get_learning_stats(self):
        """Trả về thông tin về quá trình học của AI"""
        return {
            'positions': self.positions_seen,  # Số lượng vị trí đã xem
            'games': self.trained_games,       # Số ván đấu đã học
            'memory_size': len(self.memory),   # Kích thước bộ nhớ
            'learning_rate': self.learning_rate  # Tốc độ học
        }
        
        
    def load_memory(self):
        """Tải bộ nhớ từ file"""
        memory_file = os.path.join(self.memory_dir, f'chess_memory_d{self.difficulty}.pkl')
        try:
            if os.path.exists(memory_file):
                with open(memory_file, 'rb') as f:
                    data = pickle.load(f)
                    self.memory = data.get('memory', {})
                    self.trained_games = data.get('trained_games', 0)
                    self.positions_seen = data.get('positions_seen', 0)
                print(f"Đã tải {len(self.memory)} vị trí từ bộ nhớ")
        except Exception as e:
            print(f"Lỗi khi tải bộ nhớ: {e}")
    
    def save_memory(self):
        """Lưu bộ nhớ vào file"""
        memory_file = os.path.join(self.memory_dir, f'chess_memory_d{self.difficulty}.pkl')
        try:
            os.makedirs(self.memory_dir, exist_ok=True)
            
            abs_path = os.path.abspath(memory_file)
            print(f"Lưu memory vào: {abs_path}")
            
            with open(memory_file, 'wb') as f:
                data = {
                    'memory': self.memory,
                    'trained_games': self.trained_games,
                    'positions_seen': self.positions_seen
                }
                pickle.dump(data, f)
            print(f"Đã lưu thành công {len(self.memory)} vị trí vào bộ nhớ")
        except Exception as e:
            print(f"Lỗi khi lưu bộ nhớ: {e}")
            import traceback
            traceback.print_exc()

    def get_check_escape_move(self, board):
        """Tìm nước thoát chiếu"""
        print("Đang tìm nước thoát chiếu...")
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return None
        
        return random.choice(legal_moves)

    def get_intermediate_move(self, board):
        """Tìm nước đi với độ khó trung bình"""
        print("Đang tìm nước đi trung bình...")
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
            
        capturing_moves = []
        for move in legal_moves:
            if board.is_capture(move):
                capturing_moves.append(move)
        
        if capturing_moves:
            print(f"Tìm thấy {len(capturing_moves)} nước bắt quân")
            return random.choice(capturing_moves)
        
        return random.choice(legal_moves)
    
    def get_move(self, board):
        """Lấy nước đi cho AI dựa trên độ khó và trạng thái bàn cờ"""
        print(f"AI get_move được gọi với độ khó: {self.difficulty}")
        
        try:
            if hasattr(board, 'board'):
                print("Tham số là game object, chuyển sang board")
                board = board.board
                
            if not list(board.legal_moves):
                print("Không có nước đi hợp lệ")
                return None
                
            if board.is_check():
                print("AI đang bị chiếu, tìm nước thoát chiếu")
                return self.get_check_escape_move(board)
                
            if self.difficulty == 1:
                print("Chế độ dễ: chọn ngẫu nhiên")
                return self.get_random_move(board)
            elif self.difficulty == 2:
                print("Chế độ trung bình: chọn ngẫu nhiên/thông minh")
                if random.random() < 0.7:  # 70% khả năng chọn nước thông minh
                    return self.get_intermediate_move(board)
                else:
                    return self.get_random_move(board)
            else:  # difficulty == 3
                print("Chế độ khó: chọn nước thông minh")
                return self.get_smart_move(board)
        except Exception as e:
            print(f"Lỗi trong get_move: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                print("Thử chọn nước đi ngẫu nhiên do gặp lỗi")
                return self.get_random_move(board)
            except:
                print("Không thể chọn nước đi ngẫu nhiên")
                return None
    
    def get_random_move(self, board):
        """Chọn nước đi ngẫu nhiên"""
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None
    
    def get_intermediate_move(self, board):
        """Chọn nước đi với chiến thuật trung bình"""
        # Ưu tiên tấn công
        capture_moves = []
        check_moves = []
        other_moves = []
        
        for move in board.legal_moves:
            if board.is_capture(move):
                capture_moves.append(move)
            
            board.push(move)
            if board.is_check():
                check_moves.append(move)
            board.pop()
            
            other_moves.append(move)
        
        # Ưu tiên theo thứ tự: chiếu, bắt quân, di chuyển thường
        if check_moves:
            return random.choice(check_moves)
        elif capture_moves:
            return random.choice(capture_moves)
        else:
            return random.choice(other_moves)
    
    def get_smart_move(self, board, depth=3, max_time=2.0):
        """Chọn nước đi thông minh sử dụng minimax và alpha-beta pruning"""
        self.start_time = time.time()
        self.max_time = max_time
        self.nodes = 0
        
        best_move = None
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        legal_moves = list(board.legal_moves)
        random.shuffle(legal_moves)
        
        for move in legal_moves:
            if time.time() - self.start_time > self.max_time:
                break
                
            board.push(move)
            
            board_fen = board.fen()
            if board_fen in self.memory:
                score = self.memory[board_fen]
            else:
                score = -self._minimax(board, depth-1, -beta, -alpha, False)
                if self.learning_enabled:
                    # Save trạng thái mới vào bộ nhớ
                    self.memory[board_fen] = score
                    self.positions_seen += 1
            
            board.pop()
            
            # Update nước đi tốt nhất
            if score > best_score:
                best_score = score
                best_move = move
                
            # Update alpha
            alpha = max(alpha, score)
            
        return best_move if best_move else (legal_moves[0] if legal_moves else None)
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        """Thuật toán minimax với alpha-beta pruning"""
        self.nodes += 1
        
        if time.time() - self.start_time > self.max_time:
            return 0
        
        board_fen = board.fen()
        if board_fen in self.memory:
            return self.memory[board_fen]
        
        if depth == 0 or board.is_game_over():
            evaluation = self._evaluate_position(board)
            if self.learning_enabled:
                self.memory[board_fen] = evaluation
            return evaluation
        
        if maximizing:
            best_score = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                score = self._minimax(board, depth-1, alpha, beta, False)
                board.pop()
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in board.legal_moves:
                board.push(move)
                score = self._minimax(board, depth-1, alpha, beta, True)
                board.pop()
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score
    
    def _evaluate_position(self, board):
        """Đánh giá vị trí hiện tại của bàn cờ"""
        if board.is_checkmate():
            return -10000 if board.turn else 10000
        
        if board.is_stalemate():
            return 0
        
        white_pieces = sum(1 for square in chess.SQUARES if board.piece_at(square) and board.piece_at(square).color)
        black_pieces = sum(1 for square in chess.SQUARES if board.piece_at(square) and not board.piece_at(square).color)
        total_pieces = white_pieces + black_pieces
        
        value = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
                
            piece_value = self.PIECE_VALUES.get(piece.piece_type, 0)
            
            if total_pieces <= 10:  # Giai đoạn cuối
                # Khuyến khích đẩy vua địch vào góc
                if piece.piece_type == chess.KING:
                    if piece.color:  # Vua trắng
                        king_square = square
                        # Khuyến khích vua đen ở gần trung tâm trong giai đoạn cuối
                        file, rank = chess.square_file(king_square), chess.square_rank(king_square)
                        center_distance = abs(3.5 - file) + abs(3.5 - rank)
                        value += (4 - center_distance) * 10
                    else:  # Vua đen
                        king_square = square
                        # Khuyến khích đẩy vua đen ra góc trong giai đoạn cuối
                        file, rank = chess.square_file(king_square), chess.square_rank(king_square)
                        center_distance = abs(3.5 - file) + abs(3.5 - rank)
                        value -= center_distance * 10
                        
            if piece.color:  # Quân trắng
                value += piece_value
            else:  # Quân đen
                value -= piece_value
        
        if board.is_check():
            if board.turn:  # Đen vừa chiếu Trắng
                value -= 50
            else:  # Trắng vừa chiếu Đen
                value += 50
        
        mobility_white = 0
        mobility_black = 0
        
        if board.turn:  # Lượt của trắng
            mobility_white = len(list(board.legal_moves))
            board.push(chess.Move.null())  # Đi một nước null để chuyển lượt
            mobility_black = len(list(board.legal_moves))
            board.pop()
        else:  # Lượt của đen
            mobility_black = len(list(board.legal_moves))
            board.push(chess.Move.null())
            mobility_white = len(list(board.legal_moves))
            board.pop()
        
        value += (mobility_white - mobility_black) * 0.1
        
        return value
    
    def learn_from_game(self, game_moves, result):
        """Học từ một ván đấu hoàn chỉnh"""
        if not self.learning_enabled:
            print("Learning is disabled - skipping")
            return
            
        if result == "1-0":  # Trắng thắng
            reward = 1.0
        elif result == "0-1":  # Đen thắng
            reward = -1.0
        else:  # Hòa
            reward = 0.0
        
        board = chess.Board()
        
        positions = []
        
        for move_uci in game_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    positions.append(board.fen())
                    
                    board.push(move)
                else:
                    print(f"Nước đi không hợp lệ: {move_uci}")
                    return
            except Exception as e:
                print(f"Lỗi khi xử lý nước đi {move_uci}: {e}")
                return
        
        discount_factor = 0.9  
        current_reward = reward
        
        for position in reversed(positions):
            if position in self.memory:
                self.memory[position] = self.memory[position] + self.learning_rate * (current_reward - self.memory[position])
            else:
                self.memory[position] = current_reward
            
            current_reward = current_reward * discount_factor
        
        self.trained_games += 1
        
        self.save_memory()
        print(f"Đã học và lưu dữ liệu từ ván đấu (Tổng: {self.trained_games} ván, {len(self.memory)} vị trí)")
        print(f"Đường dẫn lưu: {os.path.join(self.memory_dir, f'chess_memory_d{self.difficulty}.pkl')}")
    
    def learn_from_pgn_file(self, pgn_file):
        """Học từ file PGN chứa các ván cờ"""
        if not os.path.exists(pgn_file):
            print(f"File không tồn tại: {pgn_file}")
            return
        
        try:
            games_learned = 0
            with open(pgn_file, 'r') as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                        
                    result = game.headers["Result"]
                    
                    moves = []
                    board = game.board()
                    for move in game.mainline_moves():
                        moves.append(move.uci())
                        board.push(move)
                    
                    self.learn_from_game(moves, result)
                    games_learned += 1
                    
                    if games_learned % 10 == 0:
                        print(f"Đã học {games_learned} ván cờ từ file PGN")
            
            print(f"Hoàn thành học từ file PGN: {games_learned} ván cờ")
            self.save_memory()
            
        except Exception as e:
            print(f"Lỗi khi đọc file PGN: {e}")