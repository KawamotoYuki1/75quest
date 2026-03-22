-- 75Quest Database Setup
-- Supabase SQL Editor に貼り付けて「Run」

-- ==============================
-- 1. 体重ログ
-- ==============================
CREATE TABLE weight_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  weight DECIMAL(5,1) NOT NULL,
  body_fat DECIMAL(4,1),
  memo TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 2. 食事記録
-- ==============================
CREATE TABLE meals (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast','lunch','dinner','snack')),
  description TEXT NOT NULL,
  calories INT,
  protein DECIMAL(5,1),
  fat DECIMAL(5,1),
  carbs DECIMAL(5,1),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 3. トレーニング記録
-- ==============================
CREATE TABLE workouts (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  menu_name TEXT NOT NULL,
  exercises JSONB NOT NULL DEFAULT '[]',
  completed BOOLEAN DEFAULT FALSE,
  duration_min INT,
  memo TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 4. サプリチェック
-- ==============================
CREATE TABLE supplement_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  supplement_name TEXT NOT NULL,
  taken BOOLEAN DEFAULT FALSE,
  amount TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 5. 水分摂取
-- ==============================
CREATE TABLE water_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  amount_ml INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 6. 断食記録
-- ==============================
CREATE TABLE fasting_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  is_fasting_day BOOLEAN DEFAULT FALSE,
  fast_start TIMESTAMPTZ,
  fast_end TIMESTAMPTZ,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 7. イベント
-- ==============================
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT DEFAULT '📋',
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  description TEXT,
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 8. 買い物リスト
-- ==============================
CREATE TABLE shopping_list (
  id BIGSERIAL PRIMARY KEY,
  item_name TEXT NOT NULL,
  url TEXT,
  purchased BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- 9. タスク（LINE連携用）
-- ==============================
CREATE TABLE tasks (
  id BIGSERIAL PRIMARY KEY,
  text TEXT NOT NULL,
  category TEXT DEFAULT 'タスク',
  done BOOLEAN DEFAULT FALSE,
  due_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================
-- RLS（Row Level Security）有効化
-- ==============================
ALTER TABLE weight_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplement_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE fasting_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- ==============================
-- RLS ポリシー: anon keyで全操作OK（個人利用のため）
-- service_role keyがなくても使えるように
-- ==============================
CREATE POLICY "anon_all" ON weight_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON meals FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON workouts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON supplement_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON water_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON fasting_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON shopping_list FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON tasks FOR ALL USING (true) WITH CHECK (true);

-- ==============================
-- 初期データ: イベント
-- ==============================
INSERT INTO events (name, icon, start_date, end_date, description) VALUES
  ('塩抜き3日間', '🧂', '2026-03-30', '2026-04-01', 'むくみ解消 -1〜2kg'),
  ('24時間ファスティング', '🍵', '2026-04-06', '2026-04-06', '夕食→翌夕食 水・お茶のみ'),
  ('プロテイン置き換えWeek', '🥤', '2026-04-14', '2026-04-18', '夕食→EZOBOLIC'),
  ('塩抜き3日間', '🧂', '2026-04-27', '2026-04-29', 'むくみ解消'),
  ('48時間ファスティング', '🔥', '2026-05-05', '2026-05-06', 'GW中チャレンジ'),
  ('5:2ダイエットWeek', '🔄', '2026-05-18', '2026-05-24', '週5普通+2日500kcal');

-- ==============================
-- 初期データ: 買い物リスト
-- ==============================
INSERT INTO shopping_list (item_name, url) VALUES
  ('EZOBOLIC プロテイン', 'https://www.amazon.co.jp/s?k=EZOBOLIC+プロテイン'),
  ('クレアチン', 'https://www.amazon.co.jp/s?k=クレアチン+モノハイドレート'),
  ('難消化性デキストリン', 'https://www.amazon.co.jp/s?k=難消化性デキストリン'),
  ('防風通聖散', NULL),
  ('ヨガマット', 'https://www.amazon.co.jp/s?k=ヨガマット+トレーニング'),
  ('可変式ダンベル 20kg×2', 'https://www.amazon.co.jp/s?k=可変式ダンベル+20kg');
