"""Claude API for food analysis"""
import anthropic
import base64
import httpx
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FOOD_ANALYSIS_PROMPT = """あなたは栄養管理のプロです。以下の食事情報からカロリーとPFC（タンパク質・脂質・炭水化物）を概算してください。

ルール:
- 日本の一般的な量で計算
- 概算でOK（正確でなくて良い）
- 必ず以下のJSON形式で返してください（他のテキストは不要）

{
  "meal_type": "breakfast|lunch|dinner|snack",
  "description": "料理名の要約",
  "calories": 数値,
  "protein": 数値(g),
  "fat": 数値(g),
  "carbs": 数値(g),
  "comment": "一言コーチングコメント（励まし or アドバイス）"
}

meal_typeの判定:
- 朝/モーニング → breakfast
- 昼/ランチ → lunch
- 夜/ディナー/夕食 → dinner
- 間食/おやつ/プロテイン → snack
- 時間帯の指定がなければ現在時刻で判定（12時前=breakfast, 12-17時=lunch, 17時以降=dinner）
"""

def extract_json(text: str) -> dict:
    """レスポンスからJSONを抽出"""
    import json, re
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find JSON block in text
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON found in: {text[:200]}")

def analyze_food_text(text: str) -> dict:
    """テキストから食事を解析"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"{FOOD_ANALYSIS_PROMPT}\n\n食事内容: {text}"
        }]
    )
    return extract_json(response.content[0].text)


def analyze_food_image_from_base64(b64_data: str, media_type: str = "image/jpeg") -> dict:
    """Base64画像から食事を解析"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": FOOD_ANALYSIS_PROMPT + "\n\nこの食事の写真を分析してください。"},
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64_data}}
            ]
        }]
    )
    return extract_json(response.content[0].text)


def analyze_food_image(image_url: str) -> dict:
    """画像から食事を解析"""
    # Download image
    resp = httpx.get(image_url)
    image_data = base64.b64encode(resp.content).decode("utf-8")
    content_type = resp.headers.get("content-type", "image/jpeg")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": FOOD_ANALYSIS_PROMPT + "\n\nこの食事の写真を分析してください。"},
                {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": image_data}}
            ]
        }]
    )
    return extract_json(response.content[0].text)
