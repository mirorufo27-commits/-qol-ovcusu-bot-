import math

def safe_prob(p):
    # clamp and avoid 0/1 extremes
    if p is None:
        return None
    p = max(0.01, min(0.99, p))
    return p

def estimate_over_2_5(home_goals_avg, away_goals_avg, sample_size):
    # simple heuristic: mean total goals = home_avg + away_avg
    if sample_size < 5:
        return None  # insufficient data
    mean = home_goals_avg + away_goals_avg
    # map mean to probability via logistic-like mapping
    p = 1 / (1 + math.exp(1.5 - mean))
    return safe_prob(p)

def estimate_btts(home_btts_rate, away_btts_rate, sample_size):
    if sample_size < 5:
        return None
    # combine rates with Laplace smoothing
    p = (home_btts_rate + away_btts_rate) / 2
    return safe_prob(p)

# Additional simple estimators can be added similarly
