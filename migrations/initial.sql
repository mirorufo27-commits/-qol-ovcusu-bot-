-- Initial schema for Qol Ovçusu

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS predictions (
  id TEXT PRIMARY KEY,
  match_id TEXT NOT NULL,
  league TEXT,
  home_team TEXT,
  away_team TEXT,
  kickoff TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  prediction_type TEXT, -- 'pre' or 'live'
  live_minute INTEGER,
  live_score TEXT,
  market TEXT,
  selection TEXT,
  probability REAL,
  model_version TEXT,
  supporting_stats TEXT,
  status TEXT DEFAULT 'Gözləmədə',
  evaluated_at TIMESTAMP,
  result_notified INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS match_results (
  match_id TEXT PRIMARY KEY,
  league TEXT,
  home_team TEXT,
  away_team TEXT,
  kickoff TIMESTAMP,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status TEXT,
  full_time_score TEXT,
  halftime_score TEXT,
  stats TEXT
);

CREATE TABLE IF NOT EXISTS prediction_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prediction_id TEXT,
  action TEXT,
  payload TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
