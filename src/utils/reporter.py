from datetime import datetime
import pandas as pd
import os

class Reporter:
    def __init__(self, journal_dir):
        self.journal_dir = journal_dir
        self.performance_data = []

    def log_trade(self, trade_entry):
        self.performance_data.append(trade_entry)
        self._save_trade_entry(trade_entry)

    def _save_trade_entry(self, trade_entry):
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(self.journal_dir, f"{date_str}_trades.csv")
        
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as f:
                f.write("Date,Pair,OR High,OR Low,S/R Level,Pattern,Entry,SL,TP1,TP2,Outcome,Lesson\n")
        
        with open(file_path, 'a') as f:
            f.write(f"{trade_entry['date']},{trade_entry['pair']},{trade_entry['or_high']},"
                     f"{trade_entry['or_low']},{trade_entry['sr_level']},{trade_entry['pattern']},"
                     f"{trade_entry['entry']},{trade_entry['sl']},{trade_entry['tp1']},"
                     f"{trade_entry['tp2']},{trade_entry['outcome']},{trade_entry['lesson']}\n")

    def generate_performance_report(self):
        report_df = pd.DataFrame(self.performance_data)
        report_summary = {
            'Total Trades': len(report_df),
            'Wins': len(report_df[report_df['outcome'] == 'Win']),
            'Losses': len(report_df[report_df['outcome'] == 'Loss']),
            'Win Rate': len(report_df[report_df['outcome'] == 'Win']) / len(report_df) * 100 if len(report_df) > 0 else 0,
            'Average Return': report_df['return'].mean() if 'return' in report_df else 0
        }
        return report_summary

    def save_summary_to_file(self, summary, filename='performance_summary.txt'):
        with open(os.path.join(self.journal_dir, filename), 'w') as f:
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")