"""Проверки обоих пользовательских сценариев Hybrid-бота без Telegram."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("SHOWCASE_HYBRID_BOT_TOKEN", "test-token")
os.environ.setdefault("SHOWCASE_HYBRID_WEB_APP_URL", "https://example.com/webapp")

import bot as bot_module
import keyboards as keyboards_module
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


def webapp_message(payload: dict[str, str]) -> SimpleNamespace:
    message = text_message("")
    message.web_app_data = SimpleNamespace(data=json.dumps(payload, ensure_ascii=False))
    return message


class HybridBotTest(unittest.TestCase):
    def setUp(self) -> None:
        bot_module.calculator_sessions.clear()

    def test_main_menu_combines_chat_and_webapp_actions(self) -> None:
        labels = [
            button.text
            for row in bot_module.main_menu("https://example.com/webapp").keyboard
            for button in row
        ]
        self.assertEqual(
            labels,
            [
                "🚗 Смотреть автомобили",
                "🧮 Рассчитать",
                "💬 Менеджер",
                "⭐ Отзывы",
                "◌ Сообщество",
                "❔ Вопросы",
                "◎ Соцсети",
            ],
        )
        buttons = [
            button
            for row in bot_module.main_menu("https://example.com/webapp").keyboard
            for button in row
        ]
        self.assertEqual(buttons[0].web_app.url, "https://example.com/webapp")
        self.assertEqual(buttons[-1].text, "◎ Соцсети")

    def test_invalid_webapp_url_uses_clear_placeholder(self) -> None:
        buttons = [
            button
            for row in bot_module.main_menu("").keyboard
            for button in row
        ]
        self.assertEqual(buttons[0].callback_data, "stub:webapp")

    def test_manager_button_uses_direct_url_when_configured(self) -> None:
        with patch.object(keyboards_module, "MANAGER_URL", "https://t.me/dealer_auto"):
            buttons = [
                button
                for row in keyboards_module.main_menu("https://example.com/webapp").keyboard
                for button in row
            ]
        manager_button = next(button for button in buttons if button.text == "💬 Менеджер")
        self.assertEqual(manager_button.url, "https://t.me/dealer_auto")

    def test_manager_button_uses_placeholder_without_link(self) -> None:
        with patch.object(keyboards_module, "MANAGER_URL", ""):
            buttons = [
                button
                for row in keyboards_module.main_menu("https://example.com/webapp").keyboard
                for button in row
            ]
        manager_button = next(button for button in buttons if button.text == "💬 Менеджер")
        self.assertEqual(manager_button.callback_data, "stub:manager")

    def test_site_command_sends_webapp_button(self) -> None:
        with (
            patch.object(bot_module, "WEB_APP_URL", "https://example.com/webapp"),
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "delete_message"),
        ):
            send_message.side_effect = [SimpleNamespace(message_id=808), None]
            bot_module.site(text_message("/site"))

        markup = send_message.call_args_list[1].kwargs["reply_markup"]
        button = markup.keyboard[0][0]
        self.assertEqual(button.text, "🚗 Открыть каталог")
        self.assertEqual(button.web_app.url, "https://example.com/webapp")

    def test_site_command_is_registered(self) -> None:
        with (
            patch.object(bot_module.bot, "set_my_commands") as set_commands,
            patch.object(bot_module.bot, "set_chat_menu_button"),
        ):
            bot_module.configure_commands()
        commands = set_commands.call_args.args[0]
        self.assertEqual(
            [(command.command, command.description) for command in commands],
            [
                ("start", "Запустить бота"),
                ("menu", "Открыть меню"),
                ("site", "Открыть Web App"),
            ],
        )

    def test_calculator_flow(self) -> None:
        with (
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "edit_message_text") as edit_message,
        ):
            send_message.return_value = SimpleNamespace(message_id=404)
            bot_module.handle_callback(callback("calculator"))
            self.assertEqual(bot_module.calculator_sessions[101]["step"], "mode")
            bot_module.handle_callback(callback("calc:mode:budget", message_id=404))
            bot_module.handle_text(text_message("2 500 000 ₽"))
            bot_module.handle_callback(callback("calc:age:3_to_5", message_id=404))
            bot_module.handle_text(text_message("2,0 л"))

        self.assertNotIn(101, bot_module.calculator_sessions)
        final_text = edit_message.call_args.args[0]
        self.assertIn("Ориентир на автомобиль", final_text)
        self.assertIn("Доставка и расходы", final_text)
        self.assertIn("Расчёт выполнен по указанной ориентировочной стоимости", final_text)
        result_markup = edit_message.call_args.kwargs["reply_markup"]
        self.assertEqual(result_markup.keyboard[0][0].text, "🟠 Обсудить с менеджером")

    def test_calculator_uses_webapp_input_steps(self) -> None:
        bot_module.calculator_sessions[101] = {
            "step": "price",
            "price_mode": "known",
            "message_id": 404,
        }
        with patch.object(bot_module.bot, "send_message") as send_message:
            bot_module.handle_text(text_message("2 505 000"))
        self.assertEqual(bot_module.calculator_sessions[101]["step"], "price")
        self.assertIn("шагом 10 000", send_message.call_args.args[1])

        bot_module.calculator_sessions[101] = {
            "step": "engine",
            "price_mode": "known",
            "car_price_rub": 2_500_000,
            "age": "3_to_5",
            "message_id": 404,
        }
        with patch.object(bot_module.bot, "send_message") as send_message:
            bot_module.handle_text(text_message("1,65"))
        self.assertEqual(bot_module.calculator_sessions[101]["step"], "engine")
        self.assertIn("шагом 0.1", send_message.call_args.args[1])

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
