import re
from typing import Any

from fastapi import HTTPException
from supabase import Client

from llm.factory import get_llm_provider
from schemas.policy import PolicyDocumentCreate
from utils.embeddings import embed_document_text, embed_query_text


def get_region_label(region: str | None) -> str:
    mapping = {
        "MY": "马来西亚",
        "ID": "印度尼西亚",
        "TH": "泰国",
        "PH": "菲律宾",
        "VN": "越南",
    }
    if not region:
        return "未知地区"
    return mapping.get(region.upper(), region.upper())


def create_policy_document(supabase: Client, payload: PolicyDocumentCreate) -> dict[str, Any]:
    data = payload.model_dump(mode="json")
    response = supabase.table("policy_documents").insert(data).execute()
    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=500, detail="Create policy document failed")
    return rows[0]


def search_policy_documents(
    supabase: Client,
    region: str | None = None,
    keyword: str | None = None,
    document_type: str | None = None,
    source_type: str | None = None,
    status: str | None = "active",
    limit: int = 50,
) -> dict[str, Any]:
    query = supabase.table("policy_documents").select("*")

    if region and region.strip():
        query = query.eq("region", region.strip().upper())

    if keyword and keyword.strip():
        query = query.ilike("title", f"%{keyword.strip()}%")

    if document_type and document_type.strip():
        query = query.eq("document_type", document_type.strip())

    if source_type and source_type.strip():
        query = query.eq("source_type", source_type.strip())

    if status and status.strip():
        query = query.eq("status", status.strip())

    response = query.order("publish_date", desc=True).limit(limit).execute()
    items = response.data or []
    return {"count": len(items), "items": items}


