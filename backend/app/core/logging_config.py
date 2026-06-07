import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level: int = logging.INFO):
    root = logging.getLogger()
    root.setLevel(level)

    # 清除已有 handler（避免重复添加）
    root.handlers.clear()

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    # 滚动文件 (10MB x 5)
    file_handler = RotatingFileHandler(
        LOG_DIR / "quant_dashboard.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_handler)

    # 错误单独记录
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(error_handler)

    # 抑制第三方库噪音
    for lib in ["urllib3", "httpx", "httpcore", "asyncio", "sqlalchemy.engine"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return root
