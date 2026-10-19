import json
from datetime import datetime
from typing import Optional

from .predictor import expected_goal_lambda, over25_probability, btts_probability

STATUS_WAITING = 'Gözləmədə'
STATUS_CORRECT = 'Düzgün'
STATUS_WRONG = 'Səhv'
STATUS_CANCELLED = 'Ləğv edilib'
STATUS_NODATA = 'Məlumat çatışmır'


def evaluate_prediction(prediction, match_result):
    """
    Keep existing evaluation logic for settled matches.
    """
    market = prediction.get('market')
    try:
        if not match_result or match_result.get('status') in ['postponed', 'cancelled', 'abandoned']:
            return STATUS_CANCELLED
    except Exception:
        return STATUS_NODATA

    stats = match_result.get('stats') or {}
    fts = match_result.get('full_time_score')
    if fts:
        try:
            parts = fts.split('-')
            home_goals = int(parts[0])
            away_goals = int(parts[1])
        except Exception:
            return STATUS_NODATA
    else:
        return STATUS_NODATA

    total_goals = home_goals + away_goals

    if market == 'over_2_5':
        return STATUS_CORRECT if total_goals >= 3 else STATUS_WRONG
    if market == 'under_2_5':
        return STATUS_CORRECT if total_goals <= 2 else STATUS_WRONG
    if market == 'btts':
        return STATUS_CORRECT if home_goals >= 1 and away_goals >= 1 else STATUS_WRONG
    if market == 'btts_no':
        return STATUS_CORRECT if not (home_goals >= 1 and away_goals >= 1) else STATUS_WRONG

    # corners and team corners
    if market == 'first_half_over_4_5_corners':
        fh = stats.get('first_half') or {}
        corners = fh.get('corners')
        if corners is None:
            return STATUS_NODATA
        return STATUS_CORRECT if corners >= 5 else STATUS_WRONG
    if market == 'full_over_9_5_corners':
        corners = stats.get('corners')
        if corners is None:
            return STATUS_NODATA
        return STATUS_CORRECT if corners >= 10 else STATUS_WRONG
    if market == 'full_over_10_5_corners':
        corners = stats.get('corners')
        if corners is None:
            return STATUS_NODATA
        return STATUS_CORRECT if corners >= 11 else STATUS_WRONG
    if market == 'team_corners':
        sel = prediction.get('selection')
        try:
            side, val = sel.split(':')
            val = int(val)
            actual = stats.get('corners_home') if side == 'home' else stats.get('corners_away')
            if actual is None:
                return STATUS_NODATA
            return STATUS_CORRECT if actual == val else STATUS_WRONG
        except Exception:
            return STATUS_NODATA

    # next goal candidate and live added goal retain original behavior
    if market == 'next_goal_candidate':
        events = match_result.get('events') or []
        created_at = prediction.get('created_at')
        if not created_at:
            return STATUS_NODATA
        created_ts = datetime.fromisoformat(created_at)
        for ev in events:
            if ev.get('type') == 'goal':
                ev_ts = datetime.fromisoformat(ev.get('timestamp'))
                if ev_ts > created_ts:
                    return STATUS_CORRECT if ev.get('team') == prediction.get('selection') else STATUS_WRONG
        return STATUS_WRONG

    if market == 'live_added_goal':
        created_at = prediction.get('created_at')
        if not created_at:
            return STATUS_NODATA
        created_ts = datetime.fromisoformat(created_at)
        events = match_result.get('events') or []
        for ev in events:
            if ev.get('type') == 'goal' and datetime.fromisoformat(ev.get('timestamp')) > created_ts:
                return STATUS_CORRECT
        return STATUS_WRONG

    return STATUS_NODATA


# New: evaluate a scheduled match using recent stats and Poisson model
def evaluate_match_for_predictions(match: dict, stats_repo, league_avg: Optional[float], config: dict) -> dict:
    """
    match: dict with keys home_team_id, away_team_id, league, kickoff, fixture_id (match id)
    stats_repo: StatsRepo instance
    league_avg: float average goals per team in league (fallback to 1.35)
    config: config dict with thresholds and stats params
    Returns dict with probabilities and candidate flags or status 'insufficient_data'.
    """
    min_matches = config.get('stats', {}).get('min_matches_required', 6)
    recent_count = config.get('stats', {}).get('recent_matches_count', 8)
    half_life = config.get('stats', {}).get('decay_half_life_matches', 5)

    home_id = match.get('home_team_id')
    away_id = match.get('away_team_id')
    if not home_id or not away_id:
        return {'status': 'insufficient_data'}

    # fetch recent goals; home_away param ensures we use home/away contexts if available
    home_gf = stats_repo.get_recent_goals_for(home_id, limit=recent_count, home_away='home')
    home_ga = stats_repo.get_recent_goals_against(home_id, limit=recent_count, home_away='home')
    away_gf = stats_repo.get_recent_goals_for(away_id, limit=recent_count, home_away='away')
    away_ga = stats_repo.get_recent_goals_against(away_id, limit=recent_count, home_away='away')

    if len(home_gf) < min_matches or len(away_gf) < min_matches or len(home_ga) < min_matches or len(away_ga) < min_matches:
        return {'status': 'insufficient_data'}

    lam_home = expected_goal_lambda(home_gf, away_ga, league_avg=league_avg or 1.35, half_life=half_life)
    lam_away = expected_goal_lambda(away_gf, home_ga, league_avg=league_avg or 1.35, half_life=half_life)

    if lam_home is None or lam_away is None:
        return {'status': 'insufficient_data'}

    over_prob = over25_probability(lam_home, lam_away)
btts_prob = btts_probability(lam_home, lam_away)

    # apply thresholds from config
    over_thresh = config.get('thresholds', {}).get('over25_min_prob', 0.7)
    btts_thresh = config.get('thresholds', {}).get('btts_min_prob', 0.75)

        over_prob = over25_probability(lam_home, lam_away)
    under_prob = under25_probability(lam_home, lam_away)
    btts_prob = btts_probability(lam_home, lam_away)

    over_thresh = config.get('thresholds', {}).get('over25_min_prob', 0.7)
    under_thresh = config.get('thresholds', {}).get('under25_min_prob', 0.7)
    btts_thresh = config.get('thresholds', {}).get('btts_min_prob', 0.75)

    return {
        'status': 'ok',
        'over25_prob': round(over_prob, 3) if over_prob is not None else None,
        'under25_prob': round(under_prob, 3) if under_prob is not None else None,
        'btts_prob': round(btts_prob, 3) if btts_prob is not None else None,
        'over25_candidate': over_prob is not None and over_prob >= over_thresh,
        'under25_candidate': under_prob is not None and under_prob >= under_thresh,
        'btts_candidate': btts_prob is not None and btts_prob >= btts_thresh,
        'lambda_home': round(lam_home, 3),
        'lambda_away': round(lam_away, 3)
    }
