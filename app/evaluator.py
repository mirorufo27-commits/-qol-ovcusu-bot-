import json
from datetime import datetime

STATUS_WAITING = 'Gözləmədə'
STATUS_CORRECT = 'Düzgün'
STATUS_WRONG = 'Səhv'
STATUS_CANCELLED = 'Ləğv edilib'
STATUS_NODATA = 'Məlumat çatışmır'


def evaluate_prediction(prediction, match_result):
    """
    prediction: dict-like with keys market, selection, probability, created_at (ISO str), prediction_type ('pre'/'live')
    match_result: dict-like with keys full_time_score (e.g., '2-1'), stats (dict)
    """
    market = prediction.get('market')
    # parse scores
    try:
        if not match_result or match_result.get('status') in ['postponed','cancelled','abandoned']:
            return STATUS_CANCELLED
    except Exception:
        return STATUS_NODATA

    stats = match_result.get('stats') or {}
    # parse full-time score
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
        return STATUS_CORRECT if home_goals >=1 and away_goals >=1 else STATUS_WRONG
    if market == 'btts_no':
        return STATUS_CORRECT if not (home_goals >=1 and away_goals >=1) else STATUS_WRONG
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
        # selection should be 'home:5' or 'away:3' format
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

    # next goal candidate and live additional goal rely on event timelines — we leave as NODATA if not present
    if market == 'next_goal_candidate':
        events = match_result.get('events') or []
        # prediction must include timestamp
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
