import pygame
import chess
import os
from src.game import ChessGame, GameMode, GameState
from src.learning_chess_ai import ChessAI
import pygame.font
from datetime import datetime
import sys
import time
import tkinter as tk

class ChessUI:
    def __init__(self, width=1000, height=700, game=None, ai=None):
        pygame.init()
        pygame.display.set_caption("Chess Game")

        self.hint_button_rect = None
        self.undo_button_rect = None
        self.resign_button_rect = None
        self.load_pgn_rect = None
        self.learning_toggle_rect = None

        # Đảm bảo chiều cao bao gồm cả không gian cho status bar
        self.status_height = 40  # Chiều cao của thanh trạng thái
    
        self.width = width
        self.height = height
    
        # Tính toán kích thước bảng cờ (hình vuông)
        self.board_size = min(width - 300, height - self.status_height)
        self.square_size = self.board_size // 8

        # Tạo cửa sổ với kích thước ban đầu
        self.screen = pygame.display.set_mode((width, height))
        # Đảm bảo kích thước cửa sổ là bội số của 8 + chiều cao status bar
        self.width = self.square_size * 8
        self.board_size = self.square_size * 8
        self.height = self.board_size + self.status_height
    
        # Tạo cửa sổ game với kích thước đã tính toán
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        # Sử dụng font hỗ trợ Unicode
        try:
            # Thử tìm font trong hệ thống hỗ trợ tiếng Việt
            available_fonts = pygame.font.get_fonts()
            unicode_fonts = ['arial', 'segoeui', 'timesnewroman', 'dejavusans', 'freesans']
        
            # Tìm font phù hợp từ danh sách
            font_name = None
            for f in unicode_fonts:
                if f.lower().replace(' ', '') in available_fonts:
                    font_name = f
                    break
        
            if font_name:
                print(f"Sử dụng font: {font_name}")
                self.font = pygame.font.SysFont(font_name, 28)
                self.small_font = pygame.font.SysFont(font_name, 20)
            else:
                # Nếu không tìm thấy font hỗ trợ, sử dụng font mặc định
                print("Không tìm thấy font Unicode, sử dụng font mặc định")
                self.font = pygame.font.SysFont(None, 28)  # Sửa lỗi typo ở đây: pygame.fzont -> pygame.font
                self.small_font = pygame.font.SysFont(None, 20)
        except:
            print("Lỗi khi tải font, sử dụng font mặc định")
            self.font = pygame.font.SysFont(None, 28)
            self.small_font = pygame.font.SysFont(None, 20)
    
        # Tải hình ảnh quân cờ
        self.pieces_images = {}
        self.load_pieces()
    
        # Màu sắc
        self.WHITE_SQUARE = (240, 217, 181)
        self.BLACK_SQUARE = (181, 136, 99)
        self.HIGHLIGHT_COLOR = (124, 252, 0, 128)  # Màu highlight nước đi hợp lệ
        self.SELECT_COLOR = (255, 255, 0, 128)     # Màu quân cờ được chọn
    
        # Trạng thái UI game
        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        self.promotion_choice = None
        
        # Tạo game và AI
        if game:
            self.game = game
        else:
            self.game = ChessGame()
            
        if ai:
            self.ai = ai
        else:
            self.ai = ChessAI(difficulty=2)
            
        # Kết hợp AI với game
        self.game.ai = self.ai
            
        self.sound_on = True
        self.load_sounds()
        
        # Khởi tạo thông tin game
        if hasattr(self.game, 'mode'):
            print(f"Khởi tạo UI với chế độ game: {self.game.mode}")
        
    def game_over_action(self):
        '''Các hành động khi kết thúc game'''
        if self.game and hasattr(self.game, 'game_over_learn'):
            # Cho AI học từ kết quả trận đấu nếu chế độ học tập được bật
            if hasattr(self.ai, 'learning_enabled') and self.ai.learning_enabled:
                print("Đang xử lý học tập sau khi game kết thúc...")
                self.game.game_over_learn()
                print("AI đã học từ ván đấu này")
                
                # Thêm hiển thị thông báo về dữ liệu học tập
                if hasattr(self.ai, 'get_learning_stats'):
                    stats = self.ai.get_learning_stats()
                    print(f"Thống kê học tập: {stats}")
            else:
                print("Học tập bị tắt - AI không học từ ván đấu này")

            #Hiển thị thông báo kết thúc game
            state = self.game.get_state()
            if state == GameState.CHECKMATE:
                winner = 'Trắng' if not self.game.current_player else 'Đen'
                self.show_message(f'{winner} thắng!')
            else:
                self.show_message('Hòa cờ!')
                
    def render(self, screen):
        """Vẽ toàn bộ giao diện"""
        # Xóa màn hình với màu nền
        screen.fill((240, 240, 240))

        # Vẽ bàn cờ
        self.draw_board(screen)
        
        # Vẽ các quân cờ
        self.draw_pieces(screen)

        # Vẽ sidebar và các nút
        self.draw_sidebar(screen)
        self.draw_learning_toggle(screen)
        self.draw_hint_button(screen)
        self.draw_load_pgn_button(screen)
        self.draw_ai_stats(screen)
        self.draw_captured_pieces(screen)

        # Vẽ ô được chọn và nước đi hợp lệ
        if self.selected_square:
            self.draw_selected_square(screen)
            if self.legal_moves:
                self.draw_legal_moves(screen)

        # Vẽ thông tin trạng thái
        self.draw_status()
        
        # Hiển thị gợi ý nếu có
        if hasattr(self, 'hint_move') and hasattr(self, 'hint_time'):
            current_time = pygame.time.get_ticks()
            if current_time - self.hint_time < 3000:
                from_square = self.hint_move.from_square
                to_square = self.hint_move.to_square
                from_x = chess.square_file(from_square) * self.square_size
                from_y = (7 - chess.square_rank(from_square)) * self.square_size
                to_x = chess.square_file(to_square) * self.square_size
                to_y = (7 - chess.square_rank(to_square)) * self.square_size
                pygame.draw.rect(screen, (0, 200, 0, 128), (from_x, from_y, self.square_size, self.square_size), 3)
                pygame.draw.rect(screen, (0, 200, 0, 128), (to_x, to_y, self.square_size, self.square_size), 3)
                pygame.draw.line(screen, (0, 200, 0), 
                                (from_x + self.square_size//2, from_y + self.square_size//2),
                                (to_x + self.square_size//2, to_y + self.square_size//2), 3)

    def load_pieces(self):
        # Mapping giữa ký hiệu quân cờ và tên file
        file_mapping = {
        'p': 'p', 'r': 'r', 'n': 'n', 'b': 'b', 'q': 'q', 'k': 'k',  # Quân đen
        'P': 'p1', 'R': 'r1', 'N': 'n1', 'B': 'b1', 'Q': 'q1', 'K': 'k1'  # Quân trắng
    }
    
        pieces = ['p', 'r', 'n', 'b', 'q', 'k', 'P', 'R', 'N', 'B', 'Q', 'K']
        loaded_pieces = 0
    
        for piece in pieces:
            try:
                # Sử dụng mapping để lấy tên file thực tế
                file_name = f'{file_mapping[piece]}.png'
                image_path = os.path.join('assets', 'images', 'pieces', file_name)
                print(f"Đang tải hình ảnh: {image_path}")
            
                self.pieces_images[piece] = pygame.transform.scale(
                    pygame.image.load(image_path),
                    (self.square_size, self.square_size)
            )
                loaded_pieces += 1
                print(f"Đã tải thành công: {file_name}")
            except Exception as e:
                print(f"Lỗi tải hình ảnh {file_mapping[piece]}.png: {e}")
    
        print(f"Đã tải {loaded_pieces}/{len(pieces)} hình ảnh quân cờ")
    
        # Nếu không tải đủ hình ảnh, tạo placeholder
        if loaded_pieces < len(pieces):
            print("Tạo placeholder cho các hình ảnh bị thiếu")
            self.create_placeholder_pieces(pieces)
    
    def create_placeholder_pieces(self, pieces):
        colors = {
            'p': (50, 50, 50), 'r': (50, 50, 50), 'n': (50, 50, 50), 
            'b': (50, 50, 50), 'q': (50, 50, 50), 'k': (50, 50, 50),
            'p1': (200, 200, 200), 'r1': (200, 200, 200), 'n1': (200, 200, 200),
            'b1': (200, 200, 200), 'q1': (200, 200, 200), 'k1': (200, 200, 200)
        }
        
        shapes = {
            'p': 'circle', 'r': 'rect', 'n': 'polygon', 
            'b': 'polygon', 'q': 'polygon', 'k': 'polygon'
        }
        
        for piece in pieces:
            surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            color = colors[piece]
            shape_type = shapes[piece.lower()]
            
            if shape_type == 'circle':
                pygame.draw.circle(
                    surface, color, 
                    (self.square_size // 2, self.square_size // 2), 
                    self.square_size // 3
                )
            elif shape_type == 'rect':
                pygame.draw.rect(
                    surface, color,
                    (self.square_size // 4, self.square_size // 4, 
                     self.square_size // 2, self.square_size // 2)
                )
            else:
                points = [
                    (self.square_size // 2, self.square_size // 6),
                    (self.square_size // 6, self.square_size // 6 * 5),
                    (self.square_size // 6 * 5, self.square_size // 6 * 5),
                ]
                pygame.draw.polygon(surface, color, points)
            
            # Vẽ text quân cờ lên hình
            text = self.small_font.render(piece, True, (255, 0, 0) if piece.islower() else (0, 0, 255))
            surface.blit(text, (self.square_size // 3, self.square_size // 3))
            
            self.pieces_images[piece] = surface

    def start_new_game(self, mode=GameMode.PLAYER_VS_PLAYER):
        self.game = ChessGame(mode=mode)
        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        print(f"Đã tạo game mới với chế độ: {mode}")  # Thêm debug
    
    def handle_event(self, event):
        """Xử lý tất cả các sự kiện từ người dùng"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Kiểm tra xem người dùng có click vào nút bật/tắt học tập không
            if hasattr(self, 'learning_toggle_rect') and self.learning_toggle_rect.collidepoint(event.pos):
                # Đảo trạng thái học tập
                if hasattr(self.ai, 'learning_enabled'):
                    self.ai.learning_enabled = not self.ai.learning_enabled
                    print(f"Chế độ học tập của AI: {'BẬT' if self.ai.learning_enabled else 'TẮT'}")
                return  # Thoát khỏi hàm vì đã xử lý sự kiện

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Kiểm tra các vùng nút đặc biệt
            if hasattr(self, 'learning_toggle_rect') and self.learning_toggle_rect.collidepoint(event.pos):
                # Xử lý nút bật/tắt học tập...
                return
                
            # Kiểm tra nút tải PGN
            if hasattr(self, 'load_pgn_rect') and self.load_pgn_rect.collidepoint(event.pos):
                print('Nút tải PNG đã được click')
                self.load_pgn_data()
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            print(f"Mouse clicked at: {mouse_pos}")  # Debug
            
            # Check game state
            if self.game.is_game_over():
                print("Game is over - handling end of game click")
                return
            
            # Xử lý nút gợi ý
            if hasattr(self, 'hint_button_rect') and self.hint_button_rect.collidepoint(mouse_pos):
                print("Hint button clicked")  # Debug
                self.show_hint()
                return
            
            # Nếu không phải các nút, xử lý bàn cờ
            if mouse_pos[0] < self.board_size and mouse_pos[1] < self.board_size:
                file = mouse_pos[0] // self.square_size
                rank = 7 - (mouse_pos[1] // self.square_size)
                square = chess.square(file, rank)
                
                # Phần còn lại của xử lý click vào bàn cờ giữ nguyên
                if self.selected_square is None:
                    piece = self.game.board.piece_at(square)
                    if piece and piece.color == self.game.current_player:
                        self.selected_square = square
                        self.legal_moves = []
                        for move in self.game.board.legal_moves:
                            if move.from_square == square:
                                self.legal_moves.append(move)
                else:
                    # Nếu đã có ô được chọn, kiểm tra xem người chơi đang muốn làm gì
                    
                    # Trường hợp 1: Chọn lại quân cờ của mình
                    piece = self.game.board.piece_at(square)
                    if piece and piece.color == self.game.current_player:
                        self.selected_square = square
                        # Lấy danh sách các nước đi hợp lệ từ ô mới
                        self.legal_moves = []
                        for move in self.game.board.legal_moves:
                            if move.from_square == square:
                                self.legal_moves.append(move)
                    
                    # Trường hợp 2: Chọn ô đích để di chuyển
                    else:
                        # Tìm nước đi hợp lệ trong danh sách
                        move = None
                        for legal_move in self.legal_moves:
                            if legal_move.to_square == square:
                                move = legal_move
                                break
                        
                        # Thực hiện nước đi nếu hợp lệ
                        if move:
                            # Kiểm tra phong cấp cho tốt
                            if self.is_promotion_move(move):
                                # Hiện hộp thoại chọn quân phong cấp
                                promotion_piece = self.show_promotion_dialog()
                                if promotion_piece:
                                    # Tạo nước đi mới với quân được phong cấp
                                    move = chess.Move(move.from_square, move.to_square, promotion=promotion_piece)
                            
                            # Thực hiện nước đi
                            success = self.game.make_move(move)
                            if success:
                                # Phát âm thanh di chuyển
                                if hasattr(self, 'move_sound'):
                                    self.move_sound.play()
                                    
                                # Kiểm tra nếu là capture move
                                captured = self.game.board.piece_at(move.to_square)
                                if captured:
                                    # Phát âm thanh capture
                                    if hasattr(self, 'capture_sound'):
                                        self.capture_sound.play()
                                
                                # Kiểm tra chiếu
                                if self.game.board.is_check():
                                    # Phát âm thanh chiếu
                                    if hasattr(self, 'check_sound'):
                                        self.check_sound.play()
                                
                                # Nếu là chế độ chơi với máy, cho máy đi
                                if self.game.mode == GameMode.PLAYER_VS_AI and not self.game.current_player:
                                    # Use a short delay before AI makes its move
                                    pygame.time.delay(300)
                                    self.make_ai_move()
                        
                        # Reset trạng thái chọn
                        self.selected_square = None
                        self.legal_moves = []
            
            # Xử lý click vào các nút trên giao diện
            elif hasattr(self, 'hint_button_rect') and self.hint_button_rect.collidepoint(event.pos):
                # Xử lý click vào nút gợi ý
                self.show_hint()
                
            elif hasattr(self, 'undo_button_rect') and self.undo_button_rect.collidepoint(event.pos):
                # Xử lý click vào nút đi lại
                self.undo_move()
                
            elif hasattr(self, 'resign_button_rect') and self.resign_button_rect.collidepoint(event.pos):
                # Xử lý click vào nút đầu hàng
                self.resign_game()
                
            elif hasattr(self, 'sound_toggle_rect') and self.sound_toggle_rect.collidepoint(event.pos):
                # Xử lý click vào nút bật/tắt âm thanh
                self.toggle_sound()
        
        # Xử lý các phím tắt
        elif event.type == pygame.KEYDOWN:
            # R: Reset game
            if event.key == pygame.K_r:
                self.reset_game()
                
            # Z: Đi lại nước đi
            elif event.key == pygame.K_z:
                self.undo_move()
                
            # H: Gợi ý nước đi
            elif event.key == pygame.K_h:
                self.show_hint()
                
            # Esc: Hủy chọn quân cờ
            elif event.key == pygame.K_ESCAPE:
                self.selected_square = None
                self.legal_moves = []
                
            # S: Bật/tắt âm thanh
            elif event.key == pygame.K_s:
                self.toggle_sound()
                
            # P: Tạm dừng game
            elif event.key == pygame.K_p:
                self.pause_game()

    def is_promotion_move(self, move):
        """Kiểm tra xem nước đi có phải là phong cấp cho tốt không"""
        piece = self.game.board.piece_at(move.from_square)
        
        if not piece or piece.piece_type != chess.PAWN:
            return False
            
        # Kiểm tra tốt trắng đến hàng 8 hoặc tốt đen đến hàng 1
        to_rank = chess.square_rank(move.to_square)
        return (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0)

    def show_promotion_dialog(self):
        """Hiển thị hộp thoại để chọn quân phong cấp"""
        # Lưu trạng thái hiện tại của bàn cờ
        screen_copy = pygame.display.get_surface().copy()
        
        # Tạo dialog
        dialog_width, dialog_height = 300, 120
        screen_width, screen_height = pygame.display.get_surface().get_size()
        
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Các quân có thể phong cấp
        promotion_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        piece_names = ["Hậu", "Xe", "Tượng", "Mã"]
        
        # Tạo font
        font = pygame.font.SysFont('Arial', 24)
        title_text = font.render("Chọn quân phong cấp:", True, (0, 0, 0))
        
        # Tạo các nút chọn
        button_width = 60
        button_height = 60
        button_spacing = 10
        buttons_total_width = button_width * len(promotion_pieces) + button_spacing * (len(promotion_pieces) - 1)
        
        button_start_x = dialog_x + (dialog_width - buttons_total_width) // 2
        button_y = dialog_y + title_text.get_height() + 10
        
        # Vòng lặp hiển thị dialog
        chosen_piece = None
        running = True
        
        while running:
            # Vẽ overlay tối
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # RGBA, alpha=128 cho hiệu ứng mờ
            pygame.display.get_surface().blit(overlay, (0, 0))
            
            # Vẽ dialog
            pygame.draw.rect(pygame.display.get_surface(), (240, 240, 240), dialog_rect)
            pygame.draw.rect(pygame.display.get_surface(), (0, 0, 0), dialog_rect, 2)
            
            # Vẽ tiêu đề
            pygame.display.get_surface().blit(title_text, 
                                            (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 10))
            
            # Vẽ các nút chọn quân
            for i, (piece, name) in enumerate(zip(promotion_pieces, piece_names)):
                button_x = button_start_x + i * (button_width + button_spacing)
                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                
                # Vẽ nút
                pygame.draw.rect(pygame.display.get_surface(), (200, 200, 200), button_rect)
                pygame.draw.rect(pygame.display.get_surface(), (0, 0, 0), button_rect, 2)
                
                # Vẽ tên quân
                text = font.render(name, True, (0, 0, 0))
                pygame.display.get_surface().blit(text, 
                                                (button_x + (button_width - text.get_width()) // 2, 
                                                button_y + (button_height - text.get_height()) // 2))
            
            pygame.display.flip()
            
            # Xử lý sự kiện
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Kiểm tra click vào nút nào
                    for i, piece in enumerate(promotion_pieces):
                        button_x = button_start_x + i * (button_width + button_spacing)
                        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                        
                        if button_rect.collidepoint(mouse_pos):
                            chosen_piece = piece
                            running = False
                            break
                            
                if event.type == pygame.KEYDOWN:
                    # Phím tắt: Q (Queen), R (Rook), B (Bishop), N (Knight)
                    if event.key == pygame.K_q:
                        chosen_piece = chess.QUEEN
                        running = False
                    elif event.key == pygame.K_r:
                        chosen_piece = chess.ROOK
                        running = False
                    elif event.key == pygame.K_b:
                        chosen_piece = chess.BISHOP
                        running = False
                    elif event.key == pygame.K_n:
                        chosen_piece = chess.KNIGHT
                        running = False
                    elif event.key == pygame.K_ESCAPE:
                        # Hủy phong cấp
                        running = False
            
        # Khôi phục màn hình
        pygame.display.get_surface().blit(screen_copy, (0, 0))
        
        return chosen_piece

    def undo_move(self):
        """Đi lại nước đi trước đó"""
        if hasattr(self.game.board, 'pop') and len(self.game.move_history) > 0:
            # Đi lại nước của người chơi
            self.game.board.pop()
            self.game.move_history.pop()
            self.game.current_player = not self.game.current_player
            
            # Trong chế độ PvE, đi lại cả nước của máy
            if self.game.game_mode == "pve" and len(self.game.move_history) > 0:
                self.game.board.pop()
                self.game.move_history.pop()
                self.game.current_player = not self.game.current_player
            
            # Reset trạng thái chọn
            self.selected_square = None
            self.legal_moves = []
            
            # Phát âm thanh nếu có
            if hasattr(self, 'undo_sound'):
                self.undo_sound.play()

    def reset_game(self):
        """Khởi động lại game"""
        # Lưu cài đặt hiện tại
        game_mode = self.game.game_mode
        difficulty = self.game.ai.difficulty if hasattr(self.game, 'ai') and self.game.ai else 2
        
        # Tạo game mới
        self.game = ChessGame(game_mode=game_mode, difficulty=difficulty)
        self.selected_square = None
        self.legal_moves = []
        
        # Phát âm thanh nếu có
        if hasattr(self, 'new_game_sound') and hasattr(self, 'sound_on') and self.sound_on:
            self.new_game_sound.play()

    def draw_ai_stats(self, screen):
        """Hiển thị thông tin thống kê về quá trình học của AI"""
        if hasattr(self.ai, 'get_learning_stats'):
            # Lấy thông tin thống kê từ AI
            stats = self.ai.get_learning_stats()
            
            # Vị trí bắt đầu vẽ
            x_pos = self.board_size + 20
            y_pos = 180
            line_height = 25
            
            # Chuẩn bị font chữ
            font = pygame.font.SysFont('Arial', 14)
            title_font = pygame.font.SysFont('Arial', 16, bold=True)
            
            # Vẽ tiêu đề
            title_text = title_font.render("THÔNG TIN HỌC TẬP", True, (0, 0, 100))
            screen.blit(title_text, (x_pos, y_pos))
            y_pos += line_height + 5
            
            # Vẽ các dòng thông tin
            info_lines = [
                f"Vị trí đã học: {stats.get('positions', 0):,}",
                f"Ván đấu đã học: {stats.get('games', 0):,}",
                f"Kích thước bộ nhớ: {stats.get('memory_size', 0):,}",
                f"Tốc độ học: {stats.get('learning_rate', 0)}"
            ]
            
            # Vẽ từng dòng thông tin
            for line in info_lines:
                text = font.render(line, True, (0, 0, 0))
                screen.blit(text, (x_pos, y_pos))
                y_pos += line_height

    def draw_hint_button(self, screen):
        """Vẽ nút gợi ý nước đi"""
        if self.game.is_game_over():
            return
            
        font = pygame.font.SysFont('Arial', 18)
        hint_text = font.render("Gợi ý", True, (255, 255, 255))

        # Vẽ nút
        self.hint_button_rect = pygame.Rect(self.board_size + 120, 550, 100, 30)
        pygame.draw.rect(screen, (50, 100, 200), self.hint_button_rect)
        screen.blit(hint_text, (self.hint_button_rect.x + 25, self.hint_button_rect.y + 5))

    def show_hint(self):
        """Hiển thị gợi ý nước đi tốt nhất"""
        print("Showing hint...")  # Debug
        if self.game.is_game_over() or not hasattr(self.game, 'ai'):
            print("Cannot show hint: Game is over or AI not available")
            return
        
        if not hasattr(self.game, 'current_player'):
            print("Cannot show hint: Game has no current_player attribute")
            return
        
        # Lưu trạng thái hiện tại
        current_player = self.game.current_player
        
        try:
            # Sử dụng AI để tìm nước đi gợi ý
            if hasattr(self.game, 'ai') and hasattr(self.game.ai, 'get_smart_move'):
                move = self.game.ai.get_smart_move(self.game, depth=2, max_time=1.0)
                print(f"AI suggested move: {move}")
            else:
                print("AI or get_smart_move method not available")
            
            if move:
                # Hiển thị gợi ý
                self.hint_move = move
                self.hint_time = pygame.time.get_ticks()  # Thời điểm hiển thị gợi ý
                print(f"Hint displayed: {move}")
            
            # Khôi phục trạng thái
            self.game.current_player = current_player
        except Exception as e:
            print(f"Error showing hint: {e}")
    def handle_click(self, pos):
        if self.game_over:
            return
            
        file = pos[0] // self.square_size
        rank = 7 - (pos[1] // self.square_size)
        square = chess.square(file, rank)
        
        # Xử lý chọn quân cờ
        if self.selected_square is None:
            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                   if move.from_square == square]
        else:
            # Xử lý di chuyển quân cờ
            for move in self.legal_moves:
                if move.to_square == square:
                    # Xử lý trường hợp phong cấp
                    if (self.game.board.piece_at(self.selected_square).piece_type == chess.PAWN and 
                        (rank == 0 or rank == 7)):
                        move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
                    
                    # Thực hiện nước đi
                    if self.game.make_move(move):
                        # Kiểm tra kết thúc trò chơi
                        if self.game.get_state() in [GameState.CHECKMATE, GameState.STALEMATE, GameState.DRAW]:
                            self.game_over = True
                        
                        # Nếu là chế độ chơi với máy, cho máy đi
                        if not self.game_over and self.game.mode == GameMode.PLAYER_VS_AI and self.game.current_player == chess.BLACK:
                            self.make_ai_move()
                    
                    self.selected_square = None
                    self.legal_moves = []
                    return            
            
            # Nếu click vào quân khác cùng màu
            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                   if move.from_square == square]
            else:
                self.selected_square = None
                self.legal_moves = []    
                
    def make_ai_move(self):
        """Yêu cầu AI thực hiện nước đi"""
        if self.game.is_game_over():
            return
            
        # Set flag to indicate AI is thinking
        self.game.ai_thinking = True
        
        try:
            # Hiển thị trạng thái "đang suy nghĩ"
            self.render(self.screen)
            pygame.display.flip()
            
            start_time = time.time()  # Bắt đầu đo thời gian
            
            # Lấy nước đi từ AI
            ai_move = self.ai.get_move(self.game.board)
            
            elapsed_time = time.time() - start_time
            # Nếu AI trả về quá nhanh, tạm dừng một chút để người dùng thấy trạng thái "đang suy nghĩ"
            if elapsed_time < 0.5:
                pygame.time.wait(int((0.5 - elapsed_time) * 1000))
            
            # Thực hiện nước đi nếu AI trả về một nước đi hợp lệ
            if ai_move:
                success = self.game.make_move(ai_move)
                print(f"AI đã đi: {ai_move}, thành công: {success}")
                
                # Kiểm tra xem trò chơi đã kết thúc chưa sau nước đi của AI
                if self.game.is_game_over():
                    self.game_over_action()
            else:
                print("AI không tìm được nước đi hợp lệ")
                
        except Exception as e:
            print(f"Lỗi trong khi AI đang suy nghĩ: {str(e)}")
        finally:
            # Reset flag
            self.game.ai_thinking = False

    def draw_load_pgn_button(self, screen):
        """Vẽ nút tải dữ liệu PGN để huấn luyện AI"""
        if hasattr(self.ai, 'learn_from_pgn_file') and self.game.mode == GameMode.PLAYER_VS_AI:
            # Xác định vị trí và kích thước nút
            button_rect = pygame.Rect(self.board_size + 20, 300, 160, 40)
            
            # Vẽ hình chữ nhật làm nền nút
            pygame.draw.rect(screen, (100, 100, 220), button_rect)
            pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)  # Viền đen
            
            # Chuẩn bị và vẽ văn bản
            font = pygame.font.SysFont('Arial', 16, bold=True)
            text = font.render("TẢI DỮ LIỆU PGN", True, (255, 255, 255))
            
            # Canh giữa văn bản trong nút
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
            
            # Lưu lại thông tin vị trí nút
            self.load_pgn_rect = button_rect

    def load_pgn_data(self):
        """Mở hộp thoại chọn file và tải dữ liệu PGN để huấn luyện AI"""
        import tkinter as tk
        from tkinter import filedialog
        
        # Tạo cửa sổ Tkinter và ẩn đi
        root = tk.Tk()
        root.withdraw()
        
        # Mở hộp thoại chọn file
        file_path = filedialog.askopenfilename(
            title="Chọn file PGN",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        
        # Nếu người dùng chọn file
        if file_path:
            print(f"Đang tải dữ liệu từ file: {file_path}")
            
            # Hiển thị thông báo đang tải
            font = pygame.font.SysFont('Arial', 20)
            text = font.render("Đang tải dữ liệu PGN...", True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.board_size // 2, self.board_size // 2))
            
            overlay = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 180))  # Nền trắng mờ
            
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            
            try:
                # Gọi phương thức học từ file PGN
                self.ai.learn_from_pgn_file(file_path)
                message = "Đã hoàn thành tải dữ liệu!"
            except Exception as e:
                message = f"Lỗi khi tải: {str(e)}"
                print(f"Lỗi: {e}")
            
            # Hiển thị kết quả
            text = font.render(message, True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.board_size // 2, self.board_size // 2))
            
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            
            # Đợi một chút trước khi tiếp tục
            pygame.time.wait(2000)

    def draw_board(self, screen=None):
        screen = screen or self.screen  # Sử dụng tham số screen nếu được cung cấp, nếu không dùng self.screen
        for rank in range(8):
            for file in range(8):
                # Vẽ ô cờ
                color = self.WHITE_SQUARE if (rank + file) % 2 == 0 else self.BLACK_SQUARE
                pygame.draw.rect(
                    screen, 
                    color, 
                    (file * self.square_size, (7 - rank) * self.square_size, 
                    self.square_size, self.square_size)
                )
                
                # Đánh dấu ô được chọn
                square = chess.square(file, rank)
                if square == self.selected_square:
                    highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    highlight.fill(self.SELECT_COLOR)
                    screen.blit(highlight, (file * self.square_size, (7 - rank) * self.square_size))
                
                # Đánh dấu các nước đi hợp lệ
                for move in self.legal_moves:
                    if move.to_square == square:
                        highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                        highlight.fill(self.HIGHLIGHT_COLOR)
                        screen.blit(highlight, (file * self.square_size, (7 - rank) * self.square_size))
                        break

    def draw_captured_pieces(self, screen):
        """Vẽ các quân cờ đã bị bắt"""
        # Tạo font
        font = pygame.font.SysFont('Arial', 16)
        
        # Vị trí hiển thị
        white_x = self.board_size + 20
        black_x = self.board_size + 150
        y = 300
        
        # Tiêu đề
        white_text = font.render("Quân trắng bị bắt:", True, (0, 0, 0))
        black_text = font.render("Quân đen bị bắt:", True, (0, 0, 0))
        screen.blit(white_text, (white_x, y))
        screen.blit(black_text, (black_x, y))
        
        # Đếm số lượng quân bị bắt theo loại
        white_captured = {piece_type: 0 for piece_type in range(1, 7)}  # 1-6 cho các loại quân
        black_captured = {piece_type: 0 for piece_type in range(1, 7)}
        
        for piece, captured_by_white in self.game.captured_pieces:
            if captured_by_white:  # Quân đen bị bắt bởi quân trắng
                black_captured[piece.piece_type] += 1
            else:  # Quân trắng bị bắt bởi quân đen
                white_captured[piece.piece_type] += 1
        
        # Vẽ các quân bị bắt
        y += 25
        
        # Ánh xạ từ piece_type sang ký hiệu hiển thị
        symbols = {
            chess.PAWN: "P",
            chess.KNIGHT: "N",
            chess.BISHOP: "B",
            chess.ROOK: "R",
            chess.QUEEN: "Q",
            chess.KING: "K"
        }
        
        for piece_type, count in white_captured.items():
            if count > 0:
                text = font.render(f"{symbols[piece_type]} x {count}", True, (0, 0, 0))
                screen.blit(text, (white_x, y))
                y += 20
        
        y = 325  # Reset y cho quân đen
        for piece_type, count in black_captured.items():
            if count > 0:
                text = font.render(f"{symbols[piece_type]} x {count}", True, (0, 0, 0))
                screen.blit(text, (black_x, y))
                y += 20

    def draw_pieces(self, screen=None):
        screen = screen or self.screen  # Sử dụng tham số screen nếu được cung cấp, nếu không dùng self.screen
        if hasattr(self.game, 'board'):
            board_state = self.game.board
            for rank in range(8):
                for file in range(8):
                    square = chess.square(file, rank)
                    piece = board_state.piece_at(square)
                    if piece:
                        piece_symbol = piece.symbol()
                        if piece_symbol in self.pieces_images:
                            screen.blit(
                                self.pieces_images[piece_symbol],
                                (file * self.square_size, (7 - rank) * self.square_size)
                            )
        if hasattr(self.game, 'ai_thinking') and self.game.ai_thinking:
            # Tạo hiệu ứng mờ
            overlay = pygame.Surface((self.board_size, 60), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # Nền đen mờ
            
            # Vị trí hiển thị thông báo
            screen.blit(overlay, (0, self.board_size // 2 - 30))
            
            # Vẽ văn bản
            font = pygame.font.SysFont('Arial', 24, bold=True)
            text = font.render("AI ĐANG SUY NGHĨ...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.board_size // 2, self.board_size // 2))
            screen.blit(text, text_rect)
            
            # Vẽ dấu chấm động để thể hiện đang xử lý
            current_time = pygame.time.get_ticks()
            dots = "." * ((current_time // 500) % 4)
            dots_text = font.render(dots, True, (255, 255, 255))
            screen.blit(dots_text, (text_rect.right + 5, text_rect.y))

    def reset_game(self):
        """Khởi động lại game"""
        # Lưu cài đặt hiện tại
        game_mode = self.game.game_mode
        difficulty = self.game.ai.difficulty if hasattr(self.game, 'ai') and self.game.ai else 2
        
        # Tạo game mới
        self.game = ChessGame(game_mode=game_mode, difficulty=difficulty)
        self.selected_square = None
        self.legal_moves = []
        
        # Phát âm thanh nếu có
        if hasattr(self, 'new_game_sound'):
            self.new_game_sound.play()

    def resign_game(self):
        """Đầu hàng trong game hiện tại"""
        if self.game.is_game_over():
            return
            
        # Đánh dấu game kết thúc bằng cách cho vua của người chơi hiện tại chiếu bí
        # Đây là giải pháp đơn giản hơn là sửa đổi cấu trúc game để thêm trạng thái resign
        current_player = self.game.current_player
        winner = "Đen" if current_player else "Trắng"
        
        # Hiển thị thông báo
        self.show_message(f"{winner} thắng do đối phương đầu hàng!")
        
        # Để AI học từ kết quả này
        if hasattr(self.game, 'game_over_learn'):
            self.game.game_over_learn()
            
    def toggle_sound(self):
        """Bật/tắt âm thanh"""
        if hasattr(self, 'sound_on'):
            self.sound_on = not self.sound_on
            
            # Điều chỉnh volume cho tất cả âm thanh
            volume = 1.0 if self.sound_on else 0.0
            if hasattr(self, 'move_sound'):
                self.move_sound.set_volume(volume)
            if hasattr(self, 'capture_sound'):
                self.capture_sound.set_volume(volume)
            if hasattr(self, 'check_sound'):
                self.check_sound.set_volume(volume)
            if hasattr(self, 'new_game_sound'):
                self.new_game_sound.set_volume(volume)
            if hasattr(self, 'undo_sound'):
                self.undo_sound.set_volume(volume)
        else:
            # Khởi tạo âm thanh nếu chưa có
            self.sound_on = True
            self.load_sounds()
            
    def load_sounds(self):
        """Tải các âm thanh cho game"""
        if pygame.mixer.get_init():
            try:
                self.move_sound = pygame.mixer.Sound("assets/sounds/move.wav")
                self.capture_sound = pygame.mixer.Sound("assets/sounds/capture.wav")
                self.check_sound = pygame.mixer.Sound("assets/sounds/check.wav")
                self.new_game_sound = pygame.mixer.Sound("assets/sounds/new_game.wav")
                self.undo_sound = pygame.mixer.Sound("assets/sounds/undo.wav")
            except:
                print("Không thể tải âm thanh. Game sẽ chạy không có âm thanh.")
                
    def pause_game(self):
        """Tạm dừng game"""
        # Lưu trạng thái hiện tại
        screen_copy = pygame.display.get_surface().copy()
        
        # Tạo overlay cho màn hình tạm dừng
        screen_width, screen_height = pygame.display.get_surface().get_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # RGBA, alpha=128 cho hiệu ứng mờ
        
        # Tạo font
        font = pygame.font.SysFont('Arial', 36)
        pause_text = font.render("GAME PAUSED", True, (255, 255, 255))
        continue_text = font.render("Press any key to continue", True, (255, 255, 255))
        
        # Vị trí hiển thị
        pause_x = (screen_width - pause_text.get_width()) // 2
        pause_y = (screen_height - pause_text.get_height()) // 2 - 20
        
        continue_x = (screen_width - continue_text.get_width()) // 2
        continue_y = pause_y + pause_text.get_height() + 20
        
        # Hiển thị màn hình tạm dừng
        pygame.display.get_surface().blit(overlay, (0, 0))
        pygame.display.get_surface().blit(pause_text, (pause_x, pause_y))
        pygame.display.get_surface().blit(continue_text, (continue_x, continue_y))
        pygame.display.flip()
        
        # Đợi người dùng nhấn phím để tiếp tục
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    paused = False
        
        # Khôi phục màn hình
        pygame.display.get_surface().blit(screen_copy, (0, 0))
        pygame.display.flip()
        
    def draw_status(self):
        """Updated status bar display"""
        status_text = ""
        
        if self.game.is_game_over():
            game_state = self.game.get_state()
            if game_state == GameState.CHECKMATE:
                winner = "Trắng" if not self.game.current_player else "Đen"
                status_text = f"{winner} thắng! - Chiếu bí!"
            elif game_state == GameState.STALEMATE:
                status_text = "Hòa cờ - Bất phân thắng bại"
            else:
                status_text = "Hòa cờ"
        else:
            current_player = "Trắng" if self.game.current_player else "Đen"
            status_text = f"Lượt của {current_player}"
            if self.game.board.is_check():
                status_text += " - CHIẾU!"
    
        # Vẽ nền cho status bar
        status_bar_rect = pygame.Rect(0, self.board_size, self.width, self.status_height)
        pygame.draw.rect(self.screen, (240, 240, 240), status_bar_rect)
    
        # Vẽ text trạng thái
        status_surface = self.font.render(status_text, True, (0, 0, 0))
        self.screen.blit(status_surface, (10, self.board_size + (self.status_height - status_surface.get_height()) // 2))
    
    def draw_game_menu(self):
        self.screen.fill((200, 200, 200))
        # Điều chỉnh kích thước và vị trí của tiêu đề
        title = self.font.render("CHESS GAME", True, (0, 0, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, self.height // 6))
    
        # Điều chỉnh kích thước nút
        button_width = min(200, self.width * 0.6)
        button_height = min(50, self.height * 0.1)
    
        # Tạo các nút
        pvp_button = pygame.Rect(
            self.width // 2 - button_width // 2, 
            self.height // 2 - button_height - 20, 
            button_width, button_height
        )
        pve_button = pygame.Rect(
            self.width // 2 - button_width // 2, 
            self.height // 2 + 20, 
            button_width, button_height
        )
    
        pygame.draw.rect(self.screen, (100, 100, 200), pvp_button)
        pygame.draw.rect(self.screen, (100, 200, 100), pve_button)
    
        pvp_text = self.font.render("Nguoi - Nguoi", True, (0, 0, 0))
        pve_text = self.font.render("Nguoi - May", True, (0, 0, 0))
    
        self.screen.blit(
            pvp_text, 
            (pvp_button.centerx - pvp_text.get_width() // 2,
            pvp_button.centery - pvp_text.get_height() // 2)
        )
        self.screen.blit(
            pve_text, 
            (pve_button.centerx - pve_text.get_width() // 2,
            pve_button.centery - pve_text.get_height() // 2)
        )
    
        return pvp_button, pve_button
    
    def draw_game_over_screen(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
    
        game_state = self.game.get_state()
        if game_state == GameState.CHECKMATE:
            winner = "Trang" if not self.game.current_player else "Den"
            message = f"{winner} thang! - Chieu bi!"
        elif game_state == GameState.STALEMATE:
            message = "Hoa co - Bat phan thang bai"
        else:
            message = "Hoa co"
    
        game_over_font = pygame.font.SysFont('Arial', max(24, int(32 * (self.width / 800))))
        text = game_over_font.render(message, True, (255, 255, 255))
        self.screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
    
        restart_text = game_over_font.render("Nhan R de choi lai", True, (255, 255, 255))
        self.screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2))
    
        menu_text = game_over_font.render("Nhan M de ve Menu", True, (255, 255, 255))
        self.screen.blit(menu_text, (self.width // 2 - menu_text.get_width() // 2, self.height // 2 + 50))
    
    def draw_sidebar(self, screen):
        """Vẽ thông tin bên lề"""
        sidebar_rect = pygame.Rect(self.board_size, 0, self.width - self.board_size, self.height)
        pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
    
        # Thông tin game
        if self.game:
            font = pygame.font.SysFont('Arial', 16)
            title = font.render("Các nước đi gần đây:", True, (0, 0, 0))
            screen.blit(title, (self.board_size + 20, 400))
        
            y = 425
            # Hiển thị tối đa 5 nước đi gần nhất
            for i in range(1, min(6, len(self.game.move_history) + 1)):
                move = self.game.move_history[-i]
                move_text = f"{len(self.game.move_history) - i + 1}. {move}"
                text = font.render(move_text, True, (50, 50, 50))
                screen.blit(text, (self.board_size + 30, y))
                y += 20

    def show_message(self, message, duration=3000):
        """Hiển thị thông báo trên màn hình"""
        font = pygame.font.SysFont('Arial', 24)
        text = font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        
        pygame.time.wait(duration)
        
    def draw_selected_square(self, screen):
        """Vẽ ô được chọn"""
        file = chess.square_file(self.selected_square)
        rank = chess.square_rank(self.selected_square)
        highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        highlight.fill(self.SELECT_COLOR)
        screen.blit(highlight, (file * self.square_size, (7 - rank) * self.square_size))
    
    def draw_legal_moves(self, screen):
        """Vẽ các nước đi hợp lệ"""
        for move in self.legal_moves:
            to_square = move.to_square
            file = chess.square_file(to_square)
            rank = chess.square_rank(to_square)
            highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight.fill(self.HIGHLIGHT_COLOR)
            screen.blit(highlight, (file * self.square_size, (7 - rank) * self.square_size))
    
    def draw_learning_toggle(self, screen):
        """Vẽ nút bật/tắt chế độ học tập của AI"""
        # Chỉ hiển thị nút nếu đang trong chế độ người chơi với AI và AI có thuộc tính learning_enabled
        if hasattr(self.ai, 'learning_enabled') and self.game.mode == GameMode.PLAYER_VS_AI:
            # Xác định vị trí và kích thước nút
            button_rect = pygame.Rect(self.board_size + 20, 120, 160, 40)
            
            # Màu nút phụ thuộc vào trạng thái: xanh lá nếu bật, đỏ nếu tắt
            button_color = (0, 200, 0) if self.ai.learning_enabled else (200, 0, 0)
            
            # Vẽ hình chữ nhật làm nền nút
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)  # Viền đen
            
            # Chuẩn bị và vẽ văn bản
            font = pygame.font.SysFont('Arial', 16, bold=True)
            text = font.render("HỌC TẬP: " + ("BẬT" if self.ai.learning_enabled else "TẮT"), True, (255, 255, 255))
            
            # Canh giữa văn bản trong nút
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
            
            # Lưu lại thông tin vị trí nút để xử lý sự kiện click chuột
            self.learning_toggle_rect = button_rect

    def draw_game_state(self, screen, state):
        """Vẽ trạng thái game"""
        message = ""
        if state == GameState.CHECKMATE:
            winner = "Trắng" if not self.game.current_player else "Đen"
            message = f"{winner} thắng! - Chiếu bí!"
        elif state == GameState.STALEMATE:
            message = "Hòa cờ - Bất phân thắng bại"
        else:
            message = "Hòa cờ"
        
        font = pygame.font.SysFont('Arial', 24)
        text = font.render(message, True, (200, 0, 0))
        screen.blit(text, (self.board_size + 20, 200))
    
    def run(self):
        running = True
        show_menu = True
        pvp_button, pve_button = self.draw_game_menu()
        
        try:  # Add error handling for the main game loop
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        if show_menu:
                            if pvp_button.collidepoint(pos):
                                self.start_new_game(mode=GameMode.PLAYER_VS_PLAYER)
                                show_menu = False
                            elif pve_button.collidepoint(pos):
                                self.start_new_game(mode=GameMode.PLAYER_VS_AI)
                                show_menu = False
                        else:
                            self.handle_event(event)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.start_new_game(mode=self.game.mode)
                        elif event.key == pygame.K_m:
                            show_menu = True
                        else:
                            self.handle_event(event)
                
                # Update and render game
                if show_menu:
                    self.draw_game_menu()
                else:
                    # Render the complete game state
                    self.render(self.screen)
                    
                    # If game over, show game over screen
                    if self.game.is_game_over():
                        self.game_over = True
                        self.draw_game_over_screen()
                
                pygame.display.flip()
                self.clock.tick(60)
        
        except Exception as e:
            # Show error information
            print(f"Error in game loop: {e}")
            import traceback
            traceback.print_exc()
            
            # Display error message on screen for visibility
            self.show_message(f"Game error: {str(e)}", duration=5000)
        
        finally:
            pygame.quit()
