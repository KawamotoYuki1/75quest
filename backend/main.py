"""75Quest LINE Bot - Main Server"""
import json
import hmac
import hashlib
import base64
from datetime import date, datetime
from contextlib import asynccontextmanager
from config import JST

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID,
    TRAINING_DAYS, FASTING_DAYS, DAILY_CALORIE_TARGET, DAILY_PROTEIN_TARGET
)
import db
import ai

# Scheduler for alerts
scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="75Quest Bot", lifespan=lifespan)


# === LINE Messaging ===
async def send_line_message(text: str):
    """Send message to kawachi via LINE"""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "to": LINE_USER_ID,
                "messages": [{"type": "text", "text": text}]
            }
        )

async def reply_line_message(reply_token: str, text: str):
    """Reply to a LINE message"""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": text}]
            }
        )

async def get_line_image(message_id: str) -> str:
    """Get image content URL from LINE"""
    return f"https://api-data.line.me/v2/bot/message/{message_id}/content"

async def download_line_image(message_id: str) -> bytes:
    """Download image from LINE"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api-data.line.me/v2/bot/message/{message_id}/content",
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
        )
        return resp.content


# === Message Handlers ===
def categorize_task(text: str) -> str:
    cats = {"買": "買い物", "購入": "買い物", "予約": "手続き", "連絡": "連絡", "返信": "連絡", "調べ": "リサーチ"}
    for k, v in cats.items():
        if k in text:
            return v
    return "タスク"

async def handle_text_message(reply_token: str, text: str, user_id: str):
    """Process text messages"""
    t = text.strip()

    # Weight
    if t.startswith("体重"):
        try:
            w = float(t.replace("体重", "").replace("kg", "").replace("キロ", "").strip())
            db.record_weight(w)
            latest = db.get_weight_history(2)
            diff = ""
            if len(latest) > 1:
                d = latest[0]["weight"] - latest[1]["weight"]
                diff = f"\n前回比: {'+'if d>0 else ''}{d:.1f}kg"
            remain = w - 75
            await reply_line_message(reply_token, f"⚖️ 体重記録: {w}kg{diff}\nあと{remain:.1f}kg → 75kg目標\nがんばれかわち！💪")
            return
        except ValueError:
            pass

    # Water
    if "水" in t and any(c.isdigit() for c in t):
        try:
            import re
            nums = re.findall(r'\d+', t)
            ml = int(nums[0])
            if ml < 100:
                ml *= 1000  # 2L → 2000ml
            total = db.add_water(ml)
            pct = round(total / 2000 * 100)
            await reply_line_message(reply_token, f"💧 水 +{ml}ml\n今日の合計: {total}ml（{pct}%）")
            return
        except Exception:
            pass

    # Training done
    if any(k in t for k in ["筋トレ完了", "トレーニング完了", "トレ完了", "運動した", "筋トレした"]):
        today_dow = datetime.now(JST).date().weekday()
        menus = {0: "上半身A", 2: "下半身A", 4: "上半身B", 5: "下半身B"}
        menu = menus.get(today_dow, "トレーニング")
        db.record_workout(menu, [], completed=True)
        await reply_line_message(reply_token, f"💪 {menu} 完了！おつかれ！\n筋肉は裏切らない 🔥")
        return

    # Shopping list
    if t in ["買い物リスト", "買い物", "ショッピングリスト"]:
        items = db.get_shopping_list()
        if not items:
            await reply_line_message(reply_token, "🛒 買い物リストは空です")
            return
        lines = ["🛒 買い物リスト\n"]
        for item in items:
            lines.append(f"□ {item['item_name']}")
        await reply_line_message(reply_token, "\n".join(lines))
        return

    # Task list
    if t in ["タスク", "タスク一覧", "やること"]:
        tasks = db.get_pending_tasks()
        if not tasks:
            await reply_line_message(reply_token, "📝 タスクは空です！")
            return
        lines = ["📝 タスク一覧\n"]
        for task in tasks:
            lines.append(f"□ {task['text']}（{task['category']}）")
        await reply_line_message(reply_token, "\n".join(lines))
        return

    # Today summary
    if t in ["今日", "今日の予定", "状況", "ステータス"]:
        await send_today_summary(reply_token)
        return

    # Add task (contains 買う, する, etc.)
    if any(k in t for k in ["買う", "購入", "予約する", "連絡する", "返信する", "やる"]):
        cat = categorize_task(t)
        db.add_task(t, cat)
        count = len(db.get_pending_tasks())
        await reply_line_message(reply_token, f"✅ タスク追加\n「{t}」（{cat}）\n\n📋 残りタスク: {count}件")
        return

    # Default: treat as food report
    try:
        result = ai.analyze_food_text(t)
        db.record_meal(
            result["meal_type"],
            result["description"],
            result.get("calories"),
            result.get("protein"),
            result.get("fat"),
            result.get("carbs"),
        )
        today_meals = db.get_today_meals()
        total_cal = sum(m.get("calories") or 0 for m in today_meals)
        total_p = sum(m.get("protein") or 0 for m in today_meals)
        remain = DAILY_CALORIE_TARGET - total_cal

        meal_names = {"breakfast": "朝食", "lunch": "昼食", "dinner": "夕食", "snack": "間食"}
        meal_label = meal_names.get(result["meal_type"], "食事")

        msg = f"🍽 {meal_label}記録\n"
        msg += f"{result['description']}\n"
        msg += f"→ {result.get('calories', '?')}kcal（P{result.get('protein', '?')}g F{result.get('fat', '?')}g C{result.get('carbs', '?')}g）\n\n"
        msg += f"📊 今日の合計: {total_cal} / {DAILY_CALORIE_TARGET}kcal\n"
        msg += f"タンパク質: {total_p:.0f}g / {DAILY_PROTEIN_TARGET}g\n"
        msg += f"残り: {remain}kcal\n\n"
        msg += f"💬 {result.get('comment', 'いい感じ！')}"

        await reply_line_message(reply_token, msg)
    except Exception as e:
        # If AI analysis fails, just acknowledge
        await reply_line_message(reply_token, f"📝 メモしました: {t}")


async def handle_image_message(reply_token: str, message_id: str):
    """Process image messages (food photos)"""
    try:
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        # Download image directly for Claude
        image_data = await download_line_image(message_id)
        import base64
        b64 = base64.b64encode(image_data).decode("utf-8")

        import anthropic
        from config import ANTHROPIC_API_KEY
        aclient = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = aclient.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": ai.FOOD_ANALYSIS_PROMPT + "\n\nこの食事の写真を分析してください。"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}
                ]
            }]
        )
        result = json.loads(response.content[0].text)

        db.record_meal(
            result["meal_type"],
            result["description"],
            result.get("calories"),
            result.get("protein"),
            result.get("fat"),
            result.get("carbs"),
        )

        today_meals = db.get_today_meals()
        total_cal = sum(m.get("calories") or 0 for m in today_meals)
        remain = DAILY_CALORIE_TARGET - total_cal

        meal_names = {"breakfast": "朝食", "lunch": "昼食", "dinner": "夕食", "snack": "間食"}
        meal_label = meal_names.get(result["meal_type"], "食事")

        msg = f"📸 {meal_label}記録（写真から解析）\n"
        msg += f"{result['description']}\n"
        msg += f"→ {result.get('calories', '?')}kcal（P{result.get('protein', '?')}g F{result.get('fat', '?')}g C{result.get('carbs', '?')}g）\n\n"
        msg += f"📊 今日の合計: {total_cal} / {DAILY_CALORIE_TARGET}kcal\n"
        msg += f"残り: {remain}kcal\n\n"
        msg += f"💬 {result.get('comment', 'いい感じ！')}"

        await reply_line_message(reply_token, msg)
    except Exception as e:
        await reply_line_message(reply_token, f"📸 写真を受け取りました！解析中にエラーが発生しました: {str(e)[:100]}")


async def send_today_summary(reply_token: str = None):
    """Send today's summary"""
    today_dow = datetime.now(JST).date().weekday()
    is_train = today_dow in TRAINING_DAYS
    is_fast = today_dow in FASTING_DAYS
    menus = {0: "上半身A 💪", 2: "下半身A 🦵", 4: "上半身B 💪", 5: "下半身B 🦵"}

    meals = db.get_today_meals()
    total_cal = sum(m.get("calories") or 0 for m in meals)
    workout = db.get_today_workout()
    water = db.get_today_water()
    events = db.get_today_events()
    weight = db.get_latest_weight()

    msg = f"📋 今日のステータス\n\n"
    if weight:
        msg += f"⚖️ 体重: {weight['weight']}kg（あと{weight['weight']-75:.1f}kg）\n"
    msg += f"🍽 カロリー: {total_cal} / {DAILY_CALORIE_TARGET}kcal\n"
    msg += f"💧 水: {water}ml / 2000ml\n"
    msg += f"{'💪 トレ: ' + menus.get(today_dow, 'トレーニング') if is_train else '🧘 休息日'}"
    msg += f" {'✅完了' if workout else '❌未完了'}\n" if is_train else "\n"
    msg += f"{'🕐 16:8断食日' if is_fast else '🍽 自由食の日'}\n"
    if events:
        msg += f"\n📅 イベント: {', '.join(e['icon']+e['name'] for e in events)}\n"

    if reply_token:
        await reply_line_message(reply_token, msg)
    else:
        await send_line_message(msg)


