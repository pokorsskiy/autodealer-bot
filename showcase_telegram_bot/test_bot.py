"""Проверка основного пользовательского сценария без подключения к Telegram."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("BOT_TOKEN", "test-token")

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
        from_user=SimpleNamespace(id=101, first_name="Иван"),
        chat=SimpleNamespace(id=202),
    )


class TelegramShowcaseFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        bot_module.calculator_sessions.clear()
        bot_module.order_sessions.clear()
        bot_module.last_calculations.clear()

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
                "🌐 Наши соцсети",
                "🟠 Заказать автомобиль",
            ],
        )

    def test_reviews_and_community_use_clear_placeholders(self) -> None:
        buttons = {
            button.text: button
            for row in bot_module.main_menu().keyboard
            for button in row
        }
        self.assertIsNone(buttons["⭐ Отзывы"].url)
        self.assertEqual(buttons["⭐ Отзывы"].callback_data, "reviews")
        self.assertIsNone(buttons["💬 Общий чат"].url)
        self.assertEqual(buttons["💬 Общий чат"].callback_data, "community")
        self.assertIsNone(buttons["📞 Связаться"].url)
        self.assertEqual(buttons["📞 Связаться"].callback_data, "manager")

    def test_only_start_command_is_configured(self) -> None:
        with (
            patch.object(bot_module.bot, "set_my_commands") as set_commands,
            patch.object(bot_module.bot, "set_chat_menu_button") as set_menu_button,
        ):
            bot_module.configure_commands()
        commands = set_commands.call_args.args[0]
        self.assertEqual([(command.command, command.description) for command in commands], [("start", "Запустить бота")])
        self.assertIsInstance(
            set_menu_button.call_args.kwargs["menu_button"],
            bot_module.types.MenuButtonCommands,
        )

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
                SimpleNamespace(message_id=505),
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
            self.assertEqual(bot_module.calculator_sessions[101]["message_id"], 505)
            edit_message.assert_not_called()

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
        self.assertTrue(manager_button.url or manager_button.callback_data == "manager")

    def test_cancel_deletes_only_calculator_message(self) -> None:
        bot_module.calculator_sessions[101] = {"step": "price", "message_id": 505}
        with (
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "delete_message") as delete_message,
            patch.object(bot_module.bot, "edit_message_text") as edit_message,
        ):
            bot_module.handle_callback(callback("calc:cancel", message_id=505))

        delete_message.assert_called_once_with(202, 505)
        edit_message.assert_not_called()
        self.assertNotIn(101, bot_module.calculator_sessions)

    def test_order_collects_request_and_sends_it_to_manager(self) -> None:
        bot_module.last_calculations[101] = "Итого: 3 000 000 ₽"
        with (
            patch.object(bot_module, "YOUR_CHAT_ID", 909),
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "delete_message") as delete_message,
        ):
            send_message.side_effect = (SimpleNamespace(message_id=606), None, None)
            bot_module.handle_callback(callback("order"))
            self.assertEqual(bot_module.order_sessions[101]["message_id"], 606)
            self.assertIn("какой автомобиль", send_message.call_args.args[1])
            bot_module.handle_text(text_message("Нужен BMW X5 до 6 000 000 ₽"))

        self.assertEqual(send_message.call_count, 3)
        self.assertEqual(send_message.call_args_list[1].args[0], 909)
        self.assertIn("Новая заявка", send_message.call_args_list[1].args[1])
        self.assertIn("BMW X5", send_message.call_args_list[1].args[1])
        self.assertIn("Итого: 3 000 000 ₽", send_message.call_args_list[1].args[1])
        self.assertIn("Заявка отправлена", send_message.call_args_list[2].args[1])
        self.assertEqual(
            send_message.call_args_list[2].kwargs["reply_markup"].keyboard[0][0].callback_data,
            "order:menu",
        )
        delete_message.assert_called_once_with(202, 606)
        self.assertNotIn(101, bot_module.order_sessions)

    def test_order_confirmation_sends_new_menu_and_removes_button(self) -> None:
        with (
            patch.object(bot_module.bot, "answer_callback_query"),
            patch.object(bot_module.bot, "edit_message_text") as edit_message,
            patch.object(bot_module.bot, "send_message") as send_message,
            patch.object(bot_module.bot, "delete_message") as delete_message,
        ):
            send_message.side_effect = (
                SimpleNamespace(message_id=707),
                SimpleNamespace(message_id=708),
            )
            bot_module.handle_callback(callback("order:menu", message_id=606))

        self.assertEqual(edit_message.call_args.kwargs["reply_markup"], None)
        self.assertEqual(edit_message.call_args.kwargs["message_id"], 606)
        self.assertEqual(
            send_message.call_args_list[1].kwargs["reply_markup"].keyboard[0][0].text,
            "🧮 Калькулятор",
        )
        delete_message.assert_called_once_with(202, 707)

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
