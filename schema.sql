-- ================================================================
-- Japanese Hub · Supabase schema
-- Cole no SQL Editor: https://supabase.com/dashboard/project/zhrfhmhhdebcphsqghai/sql
-- ================================================================

-- Vocabulário (L1–7)
CREATE TABLE IF NOT EXISTS vocabulary (
  id        BIGSERIAL PRIMARY KEY,
  kanji     TEXT,
  kana      TEXT,
  portuguese TEXT NOT NULL,
  lesson    SMALLINT NOT NULL,
  category  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vocab_lesson   ON vocabulary(lesson);
CREATE INDEX IF NOT EXISTS idx_vocab_category ON vocabulary(category);

-- Partículas
CREATE TABLE IF NOT EXISTS particles (
  id          BIGSERIAL PRIMARY KEY,
  particle    TEXT NOT NULL,
  romaji      TEXT NOT NULL,
  lesson      SMALLINT NOT NULL,
  role        TEXT NOT NULL,
  description TEXT NOT NULL,
  example_jp  TEXT,
  example_kana TEXT,
  example_pt  TEXT
);
CREATE INDEX IF NOT EXISTS idx_parts_lesson ON particles(lesson);

-- Progresso SRS por dispositivo (anônimo)
CREATE TABLE IF NOT EXISTS user_progress (
  id         BIGSERIAL PRIMARY KEY,
  device_id  TEXT NOT NULL,
  word_id    BIGINT NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
  rating     TEXT NOT NULL CHECK (rating IN ('hard','med','easy')),
  ease       NUMERIC(5,2) NOT NULL DEFAULT 2.5,
  interval   INTEGER NOT NULL DEFAULT 0,
  reps       INTEGER NOT NULL DEFAULT 0,
  due        BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(device_id, word_id)
);
CREATE INDEX IF NOT EXISTS idx_prog_device ON user_progress(device_id);
CREATE INDEX IF NOT EXISTS idx_prog_due    ON user_progress(device_id, due);

-- Row Level Security
ALTER TABLE vocabulary    ENABLE ROW LEVEL SECURITY;
ALTER TABLE particles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;

-- vocabulary e particles: leitura pública
CREATE POLICY "anon read vocab"  ON vocabulary    FOR SELECT USING (true);
CREATE POLICY "anon read parts"  ON particles     FOR SELECT USING (true);

-- user_progress: qualquer operação (acesso anônimo por device_id)
CREATE POLICY "anon all progress" ON user_progress FOR ALL USING (true) WITH CHECK (true);
