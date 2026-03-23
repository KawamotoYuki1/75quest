"""75Quest LINE Bot - AI Assistant Mode"""
import json
import hmac
import hashlib
import base64
from datetime import date, datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import anthropic

from config import (
    LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID,
    TRAINING_DAYS, FASTING_DAYS, DAILY_CALORIE_TARGET, DAILY_PROTEIN_TARGET,
    ANTHROPIC_API_KEY, JST
)
import db

# Claude client
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Conversation history (in-memory, last 20 messages)
conv_history = []
MAX_HISTORY = 20

# Scheduler
scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="75Quest Bot", lifespan=lifespan)


# === System Prompt ===
def build_system_prompt():
    now = datetime.now(JST)
    today = now.date()
    dow = today.weekday()
    is_train = dow in TRAINING_DAYS
    is_fast = dow in FASTING_DAYS
    hour = now.hour
    menus = {0: "上半身A（膝つき腕立て、ペットボトルプレス、サイドレイズ、プランク）",
             2: "下半身A（スクワット、ランジ、カーフレイズ、脚上げ）",
             4: "上半身B（腕立て、バックエクステンション、アームカール、クランチ）",
             5: "下半身B（ワイドスクワット、ブルガリアンスクワット、ヒップリフト、マウンテンクライマー）"}

    # Get current data
    today_meals = db.get_today_meals()
    total_cal = sum(m.get("calories") or 0 for m in today_meals)
    total_p = sum(m.get("protein") or 0 for m in today_meals)
    water = db.get_today_water()
    workout = db.get_today_workout()
    weight = db.get_latest_weight()
    events = db.get_today_events()

    meals_desc = ""
    if today_meals:
        for m in today_meals:
            meals_desc += f"  - {m['meal_type']}: {m['description']} ({m.get('calories',0)}kcal, P{m.get('protein',0)}g)\n"
    else:
        meals_desc = "  まだ記録なし\n"

    return f"""あなたは「75Quest」のAIパーソナルトレーナー兼栄養士です。名前は「My Assistant」。
ユーザーは「かわち」（男性、目標75kg）です。友達のように親しく、でもプロのアドバイスをする。

## 現在の状態
- 日時: {now.strftime('%Y-%m-%d %H:%M')}（{['月','火','水','木','金','土','日'][dow]}曜日）
- 体重: {weight['weight'] if weight else '未記録'}kg（目標75kg）
- 今日のカロリー: {total_cal} / {DAILY_CALORIE_TARGET}kcal（残り{DAILY_CALORIE_TARGET - total_cal}kcal）
- タンパク質: {total_p:.0f}g / {DAILY_PROTEIN_TARGET}g
- 水分: {water}ml / 2000ml
- トレーニング: {'✅完了' if workout else '❌未完了'} {'(' + menus.get(dow, '') + ')' if is_train else ''}
- 今日は{'トレーニング日: ' + menus.get(dow, '') if is_train else '休息日'}
- 断食: {'16:8断食日（12:00〜20:00のみ食事OK）' if is_fast else '自由食の日'}
- 現在{'食事OK（12:00〜20:00）' if is_fast and 12 <= hour < 20 else '断食中' if is_fast else '自由食'}
{f'- イベント: {", ".join(e["icon"]+e["name"] for e in events)}' if events else ''}

## 今日の食事記録
{meals_desc}
## あなたができること（必ずJSONアクションで実行）

ユーザーのメッセージに応じて、返答テキストと一緒にアクションを実行できます。
返答は必ず以下のJSON形式で返してください：

{{"reply": "ユーザーへの返答テキスト", "actions": [アクション配列]}}

### アクション一覧
1. 食事記録: {{"action":"meal","meal_type":"lunch","description":"料理名","calories":500,"protein":20,"fat":15,"carbs":60}}
2. 食事削除: {{"action":"delete_meal","meal_id":数値}} または {{"action":"delete_recent_meals","minutes":5}}
3. 体重記録: {{"action":"weight","weight":91.5}}
4. 水分記録: {{"action":"water","amount_ml":500}}
5. トレーニング完了: {{"action":"workout","menu_name":"上半身A"}}
6. タスク追加: {{"action":"task","text":"単4電池買う","category":"買い物"}}
7. アクションなし: {{"action":"none"}}

## ルール
- 必ずJSON形式で返す（reply + actions）
- 食事報告には必ずカロリー・PFCを概算して記録する
- 複数の料理がある場合は合計を1つのmealアクションにまとめる
- 「違う」「間違い」「訂正」と言われたら、直近の食事を削除して正しいものを登録
- 写真の場合は見た目から判断（パッケージが見えたら読み取る）
- 断食中に食事報告が来たら「断食中だけど大丈夫？」と聞く
- アドバイスは具体的に（「タンパク質が足りてないから夜はサラダチキンがいいよ」等）
- 励ましは自然に（「いい感じ！」「ナイス選択！」）
- 質問には知識ベースで回答（栄養学、トレーニング、ダイエット）
- かわちは93kg→75kgを目指している。元は75kg。彼女からマッチョになってほしいと言われている
- サプリ: EZOBOLIC プロテイン、クレアチン5g、難消化性デキストリン、防風通聖散
- プロテインは断食中NG（カロリーがあるため）
"""


