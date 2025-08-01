import logging
import os
import sys

class Logger:
    def __init__(self, log_file='trading_bot.log'):
        self.logger = logging.getLogger('TradingBotLogger')
        self.logger.setLevel(logging.DEBUG)

        # Ensure journals directory exists
        os.makedirs('journals', exist_ok=True)

        # File handler with UTF-8 encoding
        file_handler = logging.FileHandler(os.path.join('journals', log_file), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler with UTF-8-safe output
        console_handler = self._get_utf8_console_handler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def _get_utf8_console_handler(self):
        """Create a console handler that writes UTF-8 safe output even on Windows."""
        if os.name == 'nt':
            try:
                sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
            except:
                pass  # fallback if not allowed
        return logging.StreamHandler(sys.stdout)

    def log(self, message):
        self.logger.info(message)

    def log_trade(self, trade_entry):
        self.logger.info(f'📈 Trade Entry: {trade_entry}')

    def log_exit(self, trade_exit):
        self.logger.info(f'📉 Trade Exit: {trade_exit}')

    def log_confluence(self, confluence_info):
        self.logger.debug(f'🔍 Confluence Detected: {confluence_info}')

    def log_error(self, error_message):
        self.logger.error(f'❌ Error: {error_message}')

    def log_performance(self, performance_metrics):
        self.logger.info(f'📊 Performance Metrics: {performance_metrics}')

# Example usage:
# logger = Logger()
# logger.log_trade("Buy EUR/USD at 1.1000")
