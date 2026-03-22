import json
from os import getenv
from typing import Any

from openai import OpenAI


def build_product_analysis_prompt(product: dict[str, Any]) -> str:
    return f"""
请基于以下跨境电商商品数据做选品分析，并严格输出 JSON。

商品数据：
- 商品名称: {product.get("product_name")}
- 商品状态: {product.get("product_status")}
- 店铺名称: {product.get("shop_name")}
- 国家/地区: {product.get("region")}
- 商品分类: {product.get("category")}
- 售价: {product.get("price")}
- 佣金比例: {product.get("commission_rate")}
- 7天销量: {product.get("sales_7d")}
- 7天销售额: {product.get("gmv_7d")}
- 总销量: {product.get("total_sales")}
- 总销售额: {product.get("total_gmv")}
- 带货达人总数: {product.get("creator_total")}
- 达人出单率: {product.get("creator_conversion_rate")}
- 带货视频总数: {product.get("video_total")}
- 带货直播总数: {product.get("live_total")}
- 预估商品上架时间: {product.get("estimated_listing_time")}
- 机会评分: {product.get("opportunity_score")}
- 趋势分: {product.get("trend_score")}
- 竞争分: {product.get("competition_score")}
- 内容分: {product.get("content_score")}
- 风险分: {product.get("risk_score")}
- 推荐标签: {product.get("recommendation_label")}

请重点分析：
1. 这是短期爆发还是长期稳定机会？
2. 它更依赖视频还是直播？
3. 达人出单率和佣金比例是否说明它适合联盟带货？
4. 当前地区是否已经竞争激烈？
5. 适合什么类型卖家切入？
6. 如果切入，建议从什么卖点开始？
7. 主要风险是什么？
8. 建议怎么测试？

输出必须是合法 JSON：
{{
  "summary": "一句话总结这个品是否值得做",
  "why_hot": "这个商品为什么能卖起来",
  "opportunity_type": "短期爆款 / 长期机会 / 谨慎观察 三选一",
  "target_seller": "更适合什么类型卖家",
  "selling_points": "建议切入卖点，1段文字",
  "risks": "主要风险，1段文字",
  "test_plan": "建议如何测试，1段文字",
  "recommendation": "推荐 / 谨慎测试 / 不推荐 三选一"
}}
""".strip()


class BaseLLMProvider:
    def analyze_product(self, product: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self):
        api_key = getenv("DEEPSEEK_API_KEY")
        base_url = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        model = getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is missing in .env")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_product(self, product: dict[str, Any]) -> dict[str, Any]:
        prompt = build_product_analysis_prompt(product)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名跨境电商选品分析师。"
                        "你要根据商品的结构化指标，输出简洁、专业、可执行的分析。"
                        "输出必须是合法 JSON，不要输出 markdown，不要输出额外解释。"
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {content}") from e


class DoubaoProvider(BaseLLMProvider):
    def __init__(self):
        api_key = getenv("DOUBAO_API_KEY")
        base_url = getenv("DOUBAO_BASE_URL")
        model = getenv("DOUBAO_MODEL")

        if not api_key or not base_url or not model:
            raise RuntimeError("DOUBAO_API_KEY / DOUBAO_BASE_URL / DOUBAO_MODEL is missing in .env")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_product(self, product: dict[str, Any]) -> dict[str, Any]:
        prompt = build_product_analysis_prompt(product)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名跨境电商选品分析师。"
                        "你要根据商品的结构化指标，输出简洁、专业、可执行的分析。"
                        "输出必须是合法 JSON，不要输出 markdown，不要输出额外解释。"
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {content}") from e


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        api_key = getenv("OPENAI_API_KEY")
        base_url = getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = getenv("OPENAI_MODEL")

        if not api_key or not model:
            raise RuntimeError("OPENAI_API_KEY / OPENAI_MODEL is missing in .env")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_product(self, product: dict[str, Any]) -> dict[str, Any]:
        prompt = build_product_analysis_prompt(product)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名跨境电商选品分析师。"
                        "你要根据商品的结构化指标，输出简洁、专业、可执行的分析。"
                        "输出必须是合法 JSON，不要输出 markdown，不要输出额外解释。"
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {content}") from e