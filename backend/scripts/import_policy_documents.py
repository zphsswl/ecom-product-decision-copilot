from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
from supabase import Client, create_client

from schemas.policy import PolicyDocumentCreate
from services.policy_service import (
    create_policy_document,
    get_policy_chunks_by_document_id,
    process_policy_document,
)

load_dotenv()

SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DOWNLOAD_DIR = Path(r"C:\Users\Administrator\Downloads")


def read_markdown_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        texts.append(text)
    return "\n\n".join(texts).strip()


def find_existing_document(region: str, title: str) -> dict | None:
    response = (
        supabase.table("policy_documents")
        .select("*")
        .eq("region", region)
        .eq("title", title)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def import_or_get_document(
    *,
    file_path: Path,
    region: str,
    title: str,
    source_name: str,
    source_type: str,
    document_type: str,
    language: str,
    summary: str,
    category_scope: list[str],
) -> dict:
    existing = find_existing_document(region=region, title=title)
    if existing:
        print(f"文档已存在，跳过创建: {existing['id']} | {title}")
        return existing

    suffix = file_path.suffix.lower()

    if suffix == ".md":
        raw_text = read_markdown_file(file_path)
    elif suffix == ".pdf":
        raw_text = read_pdf_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    payload = PolicyDocumentCreate(
        region=region,
        title=title,
        source_url=str(file_path),
        source_name=source_name,
        source_type=source_type,
        document_type=document_type,
        language=language,
        version="v1",
        status="active",
        category_scope=category_scope,
        summary=summary,
        raw_text=raw_text,
        metadata={
            "import_method": "local_file",
            "local_path": str(file_path),
        },
    )

    created = create_policy_document(supabase, payload)
    print(f"文档创建成功: {created['id']} | {title}")
    return created


def process_if_needed(document_id: str, title: str):
    existing_chunks = get_policy_chunks_by_document_id(supabase, document_id)
    if existing_chunks:
        print(f"chunks 已存在，跳过切分: {document_id} | {title} | chunks={len(existing_chunks)}")
        print("-" * 80)
        return

    result = process_policy_document(
        supabase=supabase,
        document_id=document_id,
        overwrite_existing_chunks=False,
    )
    print("切分完成:", result)
    print("-" * 80)


def match_one_file(pattern: str, description: str) -> Path:
    candidates = list(DOWNLOAD_DIR.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"在 Downloads 目录下没有找到 {description}，匹配模式: {pattern}")
    if len(candidates) > 1:
        print(f"警告：{description} 匹配到多个文件，默认取第一个：")
        for c in candidates:
            print(" -", c.name)
    return candidates[0]


def main():
    print("Downloads 目录下文件如下：")
    for p in DOWNLOAD_DIR.iterdir():
        print("-", p.name)
    print("=" * 80)

    # 1) TikTok Shop Prohibited Products Guidelines
    prohibited_md = match_one_file(
        "TikTok Shop Prohibited Products Guidelines*.md",
        "TikTok Shop Prohibited Products Guidelines 的 md 文件",
    )
    print("匹配到文件：", prohibited_md.name)

    doc1 = import_or_get_document(
        file_path=prohibited_md,
        region="MY",
        title="TikTok Shop Prohibited Products Guidelines (MY Reference)",
        source_name="TikTok Shop",
        source_type="platform",
        document_type="platform_rule",
        language="en",
        summary="TikTok Shop 禁售商品规则，用于马来西亚市场政策/平台风险检索。",
        category_scope=["美妆个护", "食品饮料", "保健", "宠物用品", "通用"],
    )
    process_if_needed(doc1["id"], doc1["title"])

    # 2) Sales Tax LVG Guide PDF
    lvg_pdf = match_one_file(
        "*LVG*.pdf",
        "包含 LVG 的 PDF 文件",
    )
    print("匹配到文件：", lvg_pdf.name)

    doc2 = import_or_get_document(
        file_path=lvg_pdf,
        region="MY",
        title="Guide on Sales Tax for LVG (Malaysia, 1 August 2024)",
        source_name="Malaysia Tax / Customs Guide",
        source_type="tax",
        document_type="tax_guide",
        language="en",
        summary="马来西亚低价商品销售税（LVG）相关指南，用于税务/清关风险检索。",
        category_scope=["通用", "跨境电商", "税务"],
    )
    process_if_needed(doc2["id"], doc2["title"])

    # 3) TikTok Shop Restricted and Unsupported Products Guidelines
    restricted_md = match_one_file(
        "TikTok Shop Restricted and Unsupported Products Guidelines*.md",
        "TikTok Shop Restricted and Unsupported Products Guidelines 的 md 文件",
    )
    print("匹配到文件：", restricted_md.name)

    doc3 = import_or_get_document(
        file_path=restricted_md,
        region="MY",
        title="TikTok Shop Restricted and Unsupported Products Guidelines (MY Reference)",
        source_name="TikTok Shop",
        source_type="platform",
        document_type="platform_rule",
        language="en",
        summary="TikTok Shop 限制类、邀请制和不支持销售商品规则，用于马来西亚市场平台风险与限制类目检索。",
        category_scope=["美妆个护", "食品饮料", "保健", "汽车用品", "母婴", "宠物用品", "通用"],
    )
    process_if_needed(doc3["id"], doc3["title"])


if __name__ == "__main__":
    main()