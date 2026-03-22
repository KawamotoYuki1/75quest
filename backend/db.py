"""Supabase DB operations for 75Quest"""
from datetime import date, datetime
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, JST

def today_jst():
    return datetime.now(JST).date()

_client = None

def get_db():
    global _client
    if not _client:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# === Weight ===
def record_weight(weight: float, body_fat: float = None, memo: str = None):
    db = get_db()
    today = today_jst().isoformat()
    existing = db.table("weight_log").select("id").eq("date", today).execute()
    if existing.data:
        db.table("weight_log").update({"weight": weight, "body_fat": body_fat, "memo": memo}).eq("date", today).execute()
    else:
        db.table("weight_log").insert({"date": today, "weight": weight, "body_fat": body_fat, "memo": memo}).execute()
    return weight

def get_latest_weight():
    db = get_db()
    result = db.table("weight_log").select("*").order("date", desc=True).limit(1).execute()
    return result.data[0] if result.data else None

def get_weight_history(days=7):
    db = get_db()
    result = db.table("weight_log").select("*").order("date", desc=True).limit(days).execute()
    return result.data


# === Meals ===
def record_meal(meal_type: str, description: str, calories: int = None, protein: float = None, fat: float = None, carbs: float = None):
    db = get_db()
    today = today_jst().isoformat()
    db.table("meals").insert({
        "date": today,
        "meal_type": meal_type,
        "description": description,
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
    }).execute()

def get_today_meals():
    db = get_db()
    today = today_jst().isoformat()
    result = db.table("meals").select("*").eq("date", today).execute()
    return result.data


# === Workouts ===
def record_workout(menu_name: str, exercises: list, completed: bool = True):
    db = get_db()
    today = today_jst().isoformat()
    db.table("workouts").insert({
        "date": today,
        "menu_name": menu_name,
        "exercises": exercises,
        "completed": completed,
    }).execute()

def get_today_workout():
    db = get_db()
    today = today_jst().isoformat()
    result = db.table("workouts").select("*").eq("date", today).execute()
    return result.data


# === Water ===
def add_water(amount_ml: int):
    db = get_db()
    today = today_jst().isoformat()
    existing = db.table("water_log").select("*").eq("date", today).execute()
    if existing.data:
        new_amount = existing.data[0]["amount_ml"] + amount_ml
        db.table("water_log").update({"amount_ml": new_amount}).eq("date", today).execute()
        return new_amount
    else:
        db.table("water_log").insert({"date": today, "amount_ml": amount_ml}).execute()
        return amount_ml

def get_today_water():
    db = get_db()
    today = today_jst().isoformat()
    result = db.table("water_log").select("*").eq("date", today).execute()
    return result.data[0]["amount_ml"] if result.data else 0


# === Tasks ===
def add_task(text: str, category: str = "タスク"):
    db = get_db()
    db.table("tasks").insert({"text": text, "category": category, "done": False}).execute()

def get_pending_tasks():
    db = get_db()
    result = db.table("tasks").select("*").eq("done", False).execute()
    return result.data

def complete_task(task_id: int):
    db = get_db()
    db.table("tasks").update({"done": True}).eq("id", task_id).execute()


# === Shopping ===
def add_shopping_item(name: str, url: str = None):
    db = get_db()
    db.table("shopping_list").insert({"item_name": name, "url": url, "purchased": False}).execute()

def get_shopping_list():
    db = get_db()
    result = db.table("shopping_list").select("*").eq("purchased", False).execute()
    return result.data


# === Events ===
def get_today_events():
    db = get_db()
    today = today_jst().isoformat()
    result = db.table("events").select("*").execute()
    return [e for e in result.data if e["start_date"] <= today <= e["end_date"]]

def get_upcoming_events(days=7):
    db = get_db()
    today = today_jst().isoformat()
    result = db.table("events").select("*").order("start_date").execute()
    return [e for e in result.data if e["start_date"] >= today]
