import os
from datetime import timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Timezone
JST = timezone(timedelta(hours=9))

# LINE
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Training schedule (day of week: 0=Mon ... 6=Sun in Python)
# Training: Mon(0), Wed(2), Fri(4), Sat(5)
TRAINING_DAYS = {0, 2, 4, 5}
FASTING_DAYS = TRAINING_DAYS  # 16:8 only on training days

# Calorie target
DAILY_CALORIE_TARGET = 2000
DAILY_PROTEIN_TARGET = 150  # grams
DAILY_WATER_TARGET = 2000   # ml
