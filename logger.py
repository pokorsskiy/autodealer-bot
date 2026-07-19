"""
Модуль стилизованного логирования для Telegram бота.
Обеспечивает удобный вывод событий в консоль с эмодзи и временными метками.
"""

import logging
import sys
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Настройка базового логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger("autodealer-bot")

def log_msg(user_id: int, username: str | None, command_or_text: str):
    """Логирование входящих сообщений"""
    user_str = f"@{username}" if username else f"ID:{user_id}"
    logger.info(f"📩 [MSG] Пользователь {user_str}: {command_or_text}")

def log_db(action: str, details: str = ""):
    """Логирование операций с базой данных"""
    logger.info(f"💾 [DB] {action} {f'({details})' if details else ''}")

def log_admin(action: str):
    """Логирование отправки уведомлений админу"""
    logger.info(f"🔔 [ADMIN] {action}")

def log_error(context: str, error: Exception | str):
    """Логирование ошибок"""
    logger.error(f"❌ [ERROR] Ошибка в {context}: {error}")

def log_system(text: str):
    """Системные логи запуска/остановки"""
    logger.info(f"🚀 [SYSTEM] {text}")
