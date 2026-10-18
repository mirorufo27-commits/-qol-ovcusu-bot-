import math
from typing import List, Optional, Dict

# --- Goal-based helpers (Poisson) ---
def weighted_mean(values: List[float], half_life: int = 5) -> Optional[float]:
    if not values:
        return None
    weighted_sum = 0.0
    total_weight = 0.0
    # newest values last in list
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

# --- Enhanced expected goal lambda (use opponent strength, home advantage, league scaling) ---
def expected_goal_lambda(
    team_gf_recent: List[float],
    opponent_ga_recent: List[float],
    opponent_gf_recent: Optional[List[float]] = None,
    team_ga_recent: Optional[List[float]] = None,
    league_avg: Optional[float] = None,
    half_life: int = 5,
    weights: Optional[Dict[str, float]] = None,
    home: bool = False,
    home_advantage: float = 0.12,
    min_matches_required: int = 6
) -> Optional[float]:
    """
    Compute expected goal lambda for a team using:
      - team's GF recent (home/away split as provided)
      - opponent's GA recent (home/away split as provided)
      - optional opponent GF recent and team's GA recent for additional context
    Weights (defaults) apply more weight to team's own scoring.
    If data insufficient (len < min_matches_required) return None.
    """
    weights = weights or {'alpha': 0.6, 'beta': 0.25, 'gamma': 0.1, 'delta': 0.05}
    if not team_gf_recent or not opponent_ga_recent:
        return None
    # Ensure sample size requirement
    if len(team_gf_recent) < min_matches_required or len(opponent_ga_recent) < min_matches_required:
        return None

    t = weighted_mean(team_gf_recent, half_life)
    o = weighted_mean(opponent_ga_recent, half_life)
    opp = weighted_mean(opponent_gf_recent, half_life) if opponent_gf_recent else None
    tg = weighted_mean(team_ga_recent, half_life) if team_ga_recent else None

    if t is None or o is None:
        return None

    alpha = weights.get('alpha', 0.6)
    beta = weights.get('beta', 0.25)
    gamma = weights.get('gamma', 0.1)
    delta = weights.get('delta', 0.05)

    lam = alpha * t + beta * o
    if opp is not None:
        lam += gamma * opp
    if tg is not None:
        lam += delta * tg

    if home:
        lam += home_advantage

    # scale by league average (protect against None)
    if league_avg is not None and league_avg > 0:
        try:
            lam *= (league_avg / 1.35)
        except Exception:
            pass

    return max(0.01, lam)

# --- Corner-specific functions (unchanged logic; never inferred from goals) ---
def expected_corner_lambda(team_corners_recent: List[float], opponent_corners_against_recent: List[float], half_life: int = 5) -> Optional[float]:
    """
    Estimate expected corners (lambda) for a team using recent corners-for and opponent corners-against.
    Requires real corner history (first-half or full-match depending on caller).
    """
    t = weighted_mean(team_corners_recent, half_life)
    o = weighted_mean(opponent_corners_against_recent, half_life)
    if t is None or o is None:
        return None
    lam = (t + o) / 2.0
    return max(0.01, lam)


def corner_over_probability(lambda_home_corners: Optional[float], lambda_away_corners: Optional[float], threshold: int, sample_size_home: int = 0, sample_size_away: int = 0, min_sample: int = 6) -> Optional[float]:
    """
    Probability total corners >= threshold using Poisson on total lambda.
    Additional safety: if sample sizes less than min_sample, return None (insufficient data).
    """
    if lambda_home_corners is None or lambda_away_corners is None:
        return None
    if sample_size_home < min_sample or sample_size_away < min_sample:
        return None
    lambda_total = lambda_home_corners + lambda_away_corners
    cdf = 0.0
    for k in range(0, threshold):
        cdf += poisson_pmf(k, lambda_total)
    prob = 1.0 - cdf
    return max(0.0, min(1.0, prob))


def team_corner_probability(lambda_team: Optional[float]) -> Optional[float]:
    if lambda_team is None:
        return None
    p = 1.0 - math.exp(-lambda_team)
    return max(0.0, min(1.0, p))
