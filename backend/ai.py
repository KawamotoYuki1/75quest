"""Claude API for food analysis"""
import anthropic
import base64
import httpx
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FOOD_ANALYSIS_PROMPT = """あなたは栄養管理のプロです。食事情報からカロリーとPFC（タンパク質・脂質・炭水化物）を算出してください。

重要ルール:
- 写真の場合、パッケージの栄養成分表示を最優先で読み取る（コンビニ弁当、お菓子、飲み物等）
- パッケージに商品名が見えたらそれを使う
- 栄養成分表示が読めない場合は、料理の見た目から概算
- テキストの場合は日本の一般的な量で概算
- 必ず以下のJSON形式のみで返してください。JSON以外のテキストは絶対に含めないでください

{"meal_type":"breakfast","description":"商品名や料理名","calories":500,"protein":20,"fat":15,"carbs":60,"comment":"一言コメント"}

meal_typeの判定:
- 朝/モーニング → breakfast
- 昼/ランチ → lunch
- 夜/ディナー/夕食 → dinner
- 間食/おやつ/プロテイン/飲み物 → snack
- 指定なし → 現在時刻で判定（12時前=breakfast, 12-17時=lunch, 17時以降=dinner）
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


IMAGE_ANALYSIS_PROMPT = """この食事の写真を分析してください。

最優先: パッケージやラベルに書かれた商品名・栄養成分表示（カロリー、たんぱく質、脂質、炭水化物）を読み取る。
コンビニ（セブンイレブン、ファミマ、ローソン等）の商品の場合、ラベルの文字を正確に読む。
複数の商品がある場合、全商品を合算する。
栄養成分表示が読めない場合は、見た目と商品名から概算する。

必ず以下のJSON形式のみで返してください。JSON以外のテキストは絶対に含めないでください。

{"meal_type":"lunch","description":"全商品名を列挙","calories":合計数値,"protein":合計数値,"fat":合計数値,"carbs":合計数値,"comment":"一言コメント"}
"""

def analyze_food_image_from_base64(b64_data: str, media_type: str = "image/jpeg") -> dict:
    """Base64画像から食事を解析（Sonnetで高精度）"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": IMAGE_ANALYSIS_PROMPT},
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
