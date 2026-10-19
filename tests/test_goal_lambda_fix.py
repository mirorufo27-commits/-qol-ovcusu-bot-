from app.predictor import expected_goal_lambda, expected_corner_lambda, corner_over_probability


def test_goal_lambda_requires_six_matches():
    assert expected_goal_lambda([1, 2, 1, 0, 2], [1, 1, 0, 2, 1]) is None


def test_goal_lambda_does_not_apply_fake_league_average_scaling():
    result = expected_goal_lambda(
        [2] * 6, [1] * 6, league_avg=3.0
    )
    assert result == 1.5


def test_home_advantage_is_applied_only_when_requested():
    args = ([2] * 6, [1] * 6)
    normal = expected_goal_lambda(*args)
    home = expected_goal_lambda(*args, home=True)
    assert normal == 1.5
    assert round(home, 2) == 1.62


def test_corner_predictions_remain_disabled_without_corner_data():
    assert expected_corner_lambda() is None
    assert corner_over_probability() is None
