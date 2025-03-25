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
    def __init__(self, width=1200, height=700, game=None, ai=None):
        pygame.init()
        pygame.display.set_caption("Chess Game")

        self.hint_button_rect = None
        self.undo_button_rect = None
        self.resign_button_rect = None
        self.load_pgn_rect = None
        self.learning_toggle_rect = None

        # Chiều cao của thanh trạng thái
        self.status_height = 40  
        
        # Kích thước cơ bản
        self.square_size = 80  # Kích thước mỗi ô cờ
        self.board_size = self.square_size * 8  # Kích thước bàn cờ (640px)
        
        # Thêm không gian cho sidebar (tối thiểu 300px)
        sidebar_width = 300
        
        # Tính toán kích thước cửa sổ TỔNG THỂ
        self.width = self.board_size + sidebar_width  # 640px + 300px = 940px
        self.height = self.board_size + self.status_height  # 640px + 40px = 680px
        
        # Tạo cửa sổ với kích thước đã tính toán
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
                self.font = pygame.font.SysFont(None, 28)
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
        
        # Biến trạng thái cho menu
        self.in_menu = True
        
    def game_over_action(self):
        '''Các hành động khi kết thúc game'''
        # Đặt cờ game_over để ngăn vòng lặp vô hạn
        self.game_over = True
        
        try:
            # Giới hạn thời gian học tập
            if hasattr(self.ai, 'learning_enabled') and self.ai.learning_enabled:
                print("Đang xử lý học tập sau khi game kết thúc...")
                import threading
                def learn_with_timeout():
                    try:
                        self.game.game_over_learn()
                        print("AI đã học từ ván đấu này")
                    except Exception as e:
                        print(f"Lỗi học tập: {e}")
                
                # Học trong thread riêng với timeout
                learn_thread = threading.Thread(target=learn_with_timeout)
                learn_thread.daemon = True 
                learn_thread.start()
                learn_thread.join(timeout=1.0)  
        except Exception as e:
            print(f"Lỗi xử lý game over: {e}")

        # Lấy trạng thái game
        state = self.game.get_state()
        
        # Hiển thị thông báo phù hợp với từng trạng thái
        if state == GameState.CHECKMATE:
            winner = 'White' if not self.game.current_player else 'Black'
            self.show_message(f'{winner} wins!')
        elif state == GameState.STALEMATE:
            # Đảm bảo hiển thị thông báo cho trường hợp Stalemate
            self.show_message('Draw by Stalemate!', duration=3000)
        else:
            self.show_message('Draw!') 
        
        # Đảm bảo màn hình kết thúc game được hiển thị
        self.render(self.screen)

    def draw_background(self, screen):
        """Tạo nền gradient cho giao diện"""
        # Gradient từ xanh nhạt đến trắng
        color1 = (220, 240, 255)  # Xanh nhạt
        color2 = (240, 240, 240)  # Trắng
        
        # Vẽ gradient dọc
        height = screen.get_height()
        for y in range(height):
            # Tính toán màu cho từng dòng
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))
                
    def render(self, screen):
        """Vẽ toàn bộ giao diện"""
        # Xóa màn hình
        screen.fill((240, 240, 240))
        
        # Vẽ bàn cờ
        self.draw_board(screen)
        
        # Vẽ quân cờ
        self.draw_pieces(screen)
        
        # Vẽ nước đi hợp lệ nếu đã chọn quân
        if hasattr(self, 'selected_square') and self.selected_square is not None:
            if hasattr(self, 'legal_moves') and self.legal_moves:
                self.draw_legal_moves(screen)
        
        # ĐẢM BẢO vẽ sidebar
        self.draw_sidebar(screen)
        
        # Cập nhật màn hình
        pygame.display.flip()

    def draw_board(self, screen):
        """Vẽ bàn cờ vua với hai màu xen kẽ"""
        # Màu cho các ô trên bàn cờ
        light_square = (240, 217, 181)  # Màu sáng (be nhạt)
        dark_square = (181, 136, 99)    # Màu tối (nâu)
        
        # Kích thước mỗi ô vuông
        square_size = self.square_size
        
        # Vẽ các ô vuông
        for row in range(8):
            for col in range(8):
                # Xác định màu ô (xen kẽ)
                color = light_square if (row + col) % 2 == 0 else dark_square
                
                # Vẽ ô vuông
                square_rect = pygame.Rect(col * square_size, row * square_size, 
                                        square_size, square_size)
                pygame.draw.rect(screen, color, square_rect)
        
        # Vẽ viền bàn cờ
        board_rect = pygame.Rect(0, 0, 8 * square_size, 8 * square_size)
        pygame.draw.rect(screen, (0, 0, 0), board_rect, 2)
        
        # Vẽ tọa độ bàn cờ (a-h, 1-8)
        font = pygame.font.SysFont('Arial', 12)
        
        # Chữ cái (a-h) cho cột
        for col in range(8):
            label = chr(ord('a') + col)
            text = font.render(label, True, (0, 0, 0))
            
            # Đặt tọa độ ở dưới cùng của cột
            x = col * square_size + square_size // 2 - text.get_width() // 2
            y = 8 * square_size - 15
            
            screen.blit(text, (x, y))
        
        # Số (1-8) cho hàng
        for row in range(8):
            label = str(8 - row)
            text = font.render(label, True, (0, 0, 0))
            
            # Đặt tọa độ ở bên phải của hàng
            x = 8 * square_size - 15
            y = row * square_size + square_size // 2 - text.get_height() // 2
            
            screen.blit(text, (x, y))
    
    def draw_selected_square(self, screen):
        """Tô sáng ô vuông đã chọn"""
        if self.selected_square is None:
            return
            
        # Tính toán vị trí pixel của ô được chọn
        file = chess.square_file(self.selected_square)
        rank = 7 - chess.square_rank(self.selected_square)
        
        # Vẽ viền nhấn mạnh cho ô được chọn
        square_rect = pygame.Rect(file * self.square_size, rank * self.square_size,
                                self.square_size, self.square_size)
        pygame.draw.rect(screen, (255, 255, 0), square_rect, 3)

    def draw_pieces(self, screen=None):
        """Vẽ các quân cờ trên bàn cờ"""
        if screen is None:
            screen = self.screen
            
        # Đảm bảo đã tải hình ảnh quân cờ
        if not hasattr(self, 'piece_images') or not self.piece_images:
            self.load_pieces()
        
        # Kích thước mỗi ô vuông
        square_size = self.square_size
        
        # Duyệt qua toàn bộ bàn cờ
        for square in chess.SQUARES:
            piece = self.game.board.piece_at(square)
            if not piece:
                continue
                
            # Tính toán vị trí pixel
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            
            x = file * square_size
            y = rank * square_size
            
            # Xác định hình ảnh quân cờ
            color = "w" if piece.color else "b"
            piece_type = chess.piece_symbol(piece.piece_type).lower()
            piece_key = color + piece_type
            
            if piece_key in self.piece_images:
                # Vẽ quân cờ
                piece_img = self.piece_images[piece_key]
                
                # Tính vị trí để quân cờ nằm giữa ô
                piece_x = x + (square_size - piece_img.get_width()) // 2
                piece_y = y + (square_size - piece_img.get_height()) // 2
                
                screen.blit(piece_img, (piece_x, piece_y))
            else:
                print(f"Không tìm thấy hình ảnh cho quân cờ: {piece_key}")
        
        # Hiển thị thông báo AI đang suy nghĩ nếu đang trong trạng thái đó
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

    def draw_legal_moves(self, screen):
        """Hiển thị các nước đi hợp lệ cho quân cờ đã chọn"""
        # Màu hiển thị cho nước đi hợp lệ
        move_color = (0, 255, 0, 100)  # Xanh lá mờ
        capture_color = (255, 0, 0, 120)  # Đỏ mờ
        
        # Vẽ dấu hiệu cho từng nước đi hợp lệ
        for move in self.legal_moves:
            # Lấy tọa độ đích
            file = chess.square_file(move.to_square)
            rank = 7 - chess.square_rank(move.to_square)
            
            # Tính toán vị trí pixel
            x = file * self.square_size
            y = rank * self.square_size
            
            # Xác định xem đây có phải là nước bắt quân không
            is_capture = self.game.board.is_capture(move)
            color = capture_color if is_capture else move_color
            
            if is_capture:
                # Vẽ hình viền đỏ cho nước bắt quân
                pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(x, y, self.square_size, self.square_size), 3)
            else:
                # Vẽ hình tròn nhỏ cho nước đi thường
                center_x = x + self.square_size // 2
                center_y = y + self.square_size // 2
                pygame.draw.circle(screen, (0, 200, 0), (center_x, center_y), self.square_size // 8)


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
        if event.type == pygame.QUIT:
            return False  # Thoát game
        
        # Xử lý khi game over
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Phím R - chơi lại
                    self.reset_game()
                    self.game_over = False
                    return True
                elif event.key == pygame.K_m:  # Phím M - về menu
                    self.in_menu = True
                    self.game_over = False
                    return True
            return True
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Xử lý click vào các nút
            
            # Nút học tập
            if hasattr(self, 'learning_toggle_rect') and self.learning_toggle_rect.collidepoint(event.pos):
                if hasattr(self.ai, 'learning_enabled'):
                    self.ai.learning_enabled = not self.ai.learning_enabled
                    print(f"Trạng thái học tập: {'BẬT' if self.ai.learning_enabled else 'TẮT'}")
                return True
                
            # Nút tải PGN
            if hasattr(self, 'load_pgn_rect') and self.load_pgn_rect.collidepoint(event.pos):
                self.load_pgn_data()
                return True
                
            # Nút gợi ý
            if hasattr(self, 'hint_button_rect') and self.hint_button_rect.collidepoint(event.pos):
                self.show_hint()
                return True
                
            # Nút đi lại
            if hasattr(self, 'undo_button_rect') and self.undo_button_rect.collidepoint(event.pos):
                self.undo_move()
                return True
                
            # Nút reset
            if hasattr(self, 'reset_button_rect') and self.reset_button_rect.collidepoint(event.pos):
                self.reset_game()
                return True
                
            # Xử lý click vào bàn cờ nếu game chưa kết thúc
            if not self.game.is_game_over() and event.pos[0] < self.board_size and event.pos[1] < self.board_size:
                self.handle_click(event.pos)
                return True
        
        # Xử lý phím tắt
        if event.type == pygame.KEYDOWN:
            # R: Reset game
            if event.key == pygame.K_r:
                self.reset_game()
                return True
                
            # Z: Đi lại nước đi
            if event.key == pygame.K_z:
                self.undo_move()
                return True
                
            # H: Gợi ý nước đi
            if event.key == pygame.K_h:
                self.show_hint()
                return True
                
            # P: Tạm dừng game
            if event.key == pygame.K_p:
                self.pause_game()
                return True
                
            # M: Về menu chính
            if event.key == pygame.K_m:
                # Hiển thị menu chính (nếu có)
                if hasattr(self, 'show_menu'):
                    self.show_menu()
                    return True
        
        return True  # Tiếp tục game

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

    def draw_ai_stats(self, screen, x, y):
        """Hiển thị thông tin thống kê về AI"""
        # Lấy thông tin từ AI
        stats = self.ai.get_learning_stats()
        
        # Vẽ khung thông tin
        stats_rect = pygame.Rect(x, y, 200, 130)
        pygame.draw.rect(screen, (240, 240, 255), stats_rect)
        pygame.draw.rect(screen, (100, 100, 150), stats_rect, 1)
        
        # Vẽ tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("THỐNG KÊ AI", True, (0, 0, 100))
        screen.blit(title, (x + 10, y + 10))
        
        # Vẽ các thông tin
        font = pygame.font.SysFont('Arial', 12)
        y_offset = y + 35
        line_height = 20
        
        info_lines = [
            f"Vị trí đã học: {stats.get('positions', 0):,}",
            f"Ván đấu đã học: {stats.get('games', 0):,}",
            f"Kích thước bộ nhớ: {stats.get('memory_size', 0):,}",
            f"Tốc độ học: {stats.get('learning_rate', 0)}"
        ]
        
        for line in info_lines:
            text = font.render(line, True, (0, 0, 0))
            screen.blit(text, (x + 10, y_offset))
            y_offset += line_height

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
        """Xử lý sự kiện nhấp chuột trên bàn cờ"""
        if self.game.is_game_over() or (self.game.game_mode == "pve" and not self.game.current_player):
            # Không xử lý click nếu game kết thúc hoặc đang đợi AI
            return
        
        # Chuyển đổi vị trí pixel thành tọa độ bàn cờ
        file = pos[0] // self.square_size
        rank = 7 - (pos[1] // self.square_size)
        
        # Kiểm tra tọa độ hợp lệ
        if not (0 <= file < 8 and 0 <= rank < 8):
            return
            
        square = chess.square(file, rank)
        
        # Trường hợp 1: Chọn quân cờ
        if self.selected_square is None:
            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                if move.from_square == square]
                
                # Hiệu ứng âm thanh khi chọn quân (nếu có)
                if hasattr(self, 'play_sound'):
                    self.play_sound('select')
                    
                print(f"Đã chọn quân tại {chess.square_name(square)}")
                
        # Trường hợp 2: Chọn ô đích hoặc bỏ chọn
        else:
            # Nếu nhấp vào quân cùng màu khác, chọn quân đó thay thế
            if square != self.selected_square and self.game.board.piece_at(square) and \
            self.game.board.piece_at(square).color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                if move.from_square == square]
                
                # Hiệu ứng âm thanh khi chọn quân (nếu có)
                if hasattr(self, 'play_sound'):
                    self.play_sound('select')
                    
                print(f"Đã chọn lại quân tại {chess.square_name(square)}")
                return
            
            # Tìm nước đi phù hợp
            move = None
            for legal_move in self.legal_moves:
                if legal_move.to_square == square:
                    move = legal_move
                    break
            
            # Nếu đã tìm thấy nước đi hợp lệ
            if move:
                # Kiểm tra xem có phải là nước phong cấp không
                if self.is_promotion_move(move):
                    promotion_piece = self.show_promotion_dialog()
                    if promotion_piece:
                        move = chess.Move(move.from_square, move.to_square, promotion=promotion_piece)
                    else:
                        # Người chơi hủy chọn quân phong cấp
                        self.selected_square = None
                        self.legal_moves = []
                        return
                
                # Hiệu ứng di chuyển quân cờ
                if hasattr(self, 'animate_move'):
                    self.animate_move(move)
                
                # Thực hiện nước đi
                success = self.game.make_move(move)
                
                if success:
                    # Hiệu ứng âm thanh khi di chuyển (nếu có)
                    if hasattr(self, 'play_sound'):
                        captured = self.game.board.is_capture(move)
                        self.play_sound('capture' if captured else 'move')
                    
                    # Kiểm tra xem game đã kết thúc chưa
                    if self.game.is_game_over():
                        # Xử lý kết thúc game, bao gồm cả stalemate
                        self.game_over = True
                        self.game_over_action()
                    elif self.game.game_mode == "pve" and not self.game.current_player:
                        # Nếu đang chơi với AI, gọi AI đi
                        self.make_ai_move()
            
            # Reset selection
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

    def draw_load_pgn_button(self, screen, x, y):
        """Vẽ nút tải dữ liệu PGN để huấn luyện AI"""
        # Tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("Huấn luyện từ PGN", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        # Vẽ nút tải PGN
        button_rect = pygame.Rect(x, y + 25, 200, 30)
        
        # Gradient cho nút
        pygame.draw.rect(screen, (80, 120, 200), button_rect)  # Màu cơ bản
        
        # Hiệu ứng gradient
        gradient = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(gradient, (255, 255, 255, 80), (0, 0, button_rect.width, button_rect.height//2))
        screen.blit(gradient, button_rect)
        
        # Viền nút
        pygame.draw.rect(screen, (50, 50, 50), button_rect, 1)
        
        # Vẽ văn bản
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text = font.render("TẢI DỮ LIỆU PGN", True, (255, 255, 255))
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        # Lưu lại vị trí nút
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
        
        # Nếu không chọn file nào, thoát
        if not file_path:
            return
        
        # Hiển thị thông báo đang tải
        self.show_loading_overlay("Đang tải dữ liệu PGN...", color=(0, 0, 100))
        
        try:
            # Gọi hàm học từ file PGN
            games_learned = self.ai.learn_from_pgn_file(file_path)
            message = f"Đã hoàn thành! Đã học từ {games_learned} ván cờ"
            color = (0, 100, 0)  # Màu xanh lá
        except Exception as e:
            message = f"Lỗi: {str(e)}"
            color = (200, 0, 0)  # Màu đỏ
        
        # Hiển thị kết quả
        self.show_loading_overlay(message, duration=3000, color=color)

    def show_loading_overlay(self, message, duration=2000, color=(0, 0, 0)):
        """Hiển thị overlay với thông báo"""
        # Tạo overlay mờ
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # RGBA, mờ 60%
        self.screen.blit(overlay, (0, 0))
        
        # Tạo khung thông báo
        msg_width = 400
        msg_height = 120
        msg_rect = pygame.Rect((self.width - msg_width) // 2, (self.height - msg_height) // 2, 
                            msg_width, msg_height)
        
        # Vẽ khung thông báo
        pygame.draw.rect(self.screen, (240, 240, 240), msg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), msg_rect, 2)
        
        # Vẽ văn bản
        font = pygame.font.SysFont('Arial', 18)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
        
        # Vẽ logo hoặc biểu tượng (tùy chọn)
        if duration > 0:
            pygame.display.flip()
            pygame.time.wait(duration)

    def draw_captured_pieces(self, screen, x, y):
        """Vẽ các quân cờ đã bị bắt"""
        # Tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("QUÂN CỜ BỊ BẮT", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        # Vẽ khung chứa
        captured_rect = pygame.Rect(x, y + 25, 200, 100)
        pygame.draw.rect(screen, (245, 245, 245), captured_rect)
        pygame.draw.rect(screen, (180, 180, 180), captured_rect, 1)
        
        # Kiểm tra xem game có danh sách quân bị bắt không
        if not hasattr(self.game, 'captured_pieces') or not self.game.captured_pieces:
            empty_text = pygame.font.SysFont('Arial', 12).render("Chưa có quân nào bị bắt", True, (100, 100, 100))
            screen.blit(empty_text, (x + 10, y + 60))
            return
        
        # Đếm số lượng quân bị bắt theo loại và màu
        white_captured = {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0, chess.KING: 0}
        black_captured = {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0, chess.KING: 0}
        
        for piece, captured_by in self.game.captured_pieces:
            if piece.color:  # Quân trắng
                black_captured[piece.piece_type] += 1
            else:  # Quân đen
                white_captured[piece.piece_type] += 1
        
        # Ký hiệu quân cờ
        symbols = {
            chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B", 
            chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K"
        }
        
        # Vẽ quân bị bắt
        font = pygame.font.SysFont('Arial', 12)
        white_x = x + 10
        black_x = x + 110
        
        # Tiêu đề cột
        white_title = font.render("Quân trắng:", True, (0, 0, 0))
        black_title = font.render("Quân đen:", True, (0, 0, 0))
        screen.blit(white_title, (white_x, y + 30))
        screen.blit(black_title, (black_x, y + 30))
        
        # Vẽ số lượng
        y_offset = y + 50
        
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            if white_captured[piece_type] > 0:
                text = font.render(f"{symbols[piece_type]} x {white_captured[piece_type]}", True, (0, 0, 0))
                screen.blit(text, (white_x, y_offset))
            
            if black_captured[piece_type] > 0:
                text = font.render(f"{symbols[piece_type]} x {black_captured[piece_type]}", True, (0, 0, 0))
                screen.blit(text, (black_x, y_offset))
            
            if white_captured[piece_type] > 0 or black_captured[piece_type] > 0:
                y_offset += 16

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
        """Hiển thị màn hình kết thúc game"""
        # Tạo overlay mờ
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # RGBA, mờ 60%
        self.screen.blit(overlay, (0, 0))
        
        # Tạo khung thông báo
        box_width = 500
        box_height = 300
        box_rect = pygame.Rect((self.width - box_width) // 2, (self.height - box_height) // 2, 
                            box_width, box_height)
        
        # Vẽ khung với gradient
        pygame.draw.rect(self.screen, (30, 30, 60), box_rect)
        
        # Viền khung
        pygame.draw.rect(self.screen, (200, 200, 255), box_rect, 3)
        
        # Xác định thông điệp kết thúc
        game_state = self.game.get_state()
        if game_state == GameState.CHECKMATE:
            winner = "TRẮNG" if not self.game.current_player else "ĐEN"
            message = f"{winner} THẮNG! - CHIẾU BÍ!"
            color = (255, 215, 0)  # Màu vàng
        elif game_state == GameState.STALEMATE:
            message = "HÒA CỜ - BẾ TẮC"
            color = (200, 200, 200)
        else:
            message = "HÒA CỜ"
            color = (200, 200, 200)
        
        # Vẽ tiêu đề
        title_font = pygame.font.SysFont('Arial', 36, bold=True)
        game_over_text = title_font.render("KẾT THÚC GAME", True, (255, 255, 255))
        self.screen.blit(game_over_text, (self.width // 2 - game_over_text.get_width() // 2, 
                                        box_rect.y + 40))
        
        # Vẽ kết quả
        result_font = pygame.font.SysFont('Arial', 28, bold=True)
        result_text = result_font.render(message, True, color)
        self.screen.blit(result_text, (self.width // 2 - result_text.get_width() // 2, 
                                    box_rect.y + 100))
        
        # Vẽ hướng dẫn
        guide_font = pygame.font.SysFont('Arial', 20)
        
        restart_text = guide_font.render("Nhấn R để chơi lại", True, (255, 255, 255))
        self.screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                        box_rect.y + 180))
        
        menu_text = guide_font.render("Nhấn M để về Menu", True, (255, 255, 255))
        self.screen.blit(menu_text, (self.width // 2 - menu_text.get_width() // 2, 
                                    box_rect.y + 220))
        
    def draw_game_info(self, screen, x, y):
        """Hiển thị thông tin cơ bản về game"""
        font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Thông tin chế độ chơi
        mode_text = "Chế độ: " + ("Người vs Máy" if self.game.game_mode == "pve" else "Người vs Người")
        mode_surface = font.render(mode_text, True, (0, 0, 0))
        screen.blit(mode_surface, (x, y))
        
        # Thông tin người chơi hiện tại
        current_player = "Trắng" if self.game.current_player else "Đen"
        player_surface = font.render(f"Lượt chơi: {current_player}", True, (0, 0, 0))
        screen.blit(player_surface, (x, y + 25))
        
        # Thông tin trạng thái game
        if self.game.board.is_check():
            state_text = "Trạng thái: CHIẾU"
            state_color = (255, 0, 0)
        elif self.game.is_game_over():
            state_text = "Trạng thái: KẾT THÚC"
            state_color = (0, 0, 255)
        else:
            state_text = "Trạng thái: ĐANG CHƠI"
            state_color = (0, 100, 0)
        
        state_surface = font.render(state_text, True, state_color)
        screen.blit(state_surface, (x, y + 50))
    
    def draw_sidebar(self, screen):
        """Vẽ sidebar với tất cả các nút và thông tin"""
        # Kích thước và vị trí sidebar
        sidebar_rect = pygame.Rect(self.board_size, 0, self.width - self.board_size, self.height)
        
        # Vẽ nền sidebar với viền
        pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
        pygame.draw.rect(screen, (100, 100, 100), sidebar_rect, 2)
        
        # Vẽ tiêu đề
        title_font = pygame.font.SysFont('Arial', 22, bold=True)
        title_text = title_font.render("CHESS GAME", True, (0, 0, 100))
        screen.blit(title_text, (self.board_size + (sidebar_rect.width - title_text.get_width()) // 2, 20))
        
        # Vị trí bắt đầu vẽ các nút và thông tin
        y_pos = 70
        
        # ===== 1. Thông tin game =====
        self.draw_game_info(screen, self.board_size + 20, y_pos)
        y_pos += 80
        
        # ===== 2. Nút bật/tắt học tập AI =====
        if self.game.game_mode == "pve" and hasattr(self.ai, 'learning_enabled'):
            self.draw_learning_toggle(screen, self.board_size + 20, y_pos)
            y_pos += 60
        
        # ===== 3. Nút tải dữ liệu PGN =====
        if self.game.game_mode == "pve":
            self.draw_load_pgn_button(screen, self.board_size + 20, y_pos)
            y_pos += 60
        
        # ===== 4. Thông tin học tập AI =====
        if self.game.game_mode == "pve" and hasattr(self.ai, 'get_learning_stats'):
            self.draw_ai_stats(screen, self.board_size + 20, y_pos)
            y_pos += 160
        
        # ===== 5. Quân cờ đã bị bắt =====
        self.draw_captured_pieces(screen, self.board_size + 20, y_pos)
        y_pos += 150
        
        # ===== 6. Lịch sử các nước đi =====
        self.draw_move_history(screen, self.board_size + 20, y_pos)
        y_pos += 120
        
        # ===== 7. Các nút điều khiển game =====
        self.draw_game_controls(screen, self.board_size + 20, y_pos)
    
    def draw_game_controls(self, screen, x, y):
        """Vẽ các nút điều khiển game"""
        # Các nút cần vẽ
        buttons = [
            {"text": "GỢI Ý", "rect": None, "color": (80, 150, 220), "attr": "hint_button_rect"},
            {"text": "ĐI LẠI", "rect": None, "color": (220, 150, 80), "attr": "undo_button_rect"},
            {"text": "RESET", "rect": None, "color": (150, 80, 220), "attr": "reset_button_rect"}
        ]
        
        button_width = 60
        button_height = 30
        button_spacing = 10
        
        # Vẽ từng nút
        for i, btn in enumerate(buttons):
            btn_x = x + i * (button_width + button_spacing)
            btn_rect = pygame.Rect(btn_x, y, button_width, button_height)
            
            # Vẽ nút với gradient
            pygame.draw.rect(screen, btn["color"], btn_rect)
            
            # Hiệu ứng gradient
            gradient = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(gradient, (255, 255, 255, 50), (0, 0, btn_rect.width, btn_rect.height//2))
            screen.blit(gradient, btn_rect)
            
            # Viền nút
            pygame.draw.rect(screen, (50, 50, 50), btn_rect, 1)
            
            # Vẽ văn bản
            font = pygame.font.SysFont('Arial', 12, bold=True)
            text = font.render(btn["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn_rect.center)
            screen.blit(text, text_rect)
            
            # Lưu lại vị trí nút
            setattr(self, btn["attr"], btn_rect)

    def draw_move_history(self, screen, x, y):
        """Hiển thị lịch sử các nước đi"""
        # Tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("LỊCH SỬ NƯỚC ĐI", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        # Vẽ khung chứa
        history_rect = pygame.Rect(x, y + 25, 200, 80)
        pygame.draw.rect(screen, (245, 245, 245), history_rect)
        pygame.draw.rect(screen, (180, 180, 180), history_rect, 1)
        
        # Hiển thị lịch sử nước đi
        if not hasattr(self.game, 'move_history') or not self.game.move_history:
            empty_text = pygame.font.SysFont('Arial', 12).render("Chưa có nước đi nào", True, (100, 100, 100))
            screen.blit(empty_text, (x + 10, y + 60))
            return
        
        # Hiển thị lịch sử
        font = pygame.font.SysFont('Arial', 12)
        moves_per_row = 4
        y_offset = y + 35
        line_height = 18
        
        # Hiển thị tối đa 8 nước đi gần nhất
        start_idx = max(0, len(self.game.move_history) - 8)
        for i in range(start_idx, len(self.game.move_history)):
            move = self.game.move_history[i]
            move_num = i + 1
            row = (i - start_idx) // moves_per_row
            col = (i - start_idx) % moves_per_row
            
            move_text = f"{move_num}.{move}"
            text = font.render(move_text, True, (0, 0, 0))
            screen.blit(text, (x + 10 + col * 50, y_offset + row * line_height))

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
        
    def draw_legal_moves(self, screen):
        """Vẽ các nước đi hợp lệ"""
        for move in self.legal_moves:
            to_square = move.to_square
            file = chess.square_file(to_square)
            rank = chess.square_rank(to_square)
            highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight.fill(self.HIGHLIGHT_COLOR)
            screen.blit(highlight, (file * self.square_size, (7 - rank) * self.square_size))
    
    def draw_learning_toggle(self, screen, x, y):
        """Vẽ nút bật/tắt chế độ học tập của AI"""
        # Tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("Chế độ học tập", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        # Vẽ nút bật/tắt
        button_rect = pygame.Rect(x, y + 25, 200, 30)
        button_color = (0, 180, 0) if self.ai.learning_enabled else (180, 0, 0)
        
        # Vẽ nút với viền và hiệu ứng 3D
        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, (255, 255, 255), button_rect.inflate(-4, -4), 1)  # Viền trong
        pygame.draw.rect(screen, (50, 50, 50), button_rect, 1)  # Viền ngoài
        
        # Vẽ văn bản trên nút
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text = font.render("BẬT" if self.ai.learning_enabled else "TẮT", True, (255, 255, 255))
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        # Lưu lại vị trí nút để xử lý sự kiện click
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
        """Chạy game với menu chính"""
        self.running = True
        clock = pygame.time.Clock()
        
        # Thêm biến trạng thái để xác định đang ở menu hay đang chơi
        self.in_menu = True
        
        while self.running:
            # Xử lý sự kiện
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                
                if self.in_menu:
                    # Xử lý sự kiện trong menu
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Vẽ menu và lấy về các nút
                        pvp_button, pve_button = self.draw_game_menu()
                        
                        # Kiểm tra click vào nút nào
                        if pvp_button.collidepoint(event.pos):
                            self.start_new_game(GameMode.PLAYER_VS_PLAYER)
                            self.in_menu = False
                        elif pve_button.collidepoint(event.pos):
                            self.start_new_game(GameMode.PLAYER_VS_AI)
                            self.in_menu = False
                else:
                    # Xử lý sự kiện trong game
                    if not self.handle_event(event):
                        self.running = False
                        break
            
            # Vẽ giao diện
            if self.in_menu:
                # Vẽ menu chính
                self.draw_game_menu()
            else:
                # Vẽ giao diện game
                self.render(self.screen)
            
            # Cập nhật màn hình
            pygame.display.flip()
            
            # Giới hạn FPS
            clock.tick(60)
        
        pygame.quit()