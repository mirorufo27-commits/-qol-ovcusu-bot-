import pytest
from app.predictor import over25_probability, under25_probability
from app.evaluator import evaluate_match_for_predictions

# 1) Probabilities consistency test: over + under ≈ 1
def test_over_under_sum_consistency():
    lam_home = 1.2
    lam_away = 0.6
    over = over25_probability(lam_home, lam_away)
    under = under25_probability(lam_home, lam_away)
    assert over is not None and under is not None
    # allow tiny numerical tolerance
    assert abs((over + under) - 1.0) < 1e-6

# 2) If under probability is high, over candidate should be False
def test_under_high_prevents_over_candidate():
    # simulate low lambda => under high
    class SR:
        def get_recent_goals_for(self, team_id, limit=8, home_away='all'):
            return [0.5]*8
        def get_recent_goals_against(self, team_id, limit=8, home_away='all'):
            return [0.6]*8
        def get_recent_corners_for(self, *a, **k): return []
        def get_recent_corners_against(self, *a, **k): return []
    sr = SR()
    match = {'home_team_id': 1, 'away_team_id': 2, 'fixture_id': 1}
    cfg = {'thresholds': {'over25_min_prob': 0.6, 'under25_min_prob': 0.6, 'btts_min_prob': 0.75},
           'stats': {'min_matches_required': 6, 'recent_matches_count': 8},
           'model': {}}
    res = evaluate_match_for_predictions(match, sr, league_avg=1.35, config=cfg)
    assert res['status'] == 'ok'
    assert res['under25_prob'] is not None and res['under25_prob'] >= 0.6
    assert res['over25_candidate'] is False

# 3) If over prob is high, under candidate should be False
def test_over_high_selects_over_candidate():
    class SR:
        def get_recent_goals_for(self, team_id, limit=8, home_away='all'):
            return [2.6]*8 if team_id == 1 else [2.4]*8
        def get_recent_goals_against(self, team_id, limit=8, home_away='all'):
            return [1.0]*8
        def get_recent_corners_for(self, *a, **k): return []
        def get_recent_corners_against(self, *a, **k): return []
    sr = SR()
    match = {'home_team_id': 1, 'away_team_id': 2, 'fixture_id': 2}
    cfg = {'thresholds': {'over25_min_prob': 0.6, 'under25_min_prob': 0.6, 'btts_min_prob': 0.6},
           'stats': {'min_matches_required': 6, 'recent_matches_count': 8},
           'model': {}}
    res = evaluate_match_for_predictions(match, sr, league_avg=1.35, config=cfg)
    assert res['status'] == 'ok'
    assert res['over25_prob'] is not None and res['over25_prob'] >= 0.6
    assert res['under25_candidate'] is False
