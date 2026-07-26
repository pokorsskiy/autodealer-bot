"""Проверки обоих пользовательских сценариев Hybrid-бота без Telegram."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("SHOWCASE_HYBRID_BOT_TOKEN", "test-token")
os.environ.setdefault("SHOWCASE_HYBRID_WEB_APP_URL", "https://example.com/webapp")

import bot as bot_module
import logger as logger_module


def callback(data: str, message_id: int = 303) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"callback-{data}",
        data=data,
        from_user=SimpleNamespace(id=101, first_name="Иван"),
        message=SimpleNamespace(
            chat=SimpleNamespace(id=202),
            message_id=message_id,
        ),
    )


def text_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(
            id=101,
            first_name="Иван",
            last_name="Петров",
            username="ivan_auto",
        ),
        chat=SimpleNamespace(id=202),
    )


def contact_message(user_id: int = 101, phone: str = "+7 999 123-45-67") -> SimpleNamespace:
    message = text_message("")
    message.contact = SimpleNamespace(user_id=user_id, phone_number=phone)
    return message


def webapp_message(payload: dict[str, str]) -> SimpleNamespace:
    message = text_message("")
    message.web_app_data = SimpleNamespace(data=json.dumps(payload, ensure_ascii=False))
    return message


class HybridBotTest(unittest.TestCase):
    def setUp(self) -> None:
        bot_module.calculator_sessions.clear()
        bot_module.waiting_for_phone.clear()

    def test_main_menu_combines_chat_and_webapp_actions(self) -> None:
        labels = [
            button.text
            for row in bot_module.main_menu("https://example.com/webapp").keyboard
            for button in row
        ]
        self.assertEqual(
            labels,
            [
                "🚗 Автомобили в наличии",
                "🧮 Калькулятор",
                "📞 Связаться",
                "⭐ Отзывы",
                "💬 Общий чат",
                "❓ Популярные вопросы",
                "🌐 Другие соцсети",
                "🌍 Сайт",
            ],
        )
        buttons = [
            button
            for row in bot_module.main_menu("https://example.com/webapp").keyboard
            for button in row
        ]
        self.assertEqual(buttons[0].web_app.url, "https://example.com/webapp")
        self.assertEqual(buttons[-1].web_app.url, "https://example.com/webapp")

    def test_invalid_webapp_url_uses_clear_placeholder(self) -> None:
        buttons = [
            button
            for row in bot_module.main_menu("").keyboard
            for button in row
        ]
        self.assertEqual(buttons[0].callback_data, "stub:webapp")
        self.assertEqual(buttons[-1].callback_data, "stub:webapp")

    def test_calculator_flow(self) -> None:
        with (
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "edit_message_text") as edit_message,
        ):
            send_message.return_value = SimpleNamespace(message_id=404)
            bot_module.handle_callback(callback("calculator"))
            bot_module.handle_text(text_message("2 500 000 ₽"))
            bot_module.handle_callback(callback("calc:age:3_to_5", message_id=404))
            bot_module.handle_text(text_message("2,0 л"))

        self.assertNotIn(101, bot_module.calculator_sessions)
        final_text = edit_message.call_args.args[0]
        self.assertIn("Итого ориентировочно", final_text)
        self.assertIn("2.0 л (2 000 см³)", final_text)

    def test_contact_flow_saves_lead_with_telegram_source(self) -> None:
        bot_module.waiting_for_phone.add(101)
        with (
            patch.object(bot_module, "YOUR_CHAT_ID", 909),
            patch.object(bot_module, "save_lead") as save_lead,
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "delete_message"),
        ):
            send_message.side_effect = [
                None,
                None,
                SimpleNamespace(message_id=707),
                None,
            ]
            bot_module.handle_contact(contact_message())

        save_lead.assert_called_once_with(
            101,
            "ivan_auto",
            "telegram",
            "Связь с менеджером",
            "+7 999 123-45-67",
        )
        manager_notice = send_message.call_args_list[0].args[1]
        self.assertIn("Источник:</b> Telegram-чат", manager_notice)
        self.assertNotIn(101, bot_module.waiting_for_phone)

    def test_foreign_contact_is_rejected(self) -> None:
        bot_module.waiting_for_phone.add(101)
        with (
            patch.object(bot_module, "save_lead") as save_lead,
            patch.object(bot_module.bot, "send_message") as send_message,
        ):
            bot_module.handle_contact(contact_message(user_id=999))
        save_lead.assert_not_called()
        self.assertIn("свой номер", send_message.call_args.args[1])

    def test_webapp_lead_is_validated_saved_and_notified(self) -> None:
        payload = {
            "lead_type": "car",
            "car_id": "bmw-x5-2023",
            "name": "Иван",
            "phone": "+7 999 123-45-67",
            "username": "@ivan",
            "car_interest": "BMW X5 (2023)",
            "purchase_method": "Наличные",
            "comment": "Светлый салон",
        }
        with (
            patch.object(bot_module, "YOUR_CHAT_ID", 909),
            patch.object(bot_module, "save_lead") as save_lead,
            patch.object(bot_module.bot, "send_message") as send_message,
        ):
            bot_module.handle_webapp_data(webapp_message(payload))

        save_lead.assert_called_once_with(
            101,
            "ivan_auto",
            "webapp_car",
            "BMW X5 (2023)",
            "+7 999 123-45-67",
        )
        self.assertIn(
            "Источник:</b> Web App",
            send_message.call_args_list[0].args[1],
        )
        self.assertIn("Заявка из Web App принята", send_message.call_args_list[1].args[1])

    def test_invalid_webapp_phone_is_rejected(self) -> None:
        payload = {
            "lead_type": "car",
            "name": "Иван",
            "phone": "123",
            "car_interest": "BMW X5",
            "purchase_method": "Наличные",
        }
        with (
            patch.object(bot_module, "save_lead") as save_lead,
            patch.object(bot_module.bot, "send_message") as send_message,
        ):
            bot_module.handle_webapp_data(webapp_message(payload))
        save_lead.assert_not_called()
        self.assertIn("Не удалось прочитать заявку", send_message.call_args.args[1])

    def test_safe_handler_does_not_send_exception_details(self) -> None:
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
