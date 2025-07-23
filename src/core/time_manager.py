from datetime import datetime, time

class TimeManager:
    def __init__(self, schedule):
        self.schedule = schedule
        self.trading_days = set(schedule.get('trading_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']))
        self.start_time = self._parse_time(schedule.get('start_time', '07:00'))
        self.end_time = self._parse_time(schedule.get('end_time', '17:00'))
        self.avoid_times = [self._parse_time_range(t) for t in schedule.get('avoid_times', [])]
    def _parse_time(self, tstr):
        h, m = map(int, tstr.split(':'))
        return time(h, m)

    def _parse_time_range(self, rstr):
        # Handles '12:00-13:30' or 'Friday 12:00-23:59'
        parts = rstr.split()
        if len(parts) == 2:
            day, times = parts
        else:
            day, times = None, parts[0]
        start, end = times.split('-')
        return (day, self._parse_time(start), self._parse_time(end))

    def is_trading_time(self, current_dt):
        # current_dt: datetime.datetime
        day_name = current_dt.strftime('%A')
        now_time = current_dt.time()
        # Check trading day
        if day_name not in self.trading_days:
            return False
        # Check avoid times
        for avoid in self.avoid_times:
            avoid_day, avoid_start, avoid_end = avoid
            if (avoid_day is None or avoid_day == day_name) and avoid_start <= now_time <= avoid_end:
                return False
        # Check trading window
        if not (self.start_time <= now_time <= self.end_time):
            return False
        return True
