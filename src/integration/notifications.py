from telegram import Bot
import os

class NotificationManager:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.bot = Bot(token=self.telegram_token)

    def send_trade_alert(self, message):
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_error_alert(self, error_message):
        self.bot.send_message(chat_id=self.chat_id, text=f"Error: {error_message}")

    def send_performance_update(self, performance_metrics):
        message = f"Performance Update:\n{performance_metrics}"
        self.bot.send_message(chat_id=self.chat_id, text=message)