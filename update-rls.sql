-- RLSポリシーを認証ユーザー限定に変更
-- Supabase SQL Editor で実行

-- 既存ポリシー削除
DROP POLICY IF EXISTS "anon_all" ON weight_log;
DROP POLICY IF EXISTS "anon_all" ON meals;
DROP POLICY IF EXISTS "anon_all" ON workouts;
DROP POLICY IF EXISTS "anon_all" ON supplement_log;
DROP POLICY IF EXISTS "anon_all" ON water_log;
DROP POLICY IF EXISTS "anon_all" ON fasting_log;
DROP POLICY IF EXISTS "anon_all" ON events;
DROP POLICY IF EXISTS "anon_all" ON shopping_list;
DROP POLICY IF EXISTS "anon_all" ON tasks;

-- 認証済みユーザーのみアクセス可能
CREATE POLICY "auth_only" ON weight_log FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON meals FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON workouts FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON supplement_log FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON water_log FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON fasting_log FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON events FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON shopping_list FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "auth_only" ON tasks FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
