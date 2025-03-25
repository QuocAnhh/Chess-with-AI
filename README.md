# Chess with AI

![Chess Game](https://img.shields.io/badge/Chess-AI-brightgreen)
![Status](https://img.shields.io/badge/Status-Active-success)

Một ứng dụng cờ vua với trí tuệ nhân tạo, cho phép người dùng chơi cờ với máy tính ở nhiều cấp độ khác nhau.

![Chess Game Preview](assets/preview.png)

## 📋 Tính năng

- Giao diện đồ họa trực quan của bàn cờ vua
- Chơi với AI ở nhiều cấp độ khó khác nhau
- Hỗ trợ tất cả luật cờ vua tiêu chuẩn:
  - Nhập thành (castling)
  - Bắt tốt qua đường (en passant)
  - Phong cấp (promotion)
- Hiển thị các nước đi hợp lệ
- Tính năng undo/redo nước đi
- Lưu và tải các ván cờ
- Hiển thị lịch sử các nước đi

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8 hoặc cao hơn
- Các thư viện cần thiết (liệt kê trong `requirements.txt`)

### Cách cài đặt
1. Clone repository này:
```
git clone https://github.com/QuocAnhh/Chess-with-AI.git
cd Chess-with-AI
```

2. Cài đặt các thư viện phụ thuộc:
```
pip install -r requirements.txt
```

## 🎮 Cách sử dụng

Chạy chương trình với lệnh:
```
python main.py
```

### Hướng dẫn điều khiển:
- Click chuột để chọn quân cờ và di chuyển
- Nhấn `R` để reset game/chơi ván mới
- Nhấn `Z` để đi lại nước đi (Undo)
- Nhấn `H` để hiển thị gợi ý nước đi tốt
- Nhấn `P` để tạm dừng game
- Nhấn `M` để quay về menu chính

## 🧠 Thuật toán AI

Dự án sử dụng thuật toán Minimax với cắt tỉa Alpha-Beta để điều khiển AI. Các cấp độ khó khác nhau được thực hiện bằng cách thay đổi độ sâu tìm kiếm của thuật toán.

## 💻 Công nghệ sử dụng

- Python
- Pygame cho giao diện đồ họa

## 🔄 Cấu trúc dự án

```
Chess-with-AI/
├── __init__.py         # Để Python nhận diện thư mục như 1 Package
├── board.py           # Lớp đại diện cho bàn cờ
├── learning_chess_ai.py     # Triển khai AI
├── game.py            # Quản lý trạng thái trò chơi
├── ui.py              # Tiện ích hỗ trợ
├── assets/            # Hình ảnh và âm thanh
└── requirements.txt   # Các thư viện phụ thuộc
```

## 🤝 Đóng góp

Dự án vẫn đang trong giai đoạn hoàn thiện, vậy nên mọi đóng góp của mọi người đều rất đáng giá và hoan nghênh! Nếu mọi người muốn đóng góp vào dự án, hãy làm theo các bước sau:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/amazing-feature`)
3. Commit thay đổi của bạn (`git commit -m 'Add some amazing feature'`)
4. Push lên branch (`git push origin feature/amazing-feature`)
5. Mở Pull Request


## 📧 Liên hệ

Github - [GitHub](https://github.com/QuocAnhh)

Facebook - https://www.facebook.com/quocanh161004

Telegram - @quoccankk
