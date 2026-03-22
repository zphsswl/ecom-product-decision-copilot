from typing import Any

from fastapi import HTTPException
from supabase import Client

from llm.factory import get_llm_provider


def get_product_by_id(supabase: Client, product_id: str) -> dict[str, Any]:
    response = (
        supabase.table("products")
        .select("*")
        .eq("id", product_id)
        .limit(1)
        .execute()
    )

    data = response.data or []
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return data[0]


def get_saved_analysis(supabase: Client, product_id: str) -> dict[str, Any] | None:
    response = (
        supabase.table("product_ai_reports")
        .select("*")
        .eq("product_id", product_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    data = response.data or []
    if len(data) == 0:
        return None

    return data[0]


def save_analysis(supabase: Client, product_id: str, analysis: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "product_id": product_id,
        "summary": analysis.get("summary", ""),
        "why_hot": analysis.get("why_hot", ""),
        "opportunity_type": analysis.get("opportunity_type", ""),
        "target_seller": analysis.get("target_seller", ""),
        "selling_points": analysis.get("selling_points", ""),
        "risks": analysis.get("risks", ""),
        "test_plan": analysis.get("test_plan", ""),
        "recommendation": analysis.get("recommendation", ""),
    }

    response = supabase.table("product_ai_reports").insert(payload).execute()

    data = response.data or []
    if len(data) == 0:
        raise HTTPException(status_code=500, detail="Failed to save analysis")

    return data[0]


def analyze_product_with_llm(
    supabase: Client,
    product_id: str,
    provider_name: str | None = None,
) -> dict[str, Any]:
    product = get_product_by_id(supabase, product_id)
    provider = get_llm_provider(provider_name)
    analysis = provider.analyze_product(product)
    saved = save_analysis(supabase, product_id, analysis)
    return saved


def build_report_text(product: dict[str, Any], analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return (
            f"商品名称：{product.get('product_name')}\n"
            f"当前暂无 AI 分析结果，请先在商品详情页生成 AI 分析。"
        )

    return (
        f"【选品报告】\n\n"
        f"商品名称：{product.get('product_name')}\n"
        f"类目：{product.get('category') or '未分类'}\n"
        f"价格：{product.get('price')}\n"
        f"GMV：{product.get('gmv')}\n"
        f"销量：{product.get('sales')}\n"
        f"增速：{product.get('growth_rate')}%\n"
        f"推荐标签：{product.get('recommendation_label') or '未评分'}\n"
        f"机会评分：{product.get('opportunity_score')}\n"
        f"趋势分：{product.get('trend_score')}\n"
        f"竞争分：{product.get('competition_score')}\n"
        f"内容分：{product.get('content_score')}\n"
        f"风险分：{product.get('risk_score')}\n"
        f"近期表现：{product.get('recent_performance') or '暂无'}\n\n"
        f"【AI 总结】\n{analysis.get('summary') or '-'}\n\n"
        f"【为什么能卖】\n{analysis.get('why_hot') or '-'}\n\n"
        f"【机会类型】\n{analysis.get('opportunity_type') or '-'}\n\n"
        f"【适合卖家】\n{analysis.get('target_seller') or '-'}\n\n"
        f"【建议切入卖点】\n{analysis.get('selling_points') or '-'}\n\n"
        f"【主要风险】\n{analysis.get('risks') or '-'}\n\n"
        f"【测试计划】\n{analysis.get('test_plan') or '-'}\n\n"
        f"【最终建议】\n{analysis.get('recommendation') or '-'}\n"
    )


def get_product_report(supabase: Client, product_id: str) -> dict[str, Any]:
    product = get_product_by_id(supabase, product_id)
    analysis = get_saved_analysis(supabase, product_id)
    report_text = build_report_text(product, analysis)

    return {
        "product": product,
        "analysis": analysis,
        "report_text": report_text,
    }