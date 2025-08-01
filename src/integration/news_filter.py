import os
import requests
from datetime import datetime, timedelta

class NewsFilter:
    def __init__(self, symbols, impact_levels=['high', 'medium']):
        self.symbols = symbols
        self.impact_levels = impact_levels
        self.currency_map = {
            'EURUSD': ['EUR', 'USD'],
            'GBPUSD': ['GBP', 'USD'],
            'XAUUSD': ['XAU', 'USD'],
            'GER40': ['EUR'],
            'UK100': ['GBP']
        }
        
        self.api_key = os.getenv('ECONOMIC_CALENDAR_API_KEY')
        self.events = self.fetch_economic_events()

    def fetch_economic_events(self, hours_ahead=12):
        if not self.api_key:
            return []
            
        now = datetime.utcnow()
        end = now + timedelta(hours=hours_ahead)
        url = "https://economic-calendar-api.com/events"
        params = {
            'start': now.isoformat(),
            'end': end.isoformat(),
            'importance': ','.join(self.impact_levels),
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=3)
            return response.json().get('events', [])
        except:
            return []

    def is_high_impact_event(self, symbol):
        if not self.events:
            return False
            
        current_time = datetime.utcnow()
        for event in self.events:
            # Check currency match
            currency = event.get('currency', '')
            if currency not in self.currency_map.get(symbol, []):
                continue
                
            # Check time window
            event_time = datetime.fromisoformat(event['date'].replace('Z', ''))
            window_start = event_time - timedelta(minutes=15)
            window_end = event_time + timedelta(minutes=30)
            
            if window_start <= current_time <= window_end:
                return True
                
        return False