PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  region_code TEXT,
  reminder_enabled INTEGER DEFAULT 0,
  reminder_offset INTEGER DEFAULT 10,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Kunlik cache (region + date bo'yicha)
CREATE TABLE IF NOT EXISTS cache_daily (
  region_api TEXT NOT NULL,
  date TEXT NOT NULL, -- YYYY-MM-DD
  suhoor TEXT NOT NULL,
  iftar TEXT NOT NULL,
  raw_json TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (region_api, date)
);

-- Oylik cache (region + year-month bo'yicha)
CREATE TABLE IF NOT EXISTS cache_monthly (
  region_api TEXT NOT NULL,
  ym TEXT NOT NULL, -- YYYY-MM
  raw_json TEXT NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (region_api, ym)
);