def get_policy_document_by_id(supabase: Client, document_id: str) -> dict[str, Any]:
    response = (
        supabase.table("policy_documents")
        .select("*")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Policy document not found")
    return rows[0]


def get_policy_chunks_by_document_id(supabase: Client, document_id: str) -> list[dict[str, Any]]:
    response = (
        supabase.table("policy_chunks")
        .select("*")
        .eq("document_id", document_id)
        .order("chunk_index")
        .execute()
    )
    return response.data or []


def delete_policy_chunks_by_document_id(supabase: Client, document_id: str) -> None:
    supabase.table("policy_chunks").delete().eq("document_id", document_id).execute()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_text_into_sections(raw_text: str) -> list[str]:
    raw_text = normalize_text(raw_text)
    if not raw_text:
        return []

    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    sections: list[str] = []
    max_chars = 900

    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            sections.append(paragraph)
            continue

        sentence_parts = re.split(r"(?<=[。！？.!?;；])", paragraph)
        buffer = ""

        for sent in sentence_parts:
            sent = sent.strip()
            if not sent:
                continue

            if len(buffer) + len(sent) <= max_chars:
                buffer += sent
            else:
                if buffer:
                    sections.append(buffer.strip())
                buffer = sent

        if buffer:
            sections.append(buffer.strip())

    return sections


def infer_section_title(chunk_text: str, default_index: int) -> str:
    first_line = chunk_text.split("\n")[0].strip()
    if len(first_line) <= 80:
        return first_line
    return f"Section {default_index + 1}"


def build_chunk_rows(document: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = document.get("raw_text")
    if not raw_text or not str(raw_text).strip():
        raise HTTPException(status_code=400, detail="Document raw_text is empty")

    sections = split_text_into_sections(raw_text)
    rows: list[dict[str, Any]] = []

    for idx, section in enumerate(sections):
        rows.append(
            {
                "document_id": document["id"],
                "region": document["region"],
                "chunk_index": idx,
                "section_title": infer_section_title(section, idx),
                "article_no": None,
                "content": section,
                "content_zh": None,
                "metadata": {
                    "source_name": document.get("source_name"),
                    "source_type": document.get("source_type"),
                    "document_type": document.get("document_type"),
                    "language": document.get("language"),
                    "publish_date": str(document.get("publish_date")) if document.get("publish_date") else None,
                    "effective_date": str(document.get("effective_date")) if document.get("effective_date") else None,
                    "category_scope": document.get("category_scope") or [],
                },
            }
        )

    return rows


def batch_insert_policy_chunks(
    supabase: Client,
    chunk_rows: list[dict[str, Any]],
    batch_size: int = 20,
) -> int:
    if not chunk_rows:
        return 0

    inserted = 0
    for i in range(0, len(chunk_rows), batch_size):
        batch = chunk_rows[i:i + batch_size]
        response = supabase.table("policy_chunks").insert(batch).execute()
        inserted += len(response.data or [])
    return inserted


def process_policy_document(
    supabase: Client,
    document_id: str,
    overwrite_existing_chunks: bool = False,
) -> dict[str, Any]:
    document = get_policy_document_by_id(supabase, document_id)
    existing_chunks = get_policy_chunks_by_document_id(supabase, document_id)

    if existing_chunks and not overwrite_existing_chunks:
        return {
            "document_id": document_id,
            "inserted_chunks": 0,
            "message": "Chunks already exist. Set overwrite_existing_chunks=true to rebuild.",
        }

    if overwrite_existing_chunks and existing_chunks:
        delete_policy_chunks_by_document_id(supabase, document_id)

    chunk_rows = build_chunk_rows(document)

    for row in chunk_rows:
        row["embedding"] = embed_document_text(row["content"])

    inserted = batch_insert_policy_chunks(supabase, chunk_rows)

    return {
        "document_id": document_id,
        "inserted_chunks": inserted,
        "message": "Policy document processed successfully",
    }


# =========================
# 检索优化：去重 / 关键词 / 章节聚合
# =========================

def normalize_chunk_text(text: str) -> str:
    text = text or ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def deduplicate_retrieved_chunks(
    items: list[dict[str, Any]],
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_doc_chunk: set[str] = set()
    seen_content: set[str] = set()

    for item in items:
        doc_id = str(item.get("document_id") or "")
        chunk_index = str(item.get("chunk_index") or "")
        doc_chunk_key = f"{doc_id}::{chunk_index}"

        content_key = normalize_chunk_text(item.get("content") or "")
        if not content_key:
            continue

        if doc_chunk_key in seen_doc_chunk:
            continue

        if content_key in seen_content:
            continue

        seen_doc_chunk.add(doc_chunk_key)
        seen_content.add(content_key)
        deduped.append(item)

        if max_items is not None and len(deduped) >= max_items:
            break

    return deduped


def deduplicate_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_doc_chunk: set[str] = set()
    seen_content: set[str] = set()

    for ref in references:
        doc_id = str(ref.get("document_id") or "")
        chunk_index = str(ref.get("chunk_index") or "")
        key = f"{doc_id}::{chunk_index}"

        content_key = normalize_chunk_text(ref.get("content") or "")
        if key in seen_doc_chunk:
            continue
        if content_key and content_key in seen_content:
            continue

        seen_doc_chunk.add(key)
        if content_key:
            seen_content.add(content_key)
        deduped.append(ref)

    return deduped


def get_chunk_by_doc_and_index(
    supabase: Client,
    document_id: str,
    chunk_index: int,
) -> dict[str, Any] | None:
    response = (
        supabase.table("policy_chunks")
        .select("*")
        .eq("document_id", document_id)
        .eq("chunk_index", chunk_index)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def detect_policy_mode(query: str) -> str | None:
    q = query.lower()

    if "invite-only" in q or "invite only" in q:
        return "invite-only"

    if "unsupported" in q or "不支持" in q:
        return "unsupported"

    if "restricted" in q or "受限" in q or "审批" in q:
        return "restricted"

    return None


def score_chunk_for_mode(chunk: dict[str, Any], mode: str | None) -> float:
    """
    对检索结果做轻量规则加权：
    - 命中 query 关键词的 chunk 加分
    - 只有定义/总述的 chunk 轻微降权
    """
    base = float(chunk.get("similarity") or 0.0)
    text = normalize_chunk_text(
        f"{chunk.get('section_title') or ''}\n{chunk.get('content') or ''}"
    )

    if not mode:
        return base

    bonus = 0.0

    if mode == "unsupported":
        if "unsupported" in text:
            bonus += 0.03
        if "following products are currently unsupported" in text:
            bonus += 0.03
        if "unsupported products" in text:
            bonus += 0.02

    elif mode == "restricted":
        if "restricted" in text:
            bonus += 0.03
        if "require prior approval" in text:
            bonus += 0.02
        if "product approval" in text:
            bonus += 0.02

    elif mode == "invite-only":
        if "invite-only" in text or "invite only" in text:
            bonus += 0.03
        if "qualification center" in text:
            bonus += 0.02

    # 纯定义块/总述块稍微降权
    definition_like = [
        "definitions",
        "all unsupported products are currently prohibited",
        "note that the approval documentation requirements may vary",
    ]
    if any(p in text for p in definition_like):
        bonus -= 0.01

    # 列表块/项目块加权
    list_like = [
        "- ",
        "•",
        "cars",
        "alcohol",
        "medical needles",
        "mystery boxes",
        "services",
        "sim cards",
        "formula milk",
        "health supplements",
        "streaming media devices",
    ]
    if any(p in text for p in list_like):
        bonus += 0.015

    return base + bonus


def is_heading_like(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False

    patterns = [
        r'^\d+(\.\d+)*\s+',
        r'^\*\*.+\*\*$',
        r'^[A-Z][A-Za-z0-9\s\-/()"]{0,80}$',
    ]
    return any(re.match(p, t) for p in patterns)


def collect_section_context(
    supabase: Client,
    seed_chunk: dict[str, Any],
    max_forward_chunks: int = 8,
    max_total_chars: int = 3500,
) -> list[dict[str, Any]]:
    """
    以命中的 chunk 为种子，向后按章节聚合：
    - 如果后续 chunk 还是同一章节内容/列表项，则继续收集
    - 遇到明显的新章节标题后停止
    """
    collected = [seed_chunk]

    document_id = seed_chunk.get("document_id")
    seed_index = seed_chunk.get("chunk_index")

    if document_id is None or seed_index is None:
        return collected

    seed_title = (seed_chunk.get("section_title") or "").strip()
    total_chars = len(seed_chunk.get("content") or "")

    for offset in range(1, max_forward_chunks + 1):
        next_chunk = get_chunk_by_doc_and_index(supabase, document_id, seed_index + offset)
        if not next_chunk:
            break

        next_title = (next_chunk.get("section_title") or "").strip()
        next_content = next_chunk.get("content") or ""
        normalized = normalize_chunk_text(f"{next_title}\n{next_content}")

        # 遇到明显的新大章节时停止
        if next_title and is_heading_like(next_title):
            if next_title != seed_title:
                if offset > 1:
                    break

        # 如果 chunk 明显是当前问题无关模式，则不继续
        # 这里只做轻量控制，避免一下跳到完全不相关章节
        if total_chars > max_total_chars:
            break

        collected.append(next_chunk)
        total_chars += len(next_content)

        # 如果已经拿到很多列表项，可提前停止
        if normalized.count("- ") >= 3 or normalized.count("\n- ") >= 2:
            if total_chars >= 1200:
                break

    return collected


def expand_chunks_by_section(
    supabase: Client,
    seed_chunks: list[dict[str, Any]],
    mode: str | None,
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []

    for item in seed_chunks:
        section_chunks = collect_section_context(
            supabase=supabase,
            seed_chunk=item,
            max_forward_chunks=8,
            max_total_chars=3500,
        )

        for ch in section_chunks:
            ch = {
                **ch,
                "similarity": score_chunk_for_mode(ch, mode),
            }
            expanded.append(ch)

    return deduplicate_retrieved_chunks(expanded)


def match_policy_chunks(
    supabase: Client,
    query: str,
    region: str,
    top_k: int = 6,
    document_type: str | None = None,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    query_embedding = embed_query_text(query)
    mode = detect_policy_mode(query)

    raw_fetch_count = max(top_k * 4, 16)

    response = supabase.rpc(
        "match_policy_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": raw_fetch_count,
            "filter_region": region.upper(),
            "filter_document_type": document_type,
            "filter_source_type": source_type,
        },
    ).execute()

    items = response.data or []
    items = deduplicate_retrieved_chunks(items)

    # 先对原始召回按模式重排
    for item in items:
        item["similarity"] = score_chunk_for_mode(item, mode)

    items = sorted(items, key=lambda x: float(x.get("similarity") or 0.0), reverse=True)

    # 只拿前几个种子做章节扩展
    seed_limit = min(max(top_k, 4), 6)
    seed_chunks = items[:seed_limit]

    # 章节扩展
    expanded_items = expand_chunks_by_section(
        supabase=supabase,
        seed_chunks=seed_chunks,
        mode=mode,
    )

    # 再排序
    expanded_items = sorted(
        expanded_items,
        key=lambda x: float(x.get("similarity") or 0.0),
        reverse=True,
    )

    # 最终上下文给多一点，尤其规则型问题需要更多列表项
    final_limit = max(top_k + 4, 10)
    final_limit = min(final_limit, 14)

    return deduplicate_retrieved_chunks(expanded_items, max_items=final_limit)


# =========================
# 地区摘要 / 问答 / 综合报告
# =========================

def get_region_policy_summary(supabase: Client, region: str) -> dict[str, Any]:
    region = region.upper()

    docs = (
        supabase.table("policy_documents")
        .select("id, region, title, source_name, source_type, document_type, summary, publish_date")
        .eq("region", region)
        .eq("status", "active")
        .order("publish_date", desc=True)
        .limit(20)
        .execute()
    ).data or []

    overview_parts = []
    for doc in docs[:5]:
        title = doc.get("title") or "未命名文档"
        source_name = doc.get("source_name") or "未知来源"
        summary = doc.get("summary") or ""
        overview_parts.append(f"{title}（来源：{source_name}）{summary}")

    overview = "\n".join(overview_parts) if overview_parts else "当前地区还没有导入政策文档。"

    platform_rules = []
    tax_and_customs = []
    restricted_categories = []

    for doc in docs:
        doc_type = (doc.get("document_type") or "").lower()
        title = doc.get("title") or ""

        if "platform" in doc_type or "rule" in doc_type:
            platform_rules.append(title)
        elif "tax" in doc_type or "customs" in doc_type:
            tax_and_customs.append(title)
        else:
            restricted_categories.append(title)

    return {
        "region": region,
        "region_name": get_region_label(region),
        "overview": overview,
        "platform_rules": platform_rules[:5],
        "tax_and_customs": tax_and_customs[:5],
        "restricted_categories": restricted_categories[:5],
        "ai_summary": (
            f"{get_region_label(region)}政策页面当前已接入 Supabase 文档库与 Gemini embedding 检索。"
            "后续可以继续接 DeepSeek 做政策摘要与综合报告生成。"
        ),
    }


def build_policy_answer_prompt(
    region: str,
    query: str,
    retrieved_chunks: list[dict[str, Any]],
) -> str:
    region_name = get_region_label(region)

    context_blocks: list[str] = []
    for idx, item in enumerate(retrieved_chunks, start=1):
        metadata = item.get("metadata") or {}
        source_name = metadata.get("source_name") or "未知来源"
        document_type = metadata.get("document_type") or "未知文档类型"
        source_type = metadata.get("source_type") or "未知来源类型"
        publish_date = metadata.get("publish_date") or "未知日期"
        section_title = item.get("section_title") or f"Section {item.get('chunk_index', idx)}"
        similarity = item.get("similarity")

        context_blocks.append(
            f"""[参考片段 {idx}]
来源名称: {source_name}
文档类型: {document_type}
来源类型: {source_type}
发布日期: {publish_date}
章节标题: {section_title}
相似度: {similarity}

正文:
{item.get("content", "")}
""".strip()
        )

    context_text = "\n\n".join(context_blocks)

    return f"""
你是一名跨境电商政策与合规解读助手。请基于给定的政策片段，回答用户问题。

要求：
1. 只根据参考片段回答，不要凭空补充没有依据的事实。
2. 如果片段中出现了具体商品、类目、限制类型（如 restricted / unsupported / invite-only），要尽量明确列出来。
3. 对“有哪些商品”这类问题，优先输出具体类目/商品示例，而不是只重复定义。
4. 如果参考片段仍然不足以给出完整清单，要明确说“以下为当前检索到的部分示例，并非完整清单”。
5. 先给一句话总结，再给详细解释。
6. 用中文回答，语言尽量清晰、业务化、容易理解。
7. 不要输出 markdown 代码块。
8. 输出格式严格如下：

SUMMARY: 这里写一句话总结
ANSWER: 这里写详细解读

目标国家/地区：{region_name}（{region.upper()}）
用户问题：{query}

参考片段如下：
{context_text}
""".strip()


def parse_policy_answer_text(text: str) -> dict[str, str]:
    summary = ""
    answer = ""

    if "SUMMARY:" in text and "ANSWER:" in text:
        summary_part = text.split("SUMMARY:", 1)[1]
        summary = summary_part.split("ANSWER:", 1)[0].strip()
        answer = summary_part.split("ANSWER:", 1)[1].strip()
    else:
        answer = text.strip()
        summary = "已基于检索到的政策片段生成解读。"

    return {
        "summary": summary or "已基于检索到的政策片段生成解读。",
        "answer": answer or text.strip(),
    }


def ask_policy_question(
    supabase: Client,
    region: str,
    query: str,
    top_k: int = 3,
    document_type: str | None = None,
    source_type: str | None = None,
    provider_name: str = "deepseek",
    include_references: bool = True,
) -> dict[str, Any]:
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")

    retrieved_chunks = match_policy_chunks(
        supabase=supabase,
        query=query.strip(),
        region=region.upper(),
        top_k=top_k,
        document_type=document_type,
        source_type=source_type,
    )

    if not retrieved_chunks:
        return {
            "region": region.upper(),
            "region_name": get_region_label(region),
            "query": query,
            "summary": "当前没有检索到相关政策片段。",
            "answer": "当前知识库中没有召回到与该问题直接相关的政策内容，建议补充该国家/类目的政策文档后再试。",
            "references": [],
        }

    prompt = build_policy_answer_prompt(
        region=region.upper(),
        query=query.strip(),
        retrieved_chunks=retrieved_chunks,
    )

    provider = get_llm_provider(provider_name)

    if not hasattr(provider, "client") or not hasattr(provider, "model"):
        raise HTTPException(status_code=500, detail="Selected provider does not support policy QA generation")

    response = provider.client.chat.completions.create(
        model=provider.model,
        temperature=0.15,
        messages=[
            {
                "role": "system",
                "content": "你是一名跨境电商政策与合规解读助手，必须基于给定资料回答问题。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content or ""
    parsed = parse_policy_answer_text(content)

    references: list[dict[str, Any]] = []
    if include_references:
        for item in retrieved_chunks:
            metadata = item.get("metadata") or {}
            references.append(
                {
                    "document_id": item.get("document_id"),
                    "chunk_id": item.get("id"),
                    "chunk_index": item.get("chunk_index"),
                    "section_title": item.get("section_title"),
                    "similarity": item.get("similarity"),
                    "content": item.get("content"),
                    "source_name": metadata.get("source_name"),
                    "document_type": metadata.get("document_type"),
                    "source_type": metadata.get("source_type"),
                    "publish_date": metadata.get("publish_date"),
                }
            )

    references = deduplicate_references(references)

    return {
        "region": region.upper(),
        "region_name": get_region_label(region),
        "query": query,
        "summary": parsed["summary"],
        "answer": parsed["answer"],
        "references": references,
    }


def build_auto_policy_questions_for_product(product: dict[str, Any]) -> list[str]:
    region = get_region_label(product.get("region"))
    category = product.get("category") or "该类商品"
    product_name = product.get("product_name_zh") or product.get("product_name") or "该商品"

    return [
        f"在{region}销售{category}类商品，需要重点注意哪些政策、标签或合规要求？",
        f"{product_name}这类商品在{region}市场的主要政策或平台规则风险是什么？",
        f"如果卖家想在{region}测试{category}类商品，前期应优先准备什么？",
    ]


def generate_product_policy_analysis(
    supabase: Client,
    product: dict[str, Any],
    provider_name: str = "deepseek",
) -> dict[str, Any]:
    region = product.get("region")
    if not region:
        return {
            "region": None,
            "region_name": "未知地区",
            "questions": [],
            "policy_summary": "当前商品缺少地区信息，无法生成地区政策分析。",
            "risk_points": "暂无。",
            "action_suggestions": "请先补充商品地区信息。",
            "references": [],
        }

    questions = build_auto_policy_questions_for_product(product)
    answers = []
    all_refs: list[dict[str, Any]] = []

    for q in questions:
        result = ask_policy_question(
            supabase=supabase,
            region=region,
            query=q,
            top_k=3,
            provider_name=provider_name,
            include_references=True,
        )
        answers.append(result)
        all_refs.extend(result.get("references", []))

    all_refs = deduplicate_references(all_refs)

    policy_summary = answers[0]["answer"] if len(answers) > 0 else "暂无政策概览。"
    risk_points = answers[1]["answer"] if len(answers) > 1 else "暂无主要风险。"
    action_suggestions = answers[2]["answer"] if len(answers) > 2 else "暂无操作建议。"

    return {
        "region": region,
        "region_name": get_region_label(region),
        "questions": questions,
        "policy_summary": policy_summary,
        "risk_points": risk_points,
        "action_suggestions": action_suggestions,
        "references": all_refs,
    }


def build_integrated_report_text(
    product: dict[str, Any],
    analysis: dict[str, Any] | None,
    policy_analysis: dict[str, Any],
) -> str:
    product_name = product.get("product_name_zh") or product.get("product_name") or "该商品"
    region_name = policy_analysis.get("region_name") or product.get("region") or "该地区"
    category = product.get("category") or "该类目"

    recommendation = (analysis or {}).get("recommendation") or product.get("recommendation_label") or "观察"
    summary = (analysis or {}).get("summary") or "当前暂无 AI 详细分析结论。"
    why_hot = (analysis or {}).get("why_hot") or "暂无明确增长原因分析。"
    risks = (analysis or {}).get("risks") or "暂无明显经营风险提示。"
    test_plan = (analysis or {}).get("test_plan") or "建议先做小批量测试。"

    policy_summary = policy_analysis.get("policy_summary") or ""
    risk_points = policy_analysis.get("risk_points") or ""
    action_suggestions = policy_analysis.get("action_suggestions") or ""

    policy_judgement = "当前未发现明显政策风险"
    policy_action = "可按常规商品测试流程推进"

    combined_policy_text = f"{policy_summary} {risk_points}".strip()

    risk_keywords = [
        "禁止", "禁售", "限制", "违规", "风险", "资质", "许可证", "申报",
        "清关", "税务", "标签", "认证", "医疗", "保健", "儿童", "食品", "化妆品"
    ]
    if any(k in combined_policy_text for k in risk_keywords):
        policy_judgement = "该类目在当地市场可能涉及一定合规要求，需先确认后再放量"
        policy_action = action_suggestions or "建议先核查平台规则、标签要求和清关/税务要求，再开始测试"

    lines = [
        f"结论：{recommendation}",
        "",
        f"{product_name} 在 {region_name} 的 {category} 类目下，整体判断为“{recommendation}”。",
        f"核心原因：{summary}",
        f"机会判断：{why_hot}",
        f"政策判断：{policy_judgement}。",
        f"经营风险：{risks}",
        f"建议动作：{policy_action}。",
        f"测试建议：{test_plan}",
    ]

    return "\n".join(lines)