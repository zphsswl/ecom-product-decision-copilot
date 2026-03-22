import json
import time
from os import getenv
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")

DEEPSEEK_API_KEY = getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing in .env")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY is missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

BATCH_SIZE = 20
SLEEP_SECONDS = 1.5
MAX_RETRIES = 3


def fetch_products_to_translate(limit: int = 200) -> list[dict[str, Any]]:
    """
    拉取还没有中文翻译的商品。
    """
    response = (
        supabase.table("products")
        .select("id, product_name, shop_name, product_name_zh, shop_name_zh")
        .limit(limit)
        .execute()
    )

    rows = response.data or []

    need_translate = []
    for row in rows:
        product_name = row.get("product_name")
        shop_name = row.get("shop_name")
        product_name_zh = row.get("product_name_zh")
        shop_name_zh = row.get("shop_name_zh")

        if not product_name:
            continue

        if product_name_zh and shop_name_zh:
            continue

        need_translate.append(row)

    return need_translate


def build_translation_prompt(items: list[dict[str, Any]]) -> str:
    payload = []
    for item in items:
        payload.append(
            {
                "id": item["id"],
                "product_name": item.get("product_name"),
                "shop_name": item.get("shop_name"),
            }
        )

    return f"""
你是一个跨境电商数据清洗助手。
请把下面商品的 product_name 和 shop_name 翻译成简体中文。

要求：
1. 保留品牌名、型号、规格、重量、容量等关键信息。
2. 不要胡乱扩写。
3. 如果原文已经是中文，可以直接保留。
4. 如果 shop_name 为空，返回空字符串。
5. 输出必须是合法 JSON 数组，不要输出 markdown，不要输出额外解释。

输入数据：
{json.dumps(payload, ensure_ascii=False)}

输出格式：
[
  {{
    "id": "商品id",
    "product_name_zh": "商品名中文翻译",
    "shop_name_zh": "店铺名中文翻译"
  }}
]
""".strip()


def translate_batch(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt = build_translation_prompt(items)

    response = llm_client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个专业的多语种商品标题翻译助手。"
                    "你必须严格输出 JSON。"
                ),
            },
            {
                "role": "user",
                "content": (
                    prompt
                    + "\n\n请输出格式："
                    + '{"items":[{"id":"...","product_name_zh":"...","shop_name_zh":"..."}]}'
                ),
            },
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned empty content")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {content}") from e

    if isinstance(parsed, dict) and "items" in parsed:
        return parsed["items"]

    if isinstance(parsed, list):
        return parsed

    raise ValueError(f"Unexpected translation output format: {parsed}")


def update_translations(translated_items: list[dict[str, Any]]) -> None:
    for item in translated_items:
        product_id = item.get("id")
        product_name_zh = item.get("product_name_zh")
        shop_name_zh = item.get("shop_name_zh")

        if not product_id:
            continue

        (
            supabase.table("products")
            .update(
                {
                    "product_name_zh": product_name_zh or None,
                    "shop_name_zh": shop_name_zh or None,
                }
            )
            .eq("id", product_id)
            .execute()
        )


def main():
    rows = fetch_products_to_translate(limit=500)

    if not rows:
        print("没有需要翻译的商品。")
        return

    print(f"待翻译商品数：{len(rows)}")

    total = len(rows)
    processed = 0

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        success = False
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                translated = translate_batch(batch)
                update_translations(translated)
                processed += len(batch)
                print(f"已完成 {processed}/{total}")
                success = True
                time.sleep(SLEEP_SECONDS)
                break
            except Exception as e:
                last_error = e
                print(f"批次 {i}-{i + len(batch)} 第 {attempt + 1} 次失败：{e}")
                time.sleep(2)

        if not success:
            raise RuntimeError(f"批次翻译失败，范围 {i}-{i + len(batch)}，最后错误：{last_error}")

    print("全部翻译完成。")


if __name__ == "__main__":
    main()