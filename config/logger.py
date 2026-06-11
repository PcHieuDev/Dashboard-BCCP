import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# Đảm bảo thư mục logs tồn tại
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "dashboard.log"

def get_logger(name: str) -> logging.Logger:
    """
    Khởi tạo và trả về logger chuẩn cho ứng dụng.
    - Ghi log ra file logs/dashboard.log (giữ 5 file, mỗi file max 10MB).
    - Ghi log ra console (stdout).
    """
    logger = logging.getLogger(name)
    
    # Nếu logger đã được cấu hình thì trả về luôn để tránh ghi log trùng lặp
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Format của log
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. File Handler: Ghi vào file với giới hạn 10MB, giữ tối đa 5 file backup
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 2. Console Handler: Ghi ra màn hình
    console_handler = logging.StreamHandler(sys.stdout)
    # Console format có thể rút gọn hơn nếu cần, nhưng dùng chung format cho chuẩn
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
