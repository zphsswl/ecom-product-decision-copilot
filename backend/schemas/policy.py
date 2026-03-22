from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class PolicyDocumentCreate(BaseModel):
    region: str = Field(..., description="国家/地区代码，如 MY / ID / TH / PH / VN")
    title: str = Field(..., description="政策文档标题")
    source_url: str | None = Field(None, description="来源链接")
    source_name: str | None = Field(None, description="来源名称")
    source_type: str | None = Field(
        None,
        description="来源类型，如 government / platform / customs / tax / logistics",
    )
    document_type: str | None = Field(
        None,
        description="文档类型，如 law / notice / platform_rule / faq / guide",
    )
    language: str | None = Field("en", description="文档语言")
    publish_date: date | None = Field(None, description="发布日期")
    effective_date: date | None = Field(None, description="生效日期")
    version: str | None = Field(None, description="版本号")
    status: str | None = Field("active", description="状态，如 active / archived")
    category_scope: list[str] = Field(default_factory=list, description="适用品类")
    summary: str | None = Field(None, description="摘要")
    raw_text: str | None = Field(None, description="原始正文文本")
    metadata: dict[str, Any] = Field(default_factory=dict, description="附加元数据")


class PolicyDocumentResponse(BaseModel):
    id: str
    region: str
    title: str
    source_url: str | None = None
    source_name: str | None = None
    source_type: str | None = None
    document_type: str | None = None
    language: str | None = None
    publish_date: date | None = None
    effective_date: date | None = None
    version: str | None = None
    status: str | None = None
    category_scope: list[str] = Field(default_factory=list)
    summary: str | None = None
    raw_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PolicyChunkResponse(BaseModel):
    id: str
    document_id: str
    region: str
    chunk_index: int
    section_title: str | None = None
    article_no: str | None = None
    content: str
    content_zh: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PolicySearchResponse(BaseModel):
    count: int
    items: list[PolicyDocumentResponse]


class PolicyChunkSearchResult(BaseModel):
    id: str
    document_id: str
    region: str
    chunk_index: int
    section_title: str | None = None
    article_no: str | None = None
    content: str
    content_zh: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity: float


class PolicyProcessRequest(BaseModel):
    overwrite_existing_chunks: bool = False


class PolicyAskRequest(BaseModel):
    query: str = Field(..., description="用户关于政策/合规的问题")
    top_k: int = Field(3, ge=1, le=10, description="召回多少个 chunks")
    document_type: str | None = Field(None, description="可选，按文档类型过滤")
    source_type: str | None = Field(None, description="可选，按来源类型过滤")
    provider: str = Field("deepseek", description="用于生成答案的 LLM provider")
    include_references: bool = Field(True, description="是否返回引用片段")


class PolicyAskReference(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    section_title: str | None = None
    similarity: float
    content: str
    source_name: str | None = None
    document_type: str | None = None
    source_type: str | None = None
    publish_date: str | None = None


class PolicyAskResponse(BaseModel):
    region: str
    region_name: str
    query: str
    summary: str
    answer: str
    references: list[PolicyAskReference] = Field(default_factory=list)