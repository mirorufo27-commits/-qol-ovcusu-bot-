from app.predictor import estimate_over_2_5, estimate_btts

def test_estimate_over_2_5_insufficient():
    assert estimate_over_2_5(0.8,0.7,2) is None

def test_estimate_btts_insufficient():
    assert estimate_btts(0.6,0.5,3) is None


from app.predictor import match_result_probabilities


def test_match_result_probabilities_sum_to_one():
    result = match_result_probabilities(1.8, 0.9)
    assert result is not None
    assert abs(sum(result.values()) - 1.0) < 1e-9


def test_match_result_favors_stronger_home_team():
    result = match_result_probabilities(1.8, 0.9)
    assert result is not None
    assert result["home_win"] > result["away_win"]


def test_match_result_equal_rates_have_equal_win_probabilities():
    result = match_result_probabilities(1.2, 1.2)
    assert result is not None
    assert abs(result["home_win"] - result["away_win"]) < 1e-9


def test_match_result_rejects_missing_or_negative_rates():
    assert match_result_probabilities(None, 1.0) is None
    assert match_result_probabilities(1.0, None) is None
    assert match_result_probabilities(-0.5, 1.0) is None
