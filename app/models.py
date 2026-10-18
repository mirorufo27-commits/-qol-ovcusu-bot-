from dataclasses import dataclass
from typing import Optional

@dataclass
class Prediction:
    id: str
    match_id: str
    league: Optional[str]
    home_team: Optional[str]
    away_team: Optional[str]
    kickoff: Optional[str]
    created_at: Optional[str]
    prediction_type: str
    live_minute: Optional[int]
    live_score: Optional[str]
    market: str
    selection: str
    probability: float
    model_version: str
    supporting_stats: Optional[dict]
    status: str = 'Gözləmədə'
    evaluated_at: Optional[str] = None
    result_notified: bool = False

@dataclass
class MatchResult:
    match_id: str
    league: Optional[str]
    home_team: Optional[str]
    away_team: Optional[str]
    kickoff: Optional[str]
    fetched_at: Optional[str]
    status: Optional[str]
    full_time_score: Optional[str]
    halftime_score: Optional[str]
    stats: Optional[dict]