# === Scheduled Alerts ===
def setup_scheduler():
    # Morning reminder (8:00)
    scheduler.add_job(alert_morning, "cron", hour=8, minute=3)
    # Supplement reminder (11:50 before lunch on fasting days)
    scheduler.add_job(alert_supplement, "cron", hour=11, minute=50)
    # Training reminder (20:00)
    scheduler.add_job(alert_training, "cron", hour=20, minute=3)
    # Food log reminder (21:00)
    scheduler.add_job(alert_food_log, "cron", hour=21, minute=3)
    # Daily summary (22:00)
    scheduler.add_job(alert_daily_summary, "cron", hour=22, minute=3)

async def alert_morning():
    """Morning greeting + today's plan"""
    import asyncio
    today_dow = datetime.now(JST).date().weekday()
    is_train = today_dow in TRAINING_DAYS
    is_fast = today_dow in FASTING_DAYS
    menus = {0: "上半身A 💪", 2: "下半身A 🦵", 4: "上半身B 💪", 5: "下半身B 🦵"}
    events = db.get_today_events()

    msg = "🌅 おはよう、かわち！\n\n"
    msg += f"今日は{'トレーニング日: ' + menus.get(today_dow, '') if is_train else '休息日 🧘'}\n"
    msg += f"{'🕐 16:8断食（12:00まで我慢！）' if is_fast else '🍽 自由食の日'}\n"
    if events:
        msg += f"\n📅 {', '.join(e['icon']+e['name'] for e in events)}\n"
    msg += "\n💊 防風通聖散忘れずに！"
    await send_line_message(msg)

