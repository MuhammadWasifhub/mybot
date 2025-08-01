# entry_time_calculator.py

from datetime import datetime, timedelta

def get_next_candle_time(current_time: datetime, timeframe_minutes: int) -> str:
    """
    Returns the next candle's opening time based on current time and timeframe.
    """
    # Round current time to nearest minute (no seconds/microseconds)
    rounded_time = current_time.replace(second=0, microsecond=0)
    minute = rounded_time.minute
    remainder = minute % timeframe_minutes
    minutes_to_add = timeframe_minutes - remainder if remainder != 0 else timeframe_minutes
    next_candle_time = rounded_time + timedelta(minutes=minutes_to_add)

    return next_candle_time.strftime("%H:%M")  # Return in 24-hour format like '17:05'