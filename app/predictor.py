
import math
from typing import List, Optional, Dict


def weighted_mean(
    values: List[float],
    half_life: int = 5
) -> Optional[float]:
    if not values:
        return None

    half_life = max(1, half_life)
    weighted_sum = 0.0
    total_weight = 0.0

    for age, value in enumerate(reversed(values)):
        weight = 0.5 ** (age / half_life)
        weighted_sum += float(value) * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight else None


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0 or lam < 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def over25_probability(
    lambda_home: Optional[float],
    lambda_away: Optional[float]
) -> Optional[float]:
    if lambda_home is None or lambda_away is None:
        return None

    total = max(0.0, lambda_home) + max(0.0, lambda_away)
    probability = 1.0 - sum(poisson_pmf(k, total) for k in range(3))
    return max(0.0, min(1.0, probability))


def under25_probability(
    lambda_home: Optional[float],
    lambda_away: Optional[float]
) -> Optional[float]:
    if lambda_home is None or lambda_away is None:
        return None

    total = max(0.0, lambda_home) + max(0.0, lambda_away)
    probability = sum(poisson_pmf(k, total) for k in range(3))
    return max(0.0, min(1.0, probability))


def btts_probability(
    lambda_home: Optional[float],
    lambda_away: Optional[float]
) -> Optional[float]:
    if lambda_home is None or lambda_away is None:
        return None

    home_scores = 1.0 - math.exp(-max(0.0, lambda_home))
    away_scores = 1.0 - math.exp(-max(0.0, lambda_away))
    return max(0.0, min(1.0, home_scores * away_scores))


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
    if not team_gf_recent or not opponent_ga_recent:
        return None

    if (
        len(team_gf_recent) < min_matches_required
        or len(opponent_ga_recent) < min_matches_required
    ):
        return None

    team_attack = weighted_mean(team_gf_recent, half_life)
    opponent_defence = weighted_mean(opponent_ga_recent, half_life)

    if team_attack is None or opponent_defence is None:
        return None

    # Combine the team's scoring form with the opponent's goals conceded.
    lam = (team_attack + opponent_defence) / 2.0

    if opponent_gf_recent:
        opponent_attack = weighted_mean(opponent_gf_recent, half_life)
        if opponent_attack is not None:
            lam = 0.8 * lam + 0.2 * opponent_attack

    if team_ga_recent:
        team_defence = weighted_mean(team_ga_recent, half_life)
        if team_defence is not None:
            lam = 0.8 * lam + 0.2 * team_defence

    if home:
        lam += home_advantage

    # Use league average only when it represents a per-team goal average.
    if league_avg is not None and league_avg > 0:
        lam *= league_avg / 1.35

    return max(0.01, min(5.0, lam))


def estimate_over_2_5(
    lambda_home,
    lambda_away,
    sample_size=None
):
    if sample_size is not None and sample_size < 6:
        return None
    return over25_probability(lambda_home, lambda_away)


def estimate_btts(
    lambda_home,
    lambda_away,
    sample_size=None
):
    if sample_size is not None and sample_size < 6:
        return None
    return btts_probability(lambda_home, lambda_away)


# Corner predictions are disabled.
# Keep these functions temporarily so older imports do not crash.
def expected_corner_lambda(*args, **kwargs):
    return None


def corner_over_probability(*args, **kwargs):
    return None


def team_corner_probability(*args, **kwargs):
    return None
    
