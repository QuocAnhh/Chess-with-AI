import time
import threading
import psutil  # Bạn cần cài đặt package này: pip install psutil

class AIOptimizer:
    """Lớp tối ưu hiệu năng cho AI"""
    
    @staticmethod
    def check_system_resources():
        """Kiểm tra tài nguyên hệ thống để quyết định độ phức tạp của AI"""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        print(f"CPU: {cpu_percent}%, RAM: {memory_percent}%")
        
        # Xác định mức độ tài nguyên có sẵn
        if cpu_percent > 80 or memory_percent > 80:
            # Tài nguyên thấp, giảm độ phức tạp
            return {"max_depth": 2, "use_position_tables": False, "prune_value_table": True}
        elif cpu_percent > 60 or memory_percent > 60:
            # Tài nguyên trung bình
            return {"max_depth": 3, "use_position_tables": True, "prune_value_table": True}
        else:
            # Tài nguyên cao
            return {"max_depth": 4, "use_position_tables": True, "prune_value_table": False}
    
    @staticmethod
    def run_ai_in_thread(ai, board, callback):
        """Chạy AI trong một thread riêng để không làm đơ giao diện"""
        def ai_thread():
            start_time = time.time()
            move = ai.get_move(board)
            elapsed = time.time() - start_time
            print(f"AI tính toán trong {elapsed:.2f} giây")
            callback(move)
        
        # Khởi chạy thread
        thread = threading.Thread(target=ai_thread)
        thread.daemon = True  # Thread sẽ tắt khi chương trình chính kết thúc
        thread.start()
        
        return thread