async def alert_supplement():
    """Pre-lunch supplement reminder (fasting days)"""
    today_dow = datetime.now(JST).date().weekday()
    if today_dow not in FASTING_DAYS:
        return
    await send_line_message("🍵 もうすぐ12:00！\n食事前に：\n・防風通聖散\n・難消化性デキストリン\n飲んでから食べてね！")

async def alert_training():
    """Training reminder if not done"""
    today_dow = datetime.now(JST).date().weekday()
    if today_dow not in TRAINING_DAYS:
        return
    workout = db.get_today_workout()
    if not workout:
        menus = {0: "上半身A", 2: "下半身A", 4: "上半身B", 5: "下半身B"}
        menu = menus.get(today_dow, "トレーニング")
        await send_line_message(f"💪 かわち、今日の{menu}まだだよ！\n20分だけ！やろう！\n\nやったら「筋トレ完了」って送ってね")

async def alert_food_log():
    """Food log reminder if nothing recorded"""
    meals = db.get_today_meals()
    if not meals:
        await send_line_message("🍽 今日の食事、何も記録してないよ！\n食べたものを送ってね\n（写真でもテキストでもOK）")

async def alert_daily_summary():
    """End of day summary"""
    await send_today_summary()


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

            if msg["type"] == "text":
                await handle_text_message(reply_token, msg["text"], event["source"].get("userId"))
            elif msg["type"] == "image":
                await handle_image_message(reply_token, msg["id"])

    return JSONResponse(content={"status": "ok"})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "75quest-bot"}
