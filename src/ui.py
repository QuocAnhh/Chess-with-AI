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
import math

class ChessUI:
    def __init__(self, width=1200, height=700, game=None, ai=None):
        pygame.init()
        pygame.display.set_caption("Chess Game")

        self.hint_button_rect = None
        self.undo_button_rect = None
        self.resign_button_rect = None
        self.load_pgn_rect = None
        self.learning_toggle_rect = None
        

        self.status_height = 50  
        
        self.square_size = 80  
        self.board_size = self.square_size * 8  
        
        sidebar_width = 300
        
        self.width = self.board_size + sidebar_width  # 640px + 300px = 940px
        self.height = self.board_size + self.status_height  # 640px + 40px = 680px
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        try:
            # thử tìm font trong hệ thống hỗ trợ tiếng Việt
            available_fonts = pygame.font.get_fonts()
            unicode_fonts = ['arial', 'segoeui', 'timesnewroman', 'dejavusans', 'freesans']
        
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
                print("Không tìm thấy font Unicode, sử dụng font mặc định")
                self.font = pygame.font.SysFont(None, 28)
                self.small_font = pygame.font.SysFont(None, 20)
        except:
            print("Lỗi khi tải font, sử dụng font mặc định")
            self.font = pygame.font.SysFont(None, 28)
            self.small_font = pygame.font.SysFont(None, 20)

        self.pieces_images = {}
        self.load_pieces()

        self.piece_images = self.pieces_images


        self.WHITE_SQUARE = (240, 217, 181)
        self.BLACK_SQUARE = (181, 136, 99)
        self.HIGHLIGHT_COLOR = (124, 252, 0, 128)  
        self.SELECT_COLOR = (255, 255, 0, 128)    

        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        self.promotion_choice = None
        
        if game:
            self.game = game
        else:
            self.game = ChessGame()
            
        if ai:
            self.ai = ai
        else:
            self.ai = ChessAI(difficulty=2)
            
        self.game.ai = self.ai
            
        self.sound_on = True
        self.load_sounds()
        
        if hasattr(self.game, 'mode'):
            print(f"Khởi tạo UI với chế độ game: {self.game.mode}")
        
        self.in_menu = True
        
        self.status_font = pygame.font.SysFont('Arial', 20)
        
    def game_over_action(self):
        '''Các hành động khi kết thúc game'''

        # Đặt cờ game_over để ngăn vòng lặp vô hạn
        self.game_over = True
        
        try:
            # limit thời gian học tập
            if hasattr(self.ai, 'learning_enabled') and self.ai.learning_enabled:
                print("Đang xử lý học tập sau khi game kết thúc...")
                import threading
                def learn_with_timeout():
                    try:
                        self.game.game_over_learn()
                        print("AI đã học từ ván đấu này")
                    except Exception as e:
                        print(f"Lỗi học tập: {e}")
                
                # học trong thread riêng với timeout
                learn_thread = threading.Thread(target=learn_with_timeout)
                learn_thread.daemon = True 
                learn_thread.start()
                learn_thread.join(timeout=1.0)  
        except Exception as e:
            print(f"Lỗi xử lý game over: {e}")

        state = self.game.get_state()
        
        if state == GameState.CHECKMATE:
            winner = 'White' if not self.game.current_player else 'Black'
            self.show_message(f'{winner} wins!')
        elif state == GameState.STALEMATE:
            # Đảm bảo hiển thị thông báo cho trường hợp Stalemate
            self.show_message('Draw by Stalemate!', duration=3000)
        else:
            self.show_message('Draw!') 
        
        self.render(self.screen)

    def draw_background(self, screen):
        """Tạo nền gradient cho giao diện"""
        color1 = (220, 240, 255)  
        color2 = (240, 240, 240)  
        
        height = screen.get_height()
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))
                
    def render(self, screen):
        """Vẽ toàn bộ giao diện"""
        screen.fill((240, 240, 240))
        
        self.draw_board(screen)
        
        self.draw_pieces(screen)
        
        if hasattr(self, 'selected_square') and self.selected_square is not None:
            if hasattr(self, 'legal_moves') and self.legal_moves:
                self.draw_legal_moves(screen)
        
        self.draw_sidebar(screen)
        
        # Vẽ thanh trạng thái
        self.draw_status()
        
        # Cập nhật màn hình
        pygame.display.flip()

    def draw_board(self, screen):
        """Vẽ bàn cờ vua với hai màu xen kẽ"""
        light_square = (240, 217, 181)  
        dark_square = (181, 136, 99)   
        
        square_size = self.square_size
        
        for row in range(8):
            for col in range(8):
                color = light_square if (row + col) % 2 == 0 else dark_square
                
                square_rect = pygame.Rect(col * square_size, row * square_size, 
                                        square_size, square_size)
                pygame.draw.rect(screen, color, square_rect)
        
        board_rect = pygame.Rect(0, 0, 8 * square_size, 8 * square_size)
        pygame.draw.rect(screen, (0, 0, 0), board_rect, 2)
        
        font = pygame.font.SysFont('Arial', 12)
        
        for col in range(8):
            label = chr(ord('a') + col)
            text = font.render(label, True, (0, 0, 0))
            
            x = col * square_size + square_size // 2 - text.get_width() // 2
            y = 8 * square_size - 15
            
            screen.blit(text, (x, y))
        
        for row in range(8):
            label = str(8 - row)
            text = font.render(label, True, (0, 0, 0))
            
            x = 8 * square_size - 15
            y = row * square_size + square_size // 2 - text.get_height() // 2
            
            screen.blit(text, (x, y))
    
    def draw_selected_square(self, screen):
        """Tô sáng ô vuông đã chọn"""
        if self.selected_square is None:
            return
            
        file = chess.square_file(self.selected_square)
        rank = 7 - chess.square_rank(self.selected_square)
        
        square_rect = pygame.Rect(file * self.square_size, rank * self.square_size,
                                self.square_size, self.square_size)
        pygame.draw.rect(screen, (255, 255, 0), square_rect, 3)

    def draw_pieces(self, screen=None):
        """Vẽ các quân cờ trên bàn cờ"""
        if screen is None:
            screen = self.screen
            
        if not hasattr(self, 'piece_images') or not self.piece_images:
            self.load_pieces()
        
        square_size = self.square_size
        
        for square in chess.SQUARES:
            piece = self.game.board.piece_at(square)
            if not piece:
                continue
                
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            
            x = file * square_size
            y = rank * square_size
            
            color = "w" if piece.color else "b"
            piece_type = chess.piece_symbol(piece.piece_type).lower()
            piece_key = color + piece_type
            
            if piece_key in self.piece_images:
                piece_img = self.piece_images[piece_key]
                
                piece_x = x + (square_size - piece_img.get_width()) // 2
                piece_y = y + (square_size - piece_img.get_height()) // 2
                
                screen.blit(piece_img, (piece_x, piece_y))
            else:
                print(f"Không tìm thấy hình ảnh cho quân cờ: {piece_key}")
        
        if hasattr(self.game, 'ai_thinking') and self.game.ai_thinking:
            overlay = pygame.Surface((self.board_size, 60), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # Nền đen mờ
            
            screen.blit(overlay, (0, self.board_size // 2 - 30))
            
            font = pygame.font.SysFont('Arial', 24, bold=True)
            text = font.render("AI ĐANG SUY NGHĨ...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.board_size // 2, self.board_size // 2))
            screen.blit(text, text_rect)

    def draw_legal_moves(self, screen):
        """Hiển thị các nước đi hợp lệ cho quân cờ đã chọn"""
        move_color = (0, 255, 0, 100)  # Xanh lá mờ
        capture_color = (255, 0, 0, 120)  # Đỏ mờ
        
        for move in self.legal_moves:
            file = chess.square_file(move.to_square)
            rank = 7 - chess.square_rank(move.to_square)
            
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
        print(f"Đã tạo game mới với chế độ: {mode}")  
    
    def handle_event(self, event):
        """Xử lý tất cả các sự kiện từ người dùng"""
        if event.type == pygame.QUIT:
            return False  
        
        # Xử lý khi game over
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: 
                    self.reset_game()
                    self.game_over = False
                    return True
                elif event.key == pygame.K_m: 
                    self.in_menu = True
                    self.game_over = False
                    return True
            return True
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            
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
                
            if not self.game.is_game_over() and event.pos[0] < self.board_size and event.pos[1] < self.board_size:
                self.handle_click(event.pos)
                return True
        
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
                if hasattr(self, 'show_menu'):
                    self.show_menu()
                    return True
        
        return True  # tiếp tục game

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
        screen_copy = pygame.display.get_surface().copy()
        
        dialog_width, dialog_height = 300, 120
        screen_width, screen_height = pygame.display.get_surface().get_size()
        
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        promotion_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        piece_names = ["Hậu", "Xe", "Tượng", "Mã"]
        
        font = pygame.font.SysFont('Arial', 24)
        title_text = font.render("Chọn quân phong cấp:", True, (0, 0, 0))
        
        button_width = 60
        button_height = 60
        button_spacing = 10
        buttons_total_width = button_width * len(promotion_pieces) + button_spacing * (len(promotion_pieces) - 1)
        
        button_start_x = dialog_x + (dialog_width - buttons_total_width) // 2
        button_y = dialog_y + title_text.get_height() + 10
        
        chosen_piece = None
        running = True
        
        while running:
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # RGBA, alpha=128 cho hiệu ứng mờ
            pygame.display.get_surface().blit(overlay, (0, 0))
            
            pygame.draw.rect(pygame.display.get_surface(), (240, 240, 240), dialog_rect)
            pygame.draw.rect(pygame.display.get_surface(), (0, 0, 0), dialog_rect, 2)
            
            pygame.display.get_surface().blit(title_text, 
                                            (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 10))
            
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
            
            # process event
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
            
        pygame.display.get_surface().blit(screen_copy, (0, 0))
        
        return chosen_piece

    def undo_move(self):
        """Đi lại nước đi trước đó"""
        if hasattr(self.game.board, 'pop') and len(self.game.move_history) > 0:
            # Đi lại nước của người chơi
            self.game.board.pop()
            self.game.move_history.pop()
            self.game.current_player = not self.game.current_player
            
            if self.game.game_mode == "pve" and len(self.game.move_history) > 0:
                self.game.board.pop()
                self.game.move_history.pop()
                self.game.current_player = not self.game.current_player
            
            # Reset trạng thái chọn
            self.selected_square = None
            self.legal_moves = []
            
            # Phát âm thanh
            if hasattr(self, 'undo_sound'):
                self.undo_sound.play()

    def reset_game(self):
        """Khởi động lại game"""
        try:
            current_mode = "pvp"
            if hasattr(self.game, 'game_mode'):
                current_mode = self.game.game_mode
            
            difficulty = 2
            if hasattr(self.game, 'ai') and hasattr(self.game.ai, 'difficulty'):
                difficulty = self.game.ai.difficulty
            
            self.game = ChessGame()
            if current_mode == "pve":
                self.game.game_mode = "pve"
            else:
                self.game.game_mode = "pvp"
                
            self.ai.difficulty = difficulty
            self.game.ai = self.ai
            
            # Reset trạng thái
            self.selected_square = None
            self.legal_moves = []
            self.game_over = False
            
            if hasattr(self, 'new_game_sound') and hasattr(self, 'sound_on') and self.sound_on:
                self.new_game_sound.play()
                
            print(f"Game đã được khởi động lại với chế độ {self.game.game_mode}")
        except Exception as e:
            print(f"Lỗi khởi động lại game: {str(e)}")

    def draw_ai_stats(self, screen, x, y):
        """Hiển thị thông tin thống kê về AI"""
        # Lấy thông tin từ AI
        stats = self.ai.get_learning_stats()
        
        stats_rect = pygame.Rect(x, y, 200, 130)
        pygame.draw.rect(screen, (240, 240, 255), stats_rect)
        pygame.draw.rect(screen, (100, 100, 150), stats_rect, 1)
        
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("THỐNG KÊ AI", True, (0, 0, 100))
        screen.blit(title, (x + 10, y + 10))
        
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
        if self.game.is_game_over():
            print("Cannot show hint: Game is over")
            return
        
        try:
            if hasattr(self.game, 'ai') and self.game.ai:
                current_player = self.game.current_player
                move = self.game.ai.get_move(self.game.board)
                print(f"AI suggested move: {move}")
                
                if move:
                    self.hint_move = move
                    self.hint_time = pygame.time.get_ticks()
                    
                    # Lấy tọa độ đích và đi
                    from_file = chess.square_file(move.from_square)
                    from_rank = 7 - chess.square_rank(move.from_square)
                    to_file = chess.square_file(move.to_square)
                    to_rank = 7 - chess.square_rank(move.to_square)
                    
                    hint_rect1 = pygame.Rect(
                        from_file * self.square_size,
                        from_rank * self.square_size,
                        self.square_size, self.square_size
                    )
                    hint_surface1 = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    hint_surface1.fill((0, 255, 0, 128))  # Màu xanh lá mờ
                    self.screen.blit(hint_surface1, hint_rect1)
                    
                    hint_rect2 = pygame.Rect(
                        to_file * self.square_size,
                        to_rank * self.square_size,
                        self.square_size, self.square_size
                    )
                    hint_surface2 = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    hint_surface2.fill((255, 255, 0, 128))  # Màu vàng mờ
                    self.screen.blit(hint_surface2, hint_rect2)
                    
                    start_pos = (
                        from_file * self.square_size + self.square_size // 2,
                        from_rank * self.square_size + self.square_size // 2
                    )
                    end_pos = (
                        to_file * self.square_size + self.square_size // 2,
                        to_rank * self.square_size + self.square_size // 2
                    )
                    pygame.draw.line(self.screen, (255, 0, 0), start_pos, end_pos, 3)
                    
                    font = pygame.font.SysFont('Arial', 24)
                    hint_text = font.render(f"Gợi ý: {move}", True, (255, 255, 255))
                    text_rect = hint_text.get_rect(center=(self.board_size // 2, self.board_size - 20))
                    text_bg = pygame.Surface((hint_text.get_width() + 20, hint_text.get_height() + 10), pygame.SRCALPHA)
                    text_bg.fill((0, 0, 0, 180))
                    self.screen.blit(text_bg, (text_rect.x - 10, text_rect.y - 5))
                    self.screen.blit(hint_text, text_rect)
                    
                    pygame.display.flip()
                    pygame.time.wait(2000)
            else:
                print("AI not available")
            
        except Exception as e:
            print(f"Error showing hint: {str(e)}")

    def animate_move(self, move):
        """Tạo hiệu ứng di chuyển quân cờ mượt"""
        from_file = chess.square_file(move.from_square)
        from_rank = 7 - chess.square_rank(move.from_square)
        to_file = chess.square_file(move.to_square)
        to_rank = 7 - chess.square_rank(move.to_square)
        
        from_x = from_file * self.square_size
        from_y = from_rank * self.square_size
        to_x = to_file * self.square_size
        to_y = to_rank * self.square_size
        
        piece = self.game.board.piece_at(move.from_square)
        if not piece:
            return
        
        color = "w" if piece.color else "b"
        piece_type = chess.piece_symbol(piece.piece_type).lower()
        piece_key = color + piece_type
        
        if piece_key not in self.piece_images:
            return
        
        frames = 15  # Tăng số khung hình chuyển động cho mướt
        
        piece_img = self.piece_images[piece_key]
        
        glow = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        glow.fill((255, 255, 100, 100))  
        
        for i in range(frames + 1):
            progress = i / frames
            current_x = from_x + (to_x - from_x) * progress
            current_y = from_y + (to_y - from_y) * progress
            
            self.draw_board(self.screen)
            
            if i < frames // 2:
                alpha = 100 - (i * 200 // frames)
                glow.set_alpha(alpha)
                self.screen.blit(glow, (from_x, from_y))
            
            temp_board = self.game.board.copy()
            temp_board.remove_piece_at(move.from_square)
            
            for square in chess.SQUARES:
                piece_at_square = temp_board.piece_at(square)
                if not piece_at_square:
                    continue
                
                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)
                
                x = file * self.square_size
                y = rank * self.square_size
                
                sq_color = "w" if piece_at_square.color else "b"
                sq_piece_type = chess.piece_symbol(piece_at_square.piece_type).lower()
                sq_piece_key = sq_color + sq_piece_type
                
                if sq_piece_key in self.piece_images:
                    sq_piece_img = self.piece_images[sq_piece_key]
                    sq_piece_x = x + (self.square_size - sq_piece_img.get_width()) // 2
                    sq_piece_y = y + (self.square_size - sq_piece_img.get_height()) // 2
                    self.screen.blit(sq_piece_img, (sq_piece_x, sq_piece_y))
            
            shadow_offset = 3
            shadow = piece_img.copy()
            shadow.fill((0, 0, 0, 100), None, pygame.BLEND_RGBA_MULT)
            shadow_x = current_x + (self.square_size - piece_img.get_width()) // 2 + shadow_offset
            shadow_y = current_y + (self.square_size - piece_img.get_height()) // 2 + shadow_offset
            self.screen.blit(shadow, (shadow_x, shadow_y))
            
            piece_x = current_x + (self.square_size - piece_img.get_width()) // 2
            piece_y = current_y + (self.square_size - piece_img.get_height()) // 2
            self.screen.blit(piece_img, (piece_x, piece_y))
            
            light_surface = pygame.Surface((piece_img.get_width(), piece_img.get_height()), pygame.SRCALPHA)
            light_alpha = 100 - abs((i - frames//2) * 200 // frames)
            light_surface.fill((255, 255, 255, max(0, light_alpha)))
            self.screen.blit(light_surface, (piece_x, piece_y), special_flags=pygame.BLEND_ADD)
            
            self.draw_sidebar(self.screen)
            
            pygame.display.flip()
            pygame.time.wait(20)  # 20ms delay giữa các frame
        
        for i in range(5):  # 5 frames flash
            alpha = 150 - i * 30  # Giảm dần độ trong suốt
            flash = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            flash.fill((255, 255, 100, alpha))
            self.screen.blit(flash, (to_x, to_y))
            pygame.display.flip()
            pygame.time.wait(50)

    def handle_click(self, pos):
        """Xử lý sự kiện nhấp chuột trên bàn cờ"""
        if self.game.is_game_over() or (self.game.game_mode == "pve" and not self.game.current_player):
            # Không xử lý click nếu game kết thúc hoặc đang đợi AI
            return
        
        file = pos[0] // self.square_size
        rank = 7 - (pos[1] // self.square_size)
        
        if not (0 <= file < 8 and 0 <= rank < 8):
            return
            
        square = chess.square(file, rank)
        
        # TH 1: Chọn quân cờ
        if self.selected_square is None:
            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                if move.from_square == square]
                
                if hasattr(self, 'play_sound'):
                    self.play_sound('select')
                    
                print(f"Đã chọn quân tại {chess.square_name(square)}")
                
        # TH2: Chọn ô đích hoặc bỏ chọn
        else:
            # Nếu nhấp vào quân cùng màu khác, chọn quân đó thay thế
            if square != self.selected_square and self.game.board.piece_at(square) and \
            self.game.board.piece_at(square).color == self.game.current_player:
                self.selected_square = square
                self.legal_moves = [move for move in self.game.get_legal_moves() 
                                if move.from_square == square]
                
                if hasattr(self, 'play_sound'):
                    self.play_sound('select')
                    
                print(f"Đã chọn lại quân tại {chess.square_name(square)}")
                return
            
            # Tìm nước đi 
            move = None
            for legal_move in self.legal_moves:
                if legal_move.to_square == square:
                    move = legal_move
                    break
            
            # Nếu đã tìm thấy nước đi hợp lệ
            if move:
                # check xem có phải là nước phong cấp không
                if self.is_promotion_move(move):
                    promotion_piece = self.show_promotion_dialog()
                    if promotion_piece:
                        move = chess.Move(move.from_square, move.to_square, promotion=promotion_piece)
                    else:
                        # hủy chọn quân phong cấp
                        self.selected_square = None
                        self.legal_moves = []
                        return
                
                if hasattr(self, 'animate_move'):
                    self.animate_move(move)
                
                success = self.game.make_move(move)
                
                if success:
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
            
        self.game.ai_thinking = True
        
        try:
            self.render(self.screen)
            pygame.display.flip()
            
            start_time = time.time() 
            
            ai_move = self.ai.get_move(self.game.board)
            
            elapsed_time = time.time() - start_time
            if elapsed_time < 0.5:
                pygame.time.wait(int((0.5 - elapsed_time) * 1000))
            
            if ai_move:
                success = self.game.make_move(ai_move)
                print(f"AI đã đi: {ai_move}, thành công: {success}")
                
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
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("Huấn luyện từ PGN", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        button_rect = pygame.Rect(x, y + 25, 200, 30)
        
        pygame.draw.rect(screen, (80, 120, 200), button_rect)  # Màu cơ bản
        
        gradient = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(gradient, (255, 255, 255, 80), (0, 0, button_rect.width, button_rect.height//2))
        screen.blit(gradient, button_rect)
        
        pygame.draw.rect(screen, (50, 50, 50), button_rect, 1)
        
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text = font.render("TẢI DỮ LIỆU PGN", True, (255, 255, 255))
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        self.load_pgn_rect = button_rect

    def load_pgn_data(self):
        """Mở hộp thoại chọn file và tải dữ liệu PGN để huấn luyện AI"""
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        
        file_path = filedialog.askopenfilename(
            title="Chọn file PGN",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.show_loading_overlay("Đang tải dữ liệu PGN...", color=(0, 0, 100))
        
        try:
            games_learned = self.ai.learn_from_pgn_file(file_path)
            message = f"Đã hoàn thành! Đã học từ {games_learned} ván cờ"
            color = (0, 100, 0)  # Màu xanh lá
        except Exception as e:
            message = f"Lỗi: {str(e)}"
            color = (200, 0, 0)  # Màu đỏ
        
        self.show_loading_overlay(message, duration=3000, color=color)

    def show_loading_overlay(self, message, duration=2000, color=(0, 0, 0)):
        """Hiển thị overlay với thông báo"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # RGBA, mờ 60%
        self.screen.blit(overlay, (0, 0))
        
        msg_width = 400
        msg_height = 120
        msg_rect = pygame.Rect((self.width - msg_width) // 2, (self.height - msg_height) // 2, 
                            msg_width, msg_height)
        
        pygame.draw.rect(self.screen, (240, 240, 240), msg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), msg_rect, 2)
        
        font = pygame.font.SysFont('Arial', 18)
        text = font.render(message, True, color)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
        
        if duration > 0:
            pygame.display.flip()
            pygame.time.wait(duration)

    def draw_captured_pieces(self, screen, x, y):
        """Vẽ các quân cờ đã bị bắt"""
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("QUÂN CỜ BỊ BẮT", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        captured_rect = pygame.Rect(x, y + 25, 200, 100)
        pygame.draw.rect(screen, (245, 245, 245), captured_rect)
        pygame.draw.rect(screen, (180, 180, 180), captured_rect, 1)
        
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
        
        symbols = {
            chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B", 
            chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K"
        }
        
        font = pygame.font.SysFont('Arial', 12)
        white_x = x + 10
        black_x = x + 110
        
        white_title = font.render("Quân trắng:", True, (0, 0, 0))
        black_title = font.render("Quân đen:", True, (0, 0, 0))
        screen.blit(white_title, (white_x, y + 30))
        screen.blit(black_title, (black_x, y + 30))
        
        
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
        screen = screen or self.screen  
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
            overlay = pygame.Surface((self.board_size, 60), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # Nền đen mờ
            
            screen.blit(overlay, (0, self.board_size // 2 - 30))
            
            font = pygame.font.SysFont('Arial', 24, bold=True)
            text = font.render("AI ĐANG SUY NGHĨ...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.board_size // 2, self.board_size // 2))
            screen.blit(text, text_rect)
            
            current_time = pygame.time.get_ticks()
            dots = "." * ((current_time // 500) % 4)
            dots_text = font.render(dots, True, (255, 255, 255))
            screen.blit(dots_text, (text_rect.right + 5, text_rect.y))

    def reset_game(self):
        """Khởi động lại game"""
        try:
            current_mode = "pvp"
            if hasattr(self.game, 'game_mode'):
                current_mode = self.game.game_mode
            
            difficulty = 2
            if hasattr(self.game, 'ai') and hasattr(self.game.ai, 'difficulty'):
                difficulty = self.game.ai.difficulty
            
            self.game = ChessGame()
            if current_mode == "pve":
                self.game.game_mode = "pve"
            else:
                self.game.game_mode = "pvp"
                
            self.ai.difficulty = difficulty
            self.game.ai = self.ai
            
            self.selected_square = None
            self.legal_moves = []
            self.game_over = False
            
            if hasattr(self, 'new_game_sound') and hasattr(self, 'sound_on') and self.sound_on:
                self.new_game_sound.play()
                
            print(f"Game đã được khởi động lại với chế độ {self.game.game_mode}")
        except Exception as e:
            print(f"Lỗi khởi động lại game: {str(e)}")

    def resign_game(self):
        """Đầu hàng trong game hiện tại"""
        if self.game.is_game_over():
            return
            
        # Đánh dấu game kết thúc bằng cách cho vua của người chơi hiện tại chiếu bí
        current_player = self.game.current_player
        winner = "Đen" if current_player else "Trắng"
        
        self.show_message(f"{winner} thắng do đối phương đầu hàng!")
        
        if hasattr(self.game, 'game_over_learn'):
            self.game.game_over_learn()
            
    def toggle_sound(self):
        """Bật/tắt âm thanh"""
        if hasattr(self, 'sound_on'):
            self.sound_on = not self.sound_on
            
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
        screen_copy = pygame.display.get_surface().copy()
        
        screen_width, screen_height = pygame.display.get_surface().get_size()
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # RGBA, alpha=128 cho hiệu ứng mờ
        
        font = pygame.font.SysFont('Arial', 36)
        pause_text = font.render("GAME PAUSED", True, (255, 255, 255))
        continue_text = font.render("Press any key to continue", True, (255, 255, 255))
        
        pause_x = (screen_width - pause_text.get_width()) // 2
        pause_y = (screen_height - pause_text.get_height()) // 2 - 20
        
        continue_x = (screen_width - continue_text.get_width()) // 2
        continue_y = pause_y + pause_text.get_height() + 20
        
        pygame.display.get_surface().blit(overlay, (0, 0))
        pygame.display.get_surface().blit(pause_text, (pause_x, pause_y))
        pygame.display.get_surface().blit(continue_text, (continue_x, continue_y))
        pygame.display.flip()
        
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    paused = False
        
        pygame.display.get_surface().blit(screen_copy, (0, 0))
        pygame.display.flip()
        
    def draw_status(self):
        """Vẽ thanh trạng thái phía dưới giao diện"""
        status_rect = pygame.Rect(0, self.height - self.status_height, self.width, self.status_height)
        pygame.draw.rect(self.screen, (200, 200, 200), status_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), status_rect, 2)

        if hasattr(self.game, 'current_player'):
            player_text = f"Turn: {'White' if self.game.current_player else 'Black'}"
        else:
            player_text = "Turn: N/A"

        if hasattr(self.game, 'move_count'):
            move_text = f"Moves: {self.game.move_count}"
        else:
            move_text = "Moves: N/A"

        status_text = f"{player_text} | {move_text}"
        text_surface = self.status_font.render(status_text, True, (0, 0, 0))
        text_x = (self.width - text_surface.get_width()) // 2
        text_y = self.height - self.status_height + (self.status_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))
    
    def draw_game_menu(self):
        for y in range(self.height):
            color_value = 30 + int(30 * (y / self.height))
            pygame.draw.line(self.screen, (color_value, color_value, color_value+10), 
                        (0, y), (self.width, y))
        
        if hasattr(self, 'background_image'):
            bg_img = self.background_image
            self.screen.blit(bg_img, (self.width//2 - bg_img.get_width()//2, 
                                self.height//2 - bg_img.get_height()//2))
        
        title_font = pygame.font.SysFont('Segoe UI', 72, bold=True)
        title_text = "CHESS MASTER"
        title_color = (255, 215, 0)  # Gold
        title = title_font.render(title_text, True, title_color)
        
        for i in range(3):
            glow = title_font.render(title_text, True, (*title_color[:3], 50-i*15))
            self.screen.blit(glow, (self.width//2 - title.get_width()//2 - i*2, 
                                self.height//5 - i*2))
            self.screen.blit(glow, (self.width//2 - title.get_width()//2 + i*2, 
                                self.height//5 + i*2))
        
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 
                            self.height//5))
        
        button_width = 300
        button_height = 60
        
        # Nút Player vs Player
        pvp_button = pygame.Rect(
            self.width//2 - button_width//2,
            self.height//2 - button_height - 20,
            button_width, button_height
        )
        
        # Nút Player vs AI
        pve_button = pygame.Rect(
            self.width//2 - button_width//2,
            self.height//2 + 20,
            button_width, button_height
        )
        
        # check hover
        mouse_pos = pygame.mouse.get_pos()
        pvp_hover = pvp_button.collidepoint(mouse_pos)
        pve_hover = pve_button.collidepoint(mouse_pos)
        
        for button, is_hover, y_pos, text, color in [
            (pvp_button, pvp_hover, self.height//2 - button_height - 20, "PLAYER vs PLAYER", (41, 128, 185)),
            (pve_button, pve_hover, self.height//2 + 20, "PLAYER vs AI", (39, 174, 96))
        ]:
            button_color = (color[0]+20, color[1]+20, color[2]+20) if is_hover else color
            
            # Vẽ nút với gradient
            for i in range(button_height):
                grad_value = button_color[1] - int(20 * (i / button_height))
                grad_color = (button_color[0], grad_value, button_color[2])
                pygame.draw.line(self.screen, grad_color, 
                            (button.left, y_pos + i), 
                            (button.right, y_pos + i))
            
            pygame.draw.rect(self.screen, (255, 255, 255, 50), button, 1, border_radius=3)
            
            if is_hover:
                for i in range(3):
                    glow_rect = button.inflate(i*4, i*4)
                    pygame.draw.rect(self.screen, (255, 255, 255, 50-i*15), 
                                glow_rect, 1, border_radius=3+i)
            
            button_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
            text_surf = button_font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (
                button.centerx - text_surf.get_width()//2,
                button.centery - text_surf.get_height()//2
            ))
        
        # Vẽ version và credits
        version_font = pygame.font.SysFont('Segoe UI', 16)
        version_text = version_font.render("Version 2.0", True, (180, 180, 180))
        self.screen.blit(version_text, (20, self.height - 40))
        
        icon_font = pygame.font.SysFont('Segoe UI Symbol', 36)
        chess_icons = ["♔", "♕", "♖", "♗", "♘", "♙"]
        for i, icon in enumerate(chess_icons):
            icon_color = (255, 255, 255) if i % 2 == 0 else (50, 50, 50)
            icon_surf = icon_font.render(icon, True, icon_color)
            x_pos = self.width//2 - 150 + i * 60
            self.screen.blit(icon_surf, (x_pos, self.height - 80))
        
        return pvp_button, pve_button
    
    def draw_game_over_screen(self):
        """Hiển thị màn hình kết thúc game"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            alpha = 180 + int(50 * (y / self.height))  # Alpha tăng dần từ trên xuống
            color = (10, 10, 30, alpha)
            pygame.draw.line(overlay, color, (0, y), (self.width, y))
        self.screen.blit(overlay, (0, 0))
        
        box_width = 600
        box_height = 350
        box_rect = pygame.Rect((self.width - box_width) // 2, (self.height - box_height) // 2, 
                            box_width, box_height)
        
        for y in range(box_rect.height):
            color_value = 40 + int(20 * (y / box_rect.height))
            line_color = (color_value, color_value, color_value + 10)
            pygame.draw.line(self.screen, line_color,
                        (box_rect.left, box_rect.top + y),
                        (box_rect.right, box_rect.top + y))
        
         
        pygame.draw.rect(self.screen, (212, 175, 55), box_rect, 3)  # Viền vàng
        
        for i in range(3):
            light_rect = box_rect.inflate(i*8, i*8)
            pygame.draw.rect(self.screen, (255, 215, 0, 100-i*30), light_rect, 2)
        
        game_state = self.game.get_state()
        if game_state == GameState.CHECKMATE:
            winner = "WHITE" if not self.game.current_player else "BLACK"
            message = f"{winner} WINS!"
            sub_message = "CHECKMATE"
            color = (255, 215, 0)  # Màu vàng
        elif game_state == GameState.STALEMATE:
            message = "DRAW"
            sub_message = "STALEMATE"
            color = (200, 200, 200)
        else:
            message = "DRAW"
            sub_message = ""
            color = (200, 200, 200)
        
        title_font = pygame.font.SysFont('Segoe UI', 48, bold=True)
        game_over_text = title_font.render("GAME OVER", True, (255, 255, 255))
        
        shadow_text = title_font.render("GAME OVER", True, (0, 0, 0))
        self.screen.blit(shadow_text, (self.width // 2 - game_over_text.get_width() // 2 + 3, 
                                    box_rect.y + 40 + 3))
        self.screen.blit(game_over_text, (self.width // 2 - game_over_text.get_width() // 2, 
                                        box_rect.y + 40))
        
        result_font = pygame.font.SysFont('Segoe UI', 36, bold=True)
        result_text = result_font.render(message, True, color)
        
        for i in range(3):
            glow_text = result_font.render(message, True, (*color[:3], 50-i*15))
            self.screen.blit(glow_text, (self.width // 2 - result_text.get_width() // 2 - i, 
                                    box_rect.y + 120 - i))
            self.screen.blit(glow_text, (self.width // 2 - result_text.get_width() // 2 + i, 
                                    box_rect.y + 120 + i))
        
        self.screen.blit(result_text, (self.width // 2 - result_text.get_width() // 2, 
                                    box_rect.y + 120))
        
        sub_font = pygame.font.SysFont('Segoe UI', 24)
        sub_text = sub_font.render(sub_message, True, color)
        self.screen.blit(sub_text, (self.width // 2 - sub_text.get_width() // 2, 
                                box_rect.y + 170))
        
        guide_font = pygame.font.SysFont('Segoe UI', 22)
        
        alpha = 155 + int(100 * abs(math.sin(pygame.time.get_ticks() / 500)))
        restart_color = (255, 255, 255, alpha)
        restart_text = guide_font.render("Press R to play again", True, restart_color)
        self.screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                    box_rect.y + 230))
        
        menu_text = guide_font.render("Press M to return to Menu", True, (200, 200, 200))
        self.screen.blit(menu_text, (self.width // 2 - menu_text.get_width() // 2, 
                                box_rect.y + 270))
        
        icon_font = pygame.font.SysFont('Segoe UI Symbol', 36)
        crown_icon = icon_font.render("♔", True, (255, 215, 0))
        self.screen.blit(crown_icon, (box_rect.x + 50, box_rect.y + 40))
        self.screen.blit(crown_icon, (box_rect.right - 80, box_rect.y + 40))
        
    def draw_game_info(self, screen, x, y):
        """Hiển thị thông tin cơ bản về game"""
        font = pygame.font.SysFont('Arial', 16, bold=True)
        
        mode_text = "Chế độ: " + ("Người vs Máy" if self.game.game_mode == "pve" else "Người vs Người")
        mode_surface = font.render(mode_text, True, (0, 0, 0))
        screen.blit(mode_surface, (x, y))
        
        current_player = "Trắng" if self.game.current_player else "Đen"
        player_surface = font.render(f"Lượt chơi: {current_player}", True, (0, 0, 0))
        screen.blit(player_surface, (x, y + 25))
        
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
        sidebar_rect = pygame.Rect(self.board_size + 20, 0, self.width - self.board_size - 20, self.height)
    
        for y in range(sidebar_rect.height):
            color_value = 60 + int(20 * (1 - y / sidebar_rect.height))
            pygame.draw.line(screen, (color_value, color_value, color_value+20), 
                        (sidebar_rect.left, y), (sidebar_rect.right, y))
        
        pygame.draw.rect(screen, (212, 175, 55), sidebar_rect, 2)  # Viền vàng
        
        title_font = pygame.font.SysFont('Segoe UI', 28, bold=True)
        title = title_font.render("CHESS MASTER", True, (230, 230, 230))
        
        title_shadow = title_font.render("CHESS MASTER", True, (20, 20, 20))
        screen.blit(title_shadow, (sidebar_rect.centerx - title.get_width() // 2 + 2, 25 + 2))
        screen.blit(title, (sidebar_rect.centerx - title.get_width() // 2, 25))
        
        separator_y = 70
        pygame.draw.line(screen, (212, 175, 55), 
                    (sidebar_rect.left + 20, separator_y),
                    (sidebar_rect.right - 20, separator_y), 2)
        
        y_pos = separator_y + 20
        
        # Vẽ các thành phần sidebar
        self.draw_game_info(screen, sidebar_rect.left + 20, y_pos)
        y_pos += 100
        
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
        # Increase available space for move history
        available_space = self.height - self.status_height - 110 - y_pos
        
        # Nếu không gian đủ lớn, hiển thị lịch sử
        if available_space >= 120:
            self.draw_move_history(screen, self.board_size + 20, y_pos)
            y_pos += 120
        else:
            # Hiển thị lịch sử với kích thước nhỏ hơn
            self.draw_move_history(screen, self.board_size + 20, y_pos)
            y_pos += min(available_space - 10, 100)
        
        # ===== 7. Các nút điều khiển game =====
        # Place controls at the bottom of sidebar, just above status bar
        controls_y = self.height - self.status_height - 50
        self.draw_game_controls(screen, self.board_size + 20, controls_y)
    
    def draw_game_controls(self, screen, x, y):
        """Vẽ thanh công cụ điều khiển game với giao diện tối giản và hiệu quả"""
        taskbar_width = 260
        taskbar_height = 40
        
        sidebar_width = self.width - self.board_size - 20
        taskbar_x = self.board_size + (sidebar_width - taskbar_width) // 2
        
        taskbar_rect = pygame.Rect(taskbar_x, y, taskbar_width, taskbar_height)
        
        for i in range(taskbar_height):
            ratio = i / taskbar_height
            r = int(60 + ratio * 30)
            g = int(70 + ratio * 30)
            b = int(90 + ratio * 30)
            pygame.draw.line(screen, (r, g, b), 
                          (taskbar_x, y + i), 
                          (taskbar_x + taskbar_width, y + i))
        
        pygame.draw.rect(screen, (150, 150, 150), taskbar_rect, 1, border_radius=6)
        
        buttons = [
            {"text": "HINT", "color": (41, 128, 185), "attr": "hint_button_rect", "action": self.show_hint},
            {"text": "UNDO", "color": (230, 126, 34), "attr": "undo_button_rect", "action": self.undo_move},
            {"text": "RESET", "color": (155, 89, 182), "attr": "reset_button_rect", "action": self.reset_game}
        ]
        
        button_count = len(buttons)
        button_width = taskbar_width / button_count - 10  # Margin between buttons
        button_height = taskbar_height - 10  # Padding top and bottom
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, btn in enumerate(buttons):
            # Position buttons evenly
            btn_x = taskbar_x + 5 + i * (button_width + 5)
            btn_y = y + 5
            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
            
            # Check if mouse is over button
            is_hovered = btn_rect.collidepoint(mouse_pos)
            
            color = btn["color"]
            base_color = (color[0] * 0.9, color[1] * 0.9, color[2] * 0.9)
            if is_hovered:
                base_color = color
            
            pygame.draw.rect(screen, base_color, btn_rect, border_radius=5)
            
            highlight = pygame.Rect(btn_rect.x, btn_rect.y, btn_rect.width, 1)
            pygame.draw.rect(screen, (255, 255, 255, 100), highlight)
            
            font = pygame.font.SysFont('Arial', 14, bold=True)
            text = font.render(btn["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn_rect.center)
            
            shadow_rect = text_rect.copy()
            shadow_rect.x += 1
            shadow_rect.y += 1
            shadow_text = font.render(btn["text"], True, (0, 0, 0, 120))
            screen.blit(shadow_text, shadow_rect)
            
            screen.blit(text, text_rect)
            
            setattr(self, btn["attr"], btn_rect)

    def draw_move_history(self, screen, x, y):
        """Hiển thị lịch sử các nước đi với giao diện cải tiến"""
        # Vẽ tiêu đề
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("MOVE HISTORY", True, (50, 50, 120))
        screen.blit(title, (x, y))
        
        history_width = 260
        history_height = 80
        history_rect = pygame.Rect(x, y + 25, history_width, history_height)
        
        for i in range(history_height):
            ratio = i / history_height
            r = int(245 - ratio * 10)
            g = int(245 - ratio * 10)
            b = int(245 - ratio * 5)
            pygame.draw.line(screen, (r, g, b), 
                          (x, y + 25 + i), 
                          (x + history_width, y + 25 + i))
        
        pygame.draw.rect(screen, (180, 180, 200), history_rect, 1)
        
        if not hasattr(self.game, 'move_history') or not self.game.move_history:
            empty_text = pygame.font.SysFont('Arial', 12).render("No moves yet", True, (100, 100, 120))
            screen.blit(empty_text, (x + history_width//2 - empty_text.get_width()//2, 
                                   y + 25 + history_height//2 - empty_text.get_height()//2))
            return
        
        # Hiển thị lịch sử
        font = pygame.font.SysFont('Arial', 12)
        moves_per_row = 3  
        y_offset = y + 30
        line_height = 18
        
        # Hiển thị tối đa 6 nước đi gần nhất
        start_idx = max(0, len(self.game.move_history) - 6)
        for i in range(start_idx, len(self.game.move_history)):
            move = self.game.move_history[i]
            move_num = i + 1
            row = (i - start_idx) // moves_per_row
            col = (i - start_idx) % moves_per_row
            
            color = (0, 100, 0) if i % 2 == 0 else (150, 0, 0)  # Xanh cho quân trắng, đỏ cho quân đen
            
            move_text = f"{move_num}.{move}"
            text = font.render(move_text, True, color)
            screen.blit(text, (x + 15 + col * 85, y_offset + row * line_height))

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
        """Draw AI learning mode toggle button"""
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        title = font_title.render("Learning Mode", True, (50, 50, 100))
        screen.blit(title, (x, y))
        
        button_rect = pygame.Rect(x, y + 25, 200, 30)
        button_color = (0, 180, 0) if self.ai.learning_enabled else (180, 0, 0)
        
        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, (255, 255, 255), button_rect.inflate(-4, -4), 1)  # Inner border
        pygame.draw.rect(screen, (50, 50, 50), button_rect, 1)  # Outer border
        
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text = font.render("ON" if self.ai.learning_enabled else "OFF", True, (255, 255, 255))
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        self.learning_toggle_rect = button_rect

    def draw_game_state(self, screen, state):
        """Draw game state"""
        message = ""
        if state == GameState.CHECKMATE:
            winner = "White" if not self.game.current_player else "Black"
            message = f"{winner} wins! - Checkmate!"
        elif state == GameState.STALEMATE:
            message = "Draw - Stalemate"
        else:
            message = "Draw"
        
        font = pygame.font.SysFont('Arial', 24)
        text = font.render(message, True, (200, 0, 0))
        screen.blit(text, (self.board_size + 20, 200))
    
    def run(self):
        """Chạy game với menu chính"""
        self.running = True
        clock = pygame.time.Clock()
        
        self.in_menu = True
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                
                if self.in_menu:
                    if event.type == pygame.MOUSEBUTTONDOWN:
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
            
            if self.in_menu:
                self.draw_game_menu()
            else:
                self.render(self.screen)
            
            pygame.display.flip()
            
            clock.tick(60)
        
        pygame.quit()