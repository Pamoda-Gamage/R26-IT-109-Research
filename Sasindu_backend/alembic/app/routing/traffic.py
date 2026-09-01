TIME_SLOTS = ["early_morning", "morning_peak", "midday", "evening_peak", "night"]

_MULTIPLIERS = {
    "early_morning": 1.0,
    "morning_peak": 1.8,
    "midday": 1.2,
    "evening_peak": 2.0,
    "night": 0.9,
}


def traffic_multiplier(time_slot: str) -> float:
    if time_slot not in _MULTIPLIERS:
        raise ValueError(f"unknown time_slot: {time_slot!r}, expected one of {TIME_SLOTS}")
    return _MULTIPLIERS[time_slot]
