# 75Quest — かわちのボディメイクプロジェクト

93kg → 75kg のダイエット＋マッチョ化を目指すプロジェクト。
アプリ（HTML）+ LINE通知 + Claude Codeでの定期調整で運用。

## 目標
- 現在体重: 93kg（2026-03-22時点）
- 目標体重: 75kg
- 方針: 痩せる + 筋肉をつける（彼女の要望: マッチョ）
- 期間: 9〜12ヶ月

## ファイル構成
```
projects/75quest/
  index.html        — メインアプリ（75Quest）
  beauty.html       — Beauty Tips ページ
  CLAUDE.md         — この設計書
```

## 関連ノート
```
notes/training-menu-2026-03-22.md          — トレーニングメニュー詳細
notes/diet-fasting-research-2026-03-22.md  — ファスティング調査
notes/health-medical-diet-research.md      — 医療ダイエット調査
notes/mounjaro-risk-research-2026-03-22.md — GLP-1リスク調査
notes/diet-supplement-medical-research-2026-03-22.md — サプリ調査
notes/face-beauty-plan-2026-03-22.md       — 美容プラン
notes/mens-beauty-research-2026-03-22.md   — メンズ美容調査
```

## 運動計画
### トレーニング曜日
| 月 | 火 | 水 | 木 | 金 | 土 | 日 |
|---|---|---|---|---|---|---|
| 上半身A💪 | 休み🧘 | 下半身A🦵 | 休み🧘 | 上半身B💪 | 下半身B🦵 | 休み🧘 |

### 断食（16:8）= トレーニング日のみ
- 月・水・金・土 → 16:8断食（12:00〜20:00に食事）
- 火・木・日 → 自由食（カロリーは意識）

### Phase進行
- Phase 1（1-2週）: 自重のみ、毎日10分 ← **今ここ**
- Phase 2（3-4週）: 自重、週4回×20分
- Phase 3（5週〜）: ダンベル導入、週4回×30分
- Phase 4（目安80kg〜）: ジム通い検討

### 進行の仕方
かわちが「楽になった」「もっといける」と言ったらPhaseを上げる。
「膝が痛い」「キツすぎ」と言ったら調整。
Claude Codeの会話でメニュー変更 → アプリのindex.htmlを更新。

## 食事管理
- 目標カロリー: 2,000kcal/日
- PFC: P30% F25% C45%（タンパク質150g以上を意識）
- LINE「My Assistant」で食事コーチング

## サプリ・医療サポート
| アイテム | タイミング | 購入先 |
|---------|----------|--------|
| EZOBOLIC プロテイン | トレ後 or 朝 | EZOBOLIC店舗/Amazon |
| クレアチン 5g | 毎日 | Amazon |
| 難消化性デキストリン | 食前 | Amazon/ドラッグストア |
| 防風通聖散 | 食前1日3回 | ドラッグストア/内科処方 |
| コーヒー | 運動30分前 | — |

### GLP-1（マンジャロ）→ 保留
リスク大（リバウンド82.5%、筋肉25-39%減少、訴訟3,363件）。
食事+運動+ファスティングで落とせるなら不要。

## 美容プラン
- ヒゲ脱毛: 1回済、あと4-5回必要
- 肌質改善: ダーマペン + ピコレーザー交互（5ヶ月計画）
- 歪み矯正: カウンセリング → エラボトックス → ヒアルロン酸
- AGAケア: 要調査（フィナステリド、ミノキシジル等）
- ICL（視力矯正手術）: 要調査（費用、クリニック選び）

## LINE通知
- アカウント: My Assistant（通知専用）
- スクリプト: `scripts/line-notify.sh`
- 食事コーチング: `.claude/skills/line-food-coach.md`
- タスク管理: `.claude/skills/line-task-assistant.md`
- 買い物リスト: アプリ内 + LINE

## データ保存
- アプリデータ: ブラウザ localStorage（キー接頭辞: 75q_）
- 体重ログ: localStorage + `data/health/`
- 将来: Supabase等でクラウド化を検討

## 関連スキル
- `health-report` — 健康・美容総合管理
- `line-food-coach` — LINE食事コーチ
- `line-task-assistant` — LINEタスク管理

## キーワード一覧
| キーワード | 説明 |
|---|---|
| 75Quest | プロジェクト全体 |
| トレーニング | メニュー確認・調整 |
| 食事管理 | カロリー・PFC相談 |
| 断食 | 16:8断食の相談 |
| 美容 | 肌・整形の相談 |
| サプリ | サプリ・医療の相談 |
| 買い物リスト | 購入が必要なもの |
| Phase変更 | トレーニング強度を上げる |

## 完了済み
- [x] GitHub Pagesにデプロイ（https://kawamotoyuki1.github.io/75quest/）
- [x] LINE bot構築（AI会話コーチモード）
- [x] Renderデプロイ（https://seven5quest.onrender.com）
- [x] Supabase DB 9テーブル + RLS
- [x] ログイン機能（Supabase Auth）
- [x] PWA対応（ホーム画面追加可能）
- [x] UptimeRobot設定（サーバースリープ防止）
- [x] フロントアプリ → DB接続
- [x] 食事記録（テキスト+画像AI解析）
- [x] 自動アラート5つ（朝/サプリ/トレ/食事/まとめ）

## TODO（個人利用）
- [ ] Eufy P2 Pro → Apple ヘルスケア連携ON
- [ ] 防風通聖散を薬局で購入
- [ ] 難消化性デキストリン購入
- [ ] クレアチン購入
- [ ] ヨガマット購入
- [ ] 美容クリニック カウンセリング予約
- [ ] アプリの断食ロジック統一（トレ日=12:00〜20:00のみ）
- [ ] アプリのデザイン改善

## TODO（商品化 → 次のセッションで）
- [ ] マルチユーザー対応（user_id紐付け）
- [ ] オンボーディングフロー（LINE登録→目標設定→体験開始）
- [ ] Stripe課金連携（Free/Light/Standard/VIP）
- [ ] LP作成（サービス紹介+LINE登録CTA）
- [ ] SNSコンテンツテンプレート作成
- [ ] 利用規約・プライバシーポリシー
- [ ] 特定商取引法表記
- [ ] SNSアカウント作成（TikTok + Instagram + X）

## 事業計画
→ `business-plan.md` に全体計画を記載
