from os import getenv

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client

from schemas.analysis import AnalyzeRequest
from schemas.policy import PolicyAskRequest, PolicyDocumentCreate, PolicyProcessRequest
from services.analysis_service import (
    analyze_product_with_llm,
    get_product_by_id,
    get_product_report,
    get_saved_analysis,
)
from services.policy_service import (
    ask_policy_question,
    build_integrated_report_text,
    create_policy_document,
    generate_product_policy_analysis,
    get_policy_chunks_by_document_id,
    get_policy_document_by_id,
    get_region_policy_summary,
    match_policy_chunks,
    process_policy_document,
    search_policy_documents,
)

load_dotenv()

SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Ecom Product Decision Copilot API",
    version="0.4.0",
    description="Backend API for the e-commerce AI product decision copilot.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok"}


# =========================
# 商品相关接口
# =========================

@app.get("/products/search", summary="Search and filter products")
def search_products(
    keyword: str | None = Query(None, description="商品名称关键词"),
    region: str | None = Query(None, description="国家/地区"),
    category: str | None = Query(None, description="商品分类"),
    product_status: str | None = Query(None, description="商品状态"),
    min_sales_7d: int | None = Query(None, description="最小7天销量"),
    min_gmv_7d: float | None = Query(None, description="最小7天销售额"),
    min_creator_conversion_rate: float | None = Query(None, description="最小达人出单率"),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        query = supabase.table("products").select("*")

        if keyword and keyword.strip():
            query = query.ilike("product_name", f"%{keyword.strip()}%")

        if region and region.strip():
            query = query.eq("region", region.strip())

        if category and category.strip():
            query = query.eq("category", category.strip())

        if product_status and product_status.strip():
            query = query.eq("product_status", product_status.strip())

        if min_sales_7d is not None:
            query = query.gte("sales_7d", min_sales_7d)

        if min_gmv_7d is not None:
            query = query.gte("gmv_7d", min_gmv_7d)

        if min_creator_conversion_rate is not None:
            query = query.gte("creator_conversion_rate", min_creator_conversion_rate)

        response = query.order("sales_7d", desc=True).limit(limit).execute()
        data = response.data or []

        return {
            "filters": {
                "keyword": keyword,
                "region": region,
                "category": category,
                "product_status": product_status,
                "min_sales_7d": min_sales_7d,
                "min_gmv_7d": min_gmv_7d,
                "min_creator_conversion_rate": min_creator_conversion_rate,
                "limit": limit,
            },
            "count": len(data),
            "items": data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/products/{product_id}", summary="Get product detail")
def get_product_detail(product_id: str):
    try:
        return get_product_by_id(supabase, product_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get product failed: {str(e)}")


@app.post("/products/{product_id}/analyze", summary="Generate AI analysis")
def generate_product_analysis(product_id: str, body: AnalyzeRequest):
    try:
        return analyze_product_with_llm(
            supabase=supabase,
            product_id=product_id,
            provider_name=body.provider,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")


@app.get("/products/{product_id}/analysis", summary="Get latest saved analysis")
def get_product_analysis(product_id: str):
    try:
        product = get_product_by_id(supabase, product_id)
        analysis = get_saved_analysis(supabase, product_id)

        return {
            "product_id": product_id,
            "product_name": product["product_name"],
            "analysis": analysis,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch analysis failed: {str(e)}")


@app.get("/products/{product_id}/report", summary="Get product report")
def get_report(product_id: str):
    try:
        return get_product_report(supabase, product_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch report failed: {str(e)}")


@app.get("/products/{product_id}/policy-analysis", summary="Get automatic product region policy analysis")
def get_product_policy_analysis(product_id: str, provider: str = Query("deepseek")):
    try:
        product = get_product_by_id(supabase, product_id)
        return generate_product_policy_analysis(
            supabase=supabase,
            product=product,
            provider_name=provider,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch product policy analysis failed: {str(e)}")


@app.get("/products/{product_id}/integrated-report", summary="Get integrated product + policy report")
def get_integrated_report(product_id: str, provider: str = Query("deepseek")):
    try:
        product = get_product_by_id(supabase, product_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Integrated report failed at product stage: {str(e)}"
        )

    try:
        analysis = get_saved_analysis(supabase, product_id)
    except Exception:
        analysis = None

    try:
        region = (product.get("region") or "").upper()
        summary_data = get_region_policy_summary(supabase, region) if region else None

        risk_text = "暂无明显政策风险"
        action_text = "建议先小范围测试，再根据投放和转化结果决定是否放量"
        policy_summary_text = "当前未发现该地区对该类目有明显高风险限制"

        if summary_data:
            restricted = summary_data.get("restricted_categories") or []
            overview = summary_data.get("overview") or ""

            category = (product.get("category") or "").strip()
            matched_risk = False

            for item in restricted:
                if category and category in item:
                    matched_risk = True
                    risk_text = f"{category} 类目可能涉及地区限制或额外合规要求"
                    policy_summary_text = f"{region} 市场对部分敏感类目存在限制，当前商品建议先做合规确认"
                    action_text = "建议先核查类目规则、标签要求与清关要求，再决定是否放量"
                    break

            if not matched_risk and overview:
                policy_summary_text = "当前地区政策层面未见明显高风险信号，可先按普通商品测试"

        policy_analysis = {
            "region": product.get("region"),
            "region_name": summary_data.get("region_name") if summary_data else (product.get("region") or "未知地区"),
            "policy_summary": policy_summary_text,
            "risk_points": risk_text,
            "action_suggestions": action_text,
        }

    except Exception:
        policy_analysis = {
            "region": product.get("region"),
            "region_name": product.get("region") or "未知地区",
            "policy_summary": "政策信息暂时无法完整获取，建议谨慎测试",
            "risk_points": "暂无明确风险结论",
            "action_suggestions": "建议先小批量测试，并复核当地政策要求",
        }

    try:
        report_text = build_integrated_report_text(
            product=product,
            analysis=analysis,
            policy_analysis=policy_analysis,
        )
    except Exception:
        report_text = "综合建议生成失败，请稍后重试。"

    return {
        "product": product,
        "analysis": analysis,
        "policy_analysis": policy_analysis,
        "report_text": report_text,
    }

# =========================
# 政策相关接口
# =========================

@app.get("/policy/{region}", summary="Get policy summary by region from Supabase")
def get_policy(region: str):
    try:
        return get_region_policy_summary(supabase, region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch region policy failed: {str(e)}")


@app.post("/policy/{region}/ask", summary="Ask policy question with retrieval + generation")
def ask_policy(region: str, body: PolicyAskRequest):
    try:
        return ask_policy_question(
            supabase=supabase,
            region=region,
            query=body.query,
            top_k=body.top_k,
            document_type=body.document_type,
            source_type=body.source_type,
            provider_name=body.provider,
            include_references=body.include_references,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ask policy question failed: {str(e)}")


@app.get("/policies/search", summary="Search policy documents")
def search_policies(
    region: str | None = Query(None, description="国家/地区"),
    keyword: str | None = Query(None, description="政策标题关键词"),
    document_type: str | None = Query(None, description="文档类型"),
    source_type: str | None = Query(None, description="来源类型"),
    status: str | None = Query("active", description="状态"),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        return search_policy_documents(
            supabase=supabase,
            region=region,
            keyword=keyword,
            document_type=document_type,
            source_type=source_type,
            status=status,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search policy documents failed: {str(e)}")


@app.get("/policies/{document_id}", summary="Get policy document by id")
def get_policy_document(document_id: str):
    try:
        return get_policy_document_by_id(supabase, document_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch policy document failed: {str(e)}")


@app.get("/policies/{document_id}/chunks", summary="Get chunks of a policy document")
def get_policy_document_chunks(document_id: str):
    try:
        chunks = get_policy_chunks_by_document_id(supabase, document_id)
        return {
            "document_id": document_id,
            "count": len(chunks),
            "items": chunks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch policy chunks failed: {str(e)}")


@app.post("/policies/import", summary="Create a policy document")
def import_policy_document(body: PolicyDocumentCreate):
    try:
        return create_policy_document(supabase, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create policy document failed: {str(e)}")


@app.post("/policies/{document_id}/process", summary="Chunk and embed a policy document")
def process_policy(document_id: str, body: PolicyProcessRequest):
    try:
        return process_policy_document(
            supabase=supabase,
            document_id=document_id,
            overwrite_existing_chunks=body.overwrite_existing_chunks,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process policy document failed: {str(e)}")


@app.get("/policy/{region}/retrieve", summary="Retrieve policy chunks by semantic search")
def retrieve_policy_chunks(
    region: str,
    query: str = Query(..., description="用户问题"),
    top_k: int = Query(6, ge=1, le=20),
    document_type: str | None = Query(None, description="文档类型"),
    source_type: str | None = Query(None, description="来源类型"),
):
    try:
        items = match_policy_chunks(
            supabase=supabase,
            query=query,
            region=region,
            top_k=top_k,
            document_type=document_type,
            source_type=source_type,
        )
        return {
            "region": region.upper(),
            "query": query,
            "count": len(items),
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieve policy chunks failed: {str(e)}")