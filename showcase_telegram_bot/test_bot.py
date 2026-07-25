"""Проверка основного пользовательского сценария без подключения к Telegram."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("BOT_TOKEN", "test-token")

import bot as bot_module
import logger as logger_module


def callback(data: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"callback-{data}",
        data=data,
        from_user=SimpleNamespace(id=101, first_name="Иван"),
        message=SimpleNamespace(
            chat=SimpleNamespace(id=202),
            message_id=303,
        ),
    )


def text_message(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=101, first_name="Иван"),
        chat=SimpleNamespace(id=202),
    )


class TelegramShowcaseFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        bot_module.calculator_sessions.clear()

    def test_main_menu_sections(self) -> None:
        labels = [
            button.text
            for row in bot_module.main_menu().keyboard
            for button in row
        ]
        self.assertEqual(
            labels,
            [
                "🧮 Калькулятор",
                "📞 Связаться",
                "⭐ Отзывы",
                "💬 Общий чат",
                "❓ Популярные вопросы",
                "🌐 Другие соцсети",
            ],
        )

    def test_only_start_command_is_configured(self) -> None:
        with patch.object(bot_module.bot, "set_my_commands") as set_commands:
            bot_module.configure_commands()
        commands = set_commands.call_args.args[0]
        self.assertEqual([(command.command, command.description) for command in commands], [("start", "Запустить бота")])

    def test_calculator_parses_rubles_and_liters(self) -> None:
        self.assertEqual(bot_module._parse_rub_price("2 500 000 ₽"), 2_500_000)
        self.assertEqual(bot_module._parse_rub_price("2\xa0500\xa0000 руб."), 2_500_000)
        self.assertEqual(bot_module._parse_engine_liters("1,6 л"), 1.6)
        self.assertEqual(bot_module._parse_engine_liters("2.0 литра"), 2.0)

    def test_calculator_flow(self) -> None:
        with (
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "edit_message_text") as edit_message,
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "delete_message") as delete_message,
        ):
            send_message.side_effect = (
                SimpleNamespace(message_id=404),
                SimpleNamespace(message_id=405),
            )
            bot_module.start(text_message("/start"))
            self.assertIsInstance(
                send_message.call_args_list[0].kwargs["reply_markup"],
                bot_module.types.ReplyKeyboardRemove,
            )
            self.assertEqual(
                send_message.call_args_list[1].kwargs["reply_markup"].keyboard[0][0].text,
                "🧮 Калькулятор",
            )
            delete_message.assert_called_once_with(202, 404)
            edit_message.assert_not_called()

            bot_module.handle_callback(callback("calculator"))
            self.assertEqual(bot_module.calculator_sessions[101]["step"], "price")

            bot_module.handle_text(text_message("2 500 000 ₽"))
            self.assertEqual(bot_module.calculator_sessions[101]["step"], "age")

            bot_module.handle_callback(callback("calc:age:3_to_5"))
            self.assertEqual(bot_module.calculator_sessions[101]["step"], "engine")

            bot_module.handle_text(text_message("2,0 л"))

        self.assertNotIn(101, bot_module.calculator_sessions)
        final_text = edit_message.call_args.args[0]
        self.assertIn("Итого ориентировочно", final_text)
        self.assertIn("2.0 л (2 000 см³)", final_text)
        manager_button = edit_message.call_args.kwargs["reply_markup"].keyboard[0][0]
        self.assertTrue(manager_button.url or manager_button.callback_data == "stub:manager")

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
