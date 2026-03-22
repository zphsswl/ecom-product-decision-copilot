from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    provider: str | None = None


class AnalysisResult(BaseModel):
    summary: str
    why_hot: str
    opportunity_type: str
    target_seller: str
    selling_points: str
    risks: str
    test_plan: str
    recommendation: str