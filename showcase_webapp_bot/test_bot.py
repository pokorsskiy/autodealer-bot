"""Проверки Web App-бота без подключения к Telegram."""

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("SHOWCASE_WEBAPP_BOT_TOKEN", "test-token")
os.environ.setdefault("SHOWCASE_WEB_APP_URL", "https://example.com/webapp")

import bot as bot_module
import database as database_module
import logger as logger_module


def user_message(raw_data: str) -> SimpleNamespace:
    return SimpleNamespace(
        chat=SimpleNamespace(id=202),
        from_user=SimpleNamespace(
            id=101,
            first_name="Иван",
            last_name="Петров",
            username="ivan_auto",
        ),
        web_app_data=SimpleNamespace(data=raw_data),
    )


class WebAppBotTest(unittest.TestCase):
    def test_parse_car_lead(self) -> None:
        lead = bot_module._parse_lead(
            """
            {
              "lead_type": "car",
              "car_id": "bmw-x5-2023",
              "name": "Иван",
              "phone": "+7 999 123-45-67",
              "username": "@ivan",
              "car_interest": "BMW X5 (2023)",
              "purchase_method": "Наличные",
              "comment": "Светлый салон"
            }
            """
        )
        self.assertIsNotNone(lead)
        self.assertEqual(lead["lead_type"], "car")
        self.assertEqual(lead["car_id"], "bmw-x5-2023")

    def test_manager_lead_requires_comment(self) -> None:
        lead = bot_module._parse_lead(
            """
            {
              "lead_type": "manager",
              "name": "Иван",
              "phone": "+7 999 123-45-67",
              "car_interest": "Нужна помощь с выбором",
              "purchase_method": "Нужна консультация",
              "comment": ""
            }
            """
        )
        self.assertIsNone(lead)

    def test_invalid_phone_is_rejected(self) -> None:
        lead = bot_module._parse_lead(
            """
            {
              "lead_type": "car",
              "name": "Иван",
              "phone": "123",
              "car_interest": "Toyota Camry",
              "purchase_method": "Кредит"
            }
            """
        )
        self.assertIsNone(lead)

    def test_start_has_single_webapp_button(self) -> None:
        message = SimpleNamespace(
            chat=SimpleNamespace(id=202),
            from_user=SimpleNamespace(id=101),
        )
        with (
            patch.object(bot_module, "WEB_APP_URL", "https://example.com/webapp"),
            patch.object(bot_module.bot, "send_message") as send_message,
        ):
            bot_module.start(message)

        markup = send_message.call_args.kwargs["reply_markup"]
        buttons = [button for row in markup.keyboard for button in row]
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].text, "🚗 Открыть Web App")
        self.assertEqual(buttons[0].web_app.url, "https://example.com/webapp")

    def test_valid_lead_is_saved_and_sent_to_manager(self) -> None:
        raw_data = (
            '{"lead_type":"car","car_id":"toyota-camry-2024","name":"Иван",'
            '"phone":"+7 999 123-45-67","username":"@ivan","car_interest":"Toyota Camry",'
            '"purchase_method":"Наличные","comment":""}'
        )
        with (
            patch.object(bot_module, "YOUR_CHAT_ID", 909),
            patch.object(bot_module, "save_lead") as save_lead,
            patch.object(bot_module.bot, "send_message") as send_message,
        ):
            bot_module.handle_webapp_data(user_message(raw_data))

        save_lead.assert_called_once()
        self.assertEqual(send_message.call_args_list[0].args[0], 909)
        self.assertIn("Toyota Camry", send_message.call_args_list[0].args[1])
        self.assertIn("Заявка принята", send_message.call_args_list[1].args[1])

    def test_database_migration_preserves_old_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "legacy.db"
            with closing(sqlite3.connect(db_path)) as connection:
                with connection:
                    connection.execute(
                        """
                        CREATE TABLE webapp_leads (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            username TEXT,
                            name TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            car_interest TEXT NOT NULL,
                            purchase_method TEXT NOT NULL,
                            comment TEXT,
                            created_at TEXT NOT NULL
                        )
                        """
                    )
                    connection.execute(
                        """
                        INSERT INTO webapp_leads (
                            user_id, username, name, phone, car_interest,
                            purchase_method, comment, created_at
                        ) VALUES (1, 'old_user', 'Старый лид', '+79991234567',
                                  'Toyota', 'Наличные', '', '2026-01-01T12:00:00')
                        """
                    )

            with patch.object(database_module, "DB_NAME", str(db_path)):
                database_module.init_db()

            with closing(sqlite3.connect(db_path)) as connection:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(webapp_leads)")
                }
                count = connection.execute("SELECT COUNT(*) FROM webapp_leads").fetchone()[0]

            self.assertTrue({"lead_type", "contact_username", "car_id"} <= columns)
            self.assertEqual(count, 1)
            self.assertTrue(Path(f"{db_path}.bak").exists())

    def test_safe_handler_does_not_send_traceback(self) -> None:
        fake_bot = Mock()

        @logger_module.safe_handler(fake_bot)
        def broken_handler(message: SimpleNamespace) -> None:
            raise RuntimeError("секретные детали")

        with (
            patch.object(logger_module, "YOUR_CHAT_ID", 202),
            patch.object(logger_module.logger, "exception"),
        ):
            broken_handler(SimpleNamespace(chat=SimpleNamespace(id=202)))

        self.assertEqual(fake_bot.send_message.call_count, 1)
        sent_text = fake_bot.send_message.call_args.args[1]
        self.assertNotIn("Traceback", sent_text)
        self.assertNotIn("секретные детали", sent_text)


if __name__ == "__main__":
    unittest.main()
