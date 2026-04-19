import math

def calculate_time_left(quarter, minutes, seconds):
    """
    A standard NBA game is 48 minutes (2880 seconds).
    Calculate total seconds remaining (t).
    Caps t at 2880 max, and 0 min. Ignores overtime logic.
    """
    t = ((4 - quarter) * 720) + (minutes * 60) + seconds
    return max(0, min(t, 2880))

def calculate_deterministic_score(historical_results):
    """
    historical_results is a list of 1s (home win) and 0s (home loss).
    index 0 is the most recent game, index 4 is the oldest game.
    """
    if not historical_results:
        return 0.5
    
    numerator = 0.0
    denominator = 0.0
    for idx, result in enumerate(historical_results):
        i = idx + 1 # i=1 is most recent, i=5 is oldest
        weight = math.exp(-i)
        numerator += weight * result
        denominator += weight
        
    if denominator == 0:
        return 0.5
    return numerator / denominator

def calculate_pcw(time_left_seconds):
    """
    Prediction Contribution Weight (PCW).
    Weight of deterministic score decays linearly as time ticks down from 2880 to 0.
    """
    return time_left_seconds / 2880.0

def calculate_final_score(pcw, det_home, pbp_home):
    """
    Blends the Deterministic and Probabilistic scores.
    """
    final_home = (pcw * det_home) + ((1.0 - pcw) * pbp_home)
    final_away = 1.0 - final_home
    return final_home, final_away
