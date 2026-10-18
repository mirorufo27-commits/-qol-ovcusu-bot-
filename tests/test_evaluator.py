import pytest
from app.evaluator import evaluate_prediction

# Synthetic test data for acceptance tests

def test_over_2_5_three_goals():
    pred = {'market':'over_2_5'}
    match = {'full_time_score':'2-1','status':'finished','stats':{}}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_under_2_5_two_goals():
    pred = {'market':'under_2_5'}
    match = {'full_time_score':'1-1','status':'finished','stats':{}}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_btts_both_scored():
    pred = {'market':'btts'}
    match = {'full_time_score':'2-1','status':'finished','stats':{}}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_first_half_4_5_corners():
    pred = {'market':'first_half_over_4_5_corners'}
    match = {'full_time_score':'1-0','status':'finished','stats':{'first_half':{'corners':5}}}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_full_over_10_5_corners():
    pred = {'market':'full_over_10_5_corners'}
    match = {'full_time_score':'3-2','status':'finished','stats':{'corners':11}}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_live_prediction_only_after_timestamp():
    pred = {'market':'next_goal_candidate','selection':'home','created_at':'2023-01-01T12:00:00'}
    match = {'status':'finished','events':[{'type':'goal','team':'away','timestamp':'2023-01-01T11:59:00'},{'type':'goal','team':'home','timestamp':'2023-01-01T12:05:00'}], 'full_time_score':'2-1'}
    assert evaluate_prediction(pred, match) == 'Düzgün'

def test_missing_statistics_not_marked_wrong():
    pred = {'market':'first_half_over_4_5_corners'}
    match = {'status':'finished','full_time_score':'1-0','stats':{}}
    assert evaluate_prediction(pred, match) == 'Məlumat çatışmır'

def test_postponed_not_marked_wrong():
    pred = {'market':'over_2_5'}
    match = {'status':'postponed'}
    assert evaluate_prediction(pred, match) == 'Ləğv edilib'
