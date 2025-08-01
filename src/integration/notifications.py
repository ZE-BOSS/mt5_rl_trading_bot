import os
from telegram import Bot
import time

class NotificationManager:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None
        self.last_sent = {}
        self.initialize_bot()

    def initialize_bot(self):
        if not self.telegram_token or not self.chat_id:
            return
            
        try:
            self.bot = Bot(token=self.telegram_token)
            # Test connection
            self.bot.get_me()
        except Exception as e:
            print(f"Telegram init failed: {e}")

    def send_trade_alert(self, symbol, action, size, price, sl, tp):
        if not self.bot:
            return False
            
        message = (
            f"🚀 *Trade Executed*\n"
            f"• Symbol: {symbol}\n"
            f"• Action: {'BUY' if action == 'buy' else 'SELL'}\n"
            f"• Size: {size} lots\n"
            f"• Price: {price:.5f}\n"
            f"• SL: {sl:.5f}\n"
            f"• TP: {tp:.5f}"
        )
        return self._send_message(message)

    def send_error_alert(self, error_message):
        return self._send_message(f"❌ *ERROR*\n{error_message[:200]}")

    def _send_message(self, text, retry=3):
        # Prevent message flooding
        if time.time() - self.last_sent.get(text[:20], 0) < 5:
            return False
            
        for attempt in range(retry):
            try:
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode='Markdown'
                )
                self.last_sent[text[:20]] = time.time()
                return True
            except Exception as e:
                if "429" in str(e):  # Rate limited
                    time.sleep(2 ** attempt)
                else:
                    break
        return False