import math
from typing import List, Optional

# Weighted mean with exponential decay
def weighted_mean(values: List[float], half_life: int = 5) -> Optional[float]:
    if not values:
        return None
    weighted_sum = 0.0
    total_weight = 0.0
    for age, v in enumerate(reversed(values)):
        weight = 0.5 ** (age / half_life)
        weighted_sum += v * weight
        total_weight += weight
    return weighted_sum / total_weight if total_weight else None


def poisson_pmf(k: int, lam: float) -> float:
    if lam < 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def over25_probability(lambda_home: Optional[float], lambda_away: Optional[float]) -> Optional[float]:
    if lambda_home is None or lambda_away is None:
        return None
    lambda_total = lambda_home + lambda_away
    p0 = poisson_pmf(0, lambda_total)
    p1 = poisson_pmf(1, lambda_total)
    p2 = poisson_pmf(2, lambda_total)
    prob = 1.0 - (p0 + p1 + p2)
    return max(0.0, min(1.0, prob))


def btts_probability(lambda_home: Optional[float], lambda_away: Optional[float]) -> Optional[float]:
    if lambda_home is None or lambda_away is None:
        return None
    p_home_scores = 1.0 - math.exp(-lambda_home)
    p_away_scores = 1.0 - math.exp(-lambda_away)
    prob = p_home_scores * p_away_scores
    return max(0.0, min(1.0, prob))


def expected_goal_lambda(team_gf_recent: List[float], opponent_ga_recent: List[float], league_avg: Optional[float] = None, half_life: int = 5) -> Optional[float]:
    t = weighted_mean(team_gf_recent, half_life)
    o = weighted_mean(opponent_ga_recent, half_life)
    if t is None or o is None:
        return None
    lam = (t + o) / 2.0
    if league_avg:
        try:
            lam *= (league_avg / 1.35)
        except Exception:
            pass
    return max(0.01, lam)