# === LINE Messaging ===
async def send_line_message(text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}", "Content-Type": "application/json"},
            json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": text}]}
        )

async def reply_line_message(reply_token: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}", "Content-Type": "application/json"},
            json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
        )

async def download_line_image(message_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api-data.line.me/v2/bot/message/{message_id}/content",
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
        )
        return resp.content


# === AI Processing ===
def extract_json(text: str) -> dict:
    import re
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"reply": text, "actions": []}


async def process_message(text: str, image_b64: str = None):
    """Send message to Claude and execute actions"""
    global conv_history

    # Build message content
    content = []
    if image_b64:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}})
        content.append({"type": "text", "text": text or "この食事の写真を分析して記録してください。パッケージの商品名が見えたら読み取ってください。"})
    else:
        content.append({"type": "text", "text": text})

    # Add to history
    conv_history.append({"role": "user", "content": content})
    if len(conv_history) > MAX_HISTORY:
        conv_history = conv_history[-MAX_HISTORY:]

    # Call Claude
    model = "claude-sonnet-4-20250514" if image_b64 else "claude-haiku-4-5-20251001"
    response = claude.messages.create(
        model=model,
        max_tokens=1000,
        system=build_system_prompt(),
        messages=conv_history
    )

    raw = response.content[0].text
    result = extract_json(raw)

    reply_text = result.get("reply", raw)
    actions = result.get("actions", [])

    # Execute actions
    for act in actions:
        a = act.get("action")
        try:
            if a == "meal":
                db.record_meal(act["meal_type"], act["description"], act.get("calories"), act.get("protein"), act.get("fat"), act.get("carbs"))
            elif a == "delete_meal":
                db.get_db().table("meals").delete().eq("id", act["meal_id"]).execute()
            elif a == "delete_recent_meals":
                mins = act.get("minutes", 5)
                cutoff = (datetime.now(JST) - timedelta(minutes=mins)).isoformat()
                today = datetime.now(JST).date().isoformat()
                db.get_db().table("meals").delete().eq("date", today).gte("created_at", cutoff).execute()
            elif a == "weight":
                db.record_weight(act["weight"])
            elif a == "water":
                db.add_water(act["amount_ml"])
            elif a == "workout":
                db.record_workout(act.get("menu_name", "トレーニング"), [], completed=True)
            elif a == "task":
                db.add_task(act["text"], act.get("category", "タスク"))
        except Exception as e:
            print(f"[ACTION ERROR] {a}: {e}")

    # Add assistant response to history
    conv_history.append({"role": "assistant", "content": raw})

    return reply_text


