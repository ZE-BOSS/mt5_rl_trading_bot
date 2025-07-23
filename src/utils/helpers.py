def calculate_risk_percentage(account_balance, risk_per_trade):
    return account_balance * (risk_per_trade / 100)

def calculate_lot_size(account_balance, stop_loss_pips, risk_percentage):
    lot_size = risk_percentage / stop_loss_pips
    return min(lot_size, account_balance)  # Ensure lot size does not exceed account balance

def format_trade_journal_entry(date, pair, or_high, or_low, sr_level, pattern, entry, sl, tp1, tp2, outcome, lesson):
    return f"""[Trade Journal Entry]
Date: {date}
Pair: {pair}
OR High/Low: {or_high} / {or_low}
S/R Level: {sr_level}
Pattern: {pattern}
Entry: {entry}
SL: {sl}
TP1: {tp1}
TP2: {tp2}
Outcome: {outcome}
Lesson: {lesson}
"""

def is_trade_time(current_time, trading_hours):
    for start, end in trading_hours:
        if start <= current_time <= end:
            return True
    return False

def round_to_nearest(value, nearest):
    return round(value / nearest) * nearest