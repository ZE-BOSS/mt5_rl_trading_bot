import logging
import os

class Logger:
    def __init__(self, log_file='trading_bot.log'):
        self.logger = logging.getLogger('TradingBotLogger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create a file handler
        file_handler = logging.FileHandler(os.path.join('journals', log_file))
        file_handler.setLevel(logging.DEBUG)
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create a formatter and set it for both handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, message):
        self.logger.info(message)

    def log_trade(self, trade_entry):
        self.logger.info(f'Trade Entry: {trade_entry}')

    def log_exit(self, trade_exit):
        self.logger.info(f'Trade Exit: {trade_exit}')

    def log_confluence(self, confluence_info):
        self.logger.debug(f'Confluence Detected: {confluence_info}')

    def log_error(self, error_message):
        self.logger.error(f'Error: {error_message}')

    def log_performance(self, performance_metrics):
        self.logger.info(f'Performance Metrics: {performance_metrics}')

# Example usage:
# logger = Logger()
# logger.log_trade("Buy EUR/USD at 1.1000")