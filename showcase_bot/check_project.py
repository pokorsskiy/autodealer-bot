"""Быстрая проверка структуры бота-витрины без подключения к Telegram."""

from pathlib import Path


REQUIRED_FILES = (
    "bot.py",
    "config.py",
    "database.py",
    "keyboards.py",
    "logger.py",
    ".env.example",
)


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    missing = [name for name in REQUIRED_FILES if not (project_dir / name).is_file()]
    if missing:
        raise SystemExit(f"Не найдены файлы: {', '.join(missing)}")
    print("Структура showcase_bot корректна.")


if __name__ == "__main__":
    main()