# === Webhook ===
def verify_signature(body: bytes, signature: str) -> bool:
    hash = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(hash).decode(), signature)

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)
    for event in data.get("events", []):
        if event["type"] == "message":
            reply_token = event["replyToken"]
            msg = event["message"]

            try:
                if msg["type"] == "text":
                    reply = await process_message(msg["text"])
                    await reply_line_message(reply_token, reply)
                elif msg["type"] == "image":
                    image_data = await download_line_image(msg["id"])
                    b64 = base64.b64encode(image_data).decode("utf-8")
                    reply = await process_message(None, image_b64=b64)
                    await reply_line_message(reply_token, reply)
            except Exception as e:
                import traceback
                print(f"[ERROR] {traceback.format_exc()}")
                await reply_line_message(reply_token, f"エラーが発生しました: {str(e)[:150]}")

    return JSONResponse(content={"status": "ok"})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "75quest-bot", "mode": "ai-assistant"}


# === Scheduled Alerts ===
def setup_scheduler():
    scheduler.add_job(alert_morning, "cron", hour=8, minute=3)
    scheduler.add_job(alert_supplement, "cron", hour=11, minute=50)
    scheduler.add_job(alert_training, "cron", hour=20, minute=3)
    scheduler.add_job(alert_food_log, "cron", hour=21, minute=3)
    scheduler.add_job(alert_daily_summary, "cron", hour=22, minute=3)

async def alert_morning():
    now = datetime.now(JST)
    dow = now.weekday()
    is_train = dow in TRAINING_DAYS
    menus = {0: "上半身A 💪", 2: "下半身A 🦵", 4: "上半身B 💪", 5: "下半身B 🦵"}
    events = db.get_today_events()
    msg = f"🌅 おはよう、かわち！\n\n"
    msg += f"今日は{'トレーニング日: ' + menus.get(dow, '') if is_train else '休息日 🧘'}\n"
    msg += f"{'🕐 16:8断食（12:00まで我慢！）' if dow in FASTING_DAYS else '🍽 自由食の日'}\n"
    if events:
        msg += f"\n📅 {', '.join(e['icon']+e['name'] for e in events)}\n"
    msg += "\n💊 防風通聖散飲んでね！"
    await send_line_message(msg)

async def alert_supplement():
    dow = datetime.now(JST).weekday()
    if dow not in FASTING_DAYS:
        return
    await send_line_message("🍵 もうすぐ12:00！\n食事前に：\n・防風通聖散\n・難消化性デキストリン\n飲んでから食べてね！")

async def alert_training():
    dow = datetime.now(JST).weekday()
    if dow not in TRAINING_DAYS:
        return
    workout = db.get_today_workout()
    if not workout:
        menus = {0: "上半身A", 2: "下半身A", 4: "上半身B", 5: "下半身B"}
        menu = menus.get(dow, "トレーニング")
        await send_line_message(f"💪 かわち、今日の{menu}まだだよ！\n20分だけ！やろう！\n\nやったら「筋トレ完了」って送ってね")

async def alert_food_log():
    meals = db.get_today_meals()
    if not meals:
        await send_line_message("🍽 今日の食事、何も記録してないよ！\n食べたものを送ってね\n（写真でもテキストでもOK）")

async def alert_daily_summary():
    today_meals = db.get_today_meals()
    total_cal = sum(m.get("calories") or 0 for m in today_meals)
    total_p = sum(m.get("protein") or 0 for m in today_meals)
    water = db.get_today_water()
    workout = db.get_today_workout()
    weight = db.get_latest_weight()
    dow = datetime.now(JST).weekday()
    is_train = dow in TRAINING_DAYS

    msg = f"🌙 おつかれ、かわち！今日のまとめ\n\n"
    if weight:
        msg += f"⚖️ 体重: {weight['weight']}kg（あと{weight['weight']-75:.1f}kg）\n"
    msg += f"🍽 カロリー: {total_cal} / {DAILY_CALORIE_TARGET}kcal\n"
    msg += f"💪 タンパク質: {total_p:.0f}g / {DAILY_PROTEIN_TARGET}g\n"
    msg += f"💧 水: {water}ml / 2000ml\n"
    if is_train:
        msg += f"🏋️ トレ: {'✅完了！' if workout else '❌やれなかった...'}\n"
    msg += f"\n{'💯 いい1日！' if total_cal <= DAILY_CALORIE_TARGET and total_p >= 100 else '明日もがんばろう！'}"
    await send_line_message(msg)
