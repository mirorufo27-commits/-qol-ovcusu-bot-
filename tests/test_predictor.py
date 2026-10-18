from app.predictor import estimate_over_2_5, estimate_btts

def test_estimate_over_2_5_insufficient():
    assert estimate_over_2_5(0.8,0.7,2) is None

def test_estimate_btts_insufficient():
    assert estimate_btts(0.6,0.5,3) is None
