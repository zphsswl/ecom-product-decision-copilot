"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  BadgeDollarSign,
  BarChart3,
  Clapperboard,
  Package2,
  Radio,
  ShieldAlert,
  Sparkles,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { apiUrl } from "@/lib/api";

type Product = {
  id: string;
  product_name: string;
  product_status: string | null;
  shop_name: string | null;
  region: string | null;
  category: string | null;
  price: number | null;
  commission_rate: number | null;
  sales_7d: number | null;
  gmv_7d: number | null;
  total_sales: number | null;
  total_gmv: number | null;
  creator_total: number | null;
  creator_conversion_rate: number | null;
  video_total: number | null;
  live_total: number | null;
  estimated_listing_time: string | null;
  opportunity_score: number | null;
  trend_score: number | null;
  competition_score: number | null;
  content_score: number | null;
  risk_score: number | null;
  recommendation_label: string | null;
  product_name_zh: string | null;
  shop_name_zh: string | null;
};

type Analysis = {
  id: string;
  product_id: string;
  summary: string;
  why_hot: string;
  opportunity_type: string;
  target_seller: string;
  selling_points: string;
  risks: string;
  test_plan: string;
  recommendation: string;
  created_at: string;
};

type AnalysisResponse = {
  product_id: string;
  product_name: string;
  analysis: Analysis | null;
};

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);

  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const [error, setError] = useState("");
  const [analysisError, setAnalysisError] = useState("");

  useEffect(() => {
    const fetchProduct = async () => {
      if (!id) {
        setLoading(false);
        setError("缺少商品ID");
        return;
      }

      try {
        setLoading(true);
        setError("");
        const res = await fetch(apiUrl(`/products/${id}`));
        if (!res.ok) throw new Error("获取商品详情失败");
        const json: Product = await res.json();
        setProduct(json);
      } catch {
        setError("获取商品详情失败，请检查后端是否启动或商品是否存在");
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!id) return;

      try {
        setAnalysisError("");
        const res = await fetch(apiUrl(`/products/${id}/analysis`));
        if (!res.ok) {
          setAnalysis(null);
          return;
        }
        const json: AnalysisResponse = await res.json();
        setAnalysis(json.analysis || null);
      } catch {
        setAnalysis(null);
      }
    };

    fetchAnalysis();
  }, [id]);

  const handleAnalyze = async () => {
    if (!id) return;

    try {
      setAnalysisLoading(true);
      setAnalysisError("");

      const res = await fetch(apiUrl(`/products/${id}/analyze`), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          provider: "deepseek",
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "生成分析失败");
      }

      const newAnalysis: Analysis = await res.json();
      setAnalysis(newAnalysis);
    } catch {
      setAnalysisError("AI 分析生成失败，请检查后端日志、模型配置或接口权限");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const scoreBars = useMemo(() => {
    if (!product) return [];
    return [
      { label: "机会", value: product.opportunity_score ?? 0 },
      { label: "趋势", value: product.trend_score ?? 0 },
      { label: "竞争", value: product.competition_score ?? 0 },
      { label: "内容", value: product.content_score ?? 0 },
      { label: "风险", value: product.risk_score ?? 0 },
    ];
  }, [product]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">商品详情</h1>
            <p className="mt-2 text-slate-600">查看核心经营数据、AI 判断和综合报告入口</p>
          </div>
          <Button variant="outline" onClick={() => router.back()} className="rounded-2xl">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
        </div>

        {loading && (
          <Card className="rounded-[28px]">
            <CardContent className="py-8 text-slate-600">正在加载商品详情...</CardContent>
          </Card>
        )}

        {error && (
          <Card className="rounded-[28px] border-red-200">
            <CardContent className="py-8 text-red-600">{error}</CardContent>
          </Card>
        )}

        {!loading && !error && product && (
          <>
            <Card className="rounded-[28px] border-slate-200 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-3">
                    <CardTitle className="text-[34px] leading-tight">{product.product_name}</CardTitle>
                    {product.product_name_zh && (
                      <div className="text-lg text-slate-500">中文：{product.product_name_zh}</div>
                    )}
                    <div className="flex flex-wrap gap-3 text-sm text-slate-500">
                      <MetaPill icon={<Package2 className="h-4 w-4" />} text={`${product.region || "未知地区"} / ${product.category || "未分类"}`} />
                      <MetaPill icon={<Store className="h-4 w-4" />} text={product.shop_name || "未知店铺"} />
                    </div>
                    {product.shop_name_zh && (
                      <div className="text-sm text-slate-500">店铺中文：{product.shop_name_zh}</div>
                    )}
                  </div>

                  <div className="inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
                    {product.recommendation_label || "观察"}
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <MetricCard icon={<BadgeDollarSign className="h-4 w-4" />} label="售价" value={product.price ?? "-"} />
                  <MetricCard icon={<BadgeDollarSign className="h-4 w-4" />} label="佣金比例" value={formatPercent(product.commission_rate)} />
                  <MetricCard icon={<TrendingUp className="h-4 w-4" />} label="7天销量" value={formatNumber(product.sales_7d)} />
                  <MetricCard icon={<TrendingUp className="h-4 w-4" />} label="7天销售额" value={formatNumber(product.gmv_7d)} />
                  <MetricCard icon={<BarChart3 className="h-4 w-4" />} label="总销量" value={formatNumber(product.total_sales)} />
                  <MetricCard icon={<BarChart3 className="h-4 w-4" />} label="总销售额" value={formatNumber(product.total_gmv)} />
                  <MetricCard icon={<Users className="h-4 w-4" />} label="达人总数" value={formatNumber(product.creator_total)} />
                  <MetricCard icon={<Users className="h-4 w-4" />} label="达人出单率" value={formatPercent(product.creator_conversion_rate)} />
                  <MetricCard icon={<Clapperboard className="h-4 w-4" />} label="视频总数" value={formatNumber(product.video_total)} />
                  <MetricCard icon={<Radio className="h-4 w-4" />} label="直播总数" value={formatNumber(product.live_total)} />
                  <MetricCard icon={<Package2 className="h-4 w-4" />} label="商品状态" value={product.product_status || "-"} />
                  <MetricCard icon={<Package2 className="h-4 w-4" />} label="上架时间" value={formatDateTime(product.estimated_listing_time)} />
                </div>

                <div className="rounded-[24px] border bg-white p-5">
                  <div className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-900">
                    <BarChart3 className="h-5 w-5" />
                    核心指标速览
                  </div>
                  <div className="grid gap-4 md:grid-cols-5">
                    {scoreBars.map((item) => (
                      <ScoreBar key={item.label} label={item.label} value={item.value} />
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-slate-200 shadow-sm">
              <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-2xl">
                    <Sparkles className="h-5 w-5 text-slate-700" />
                    AI 分析结果
                  </CardTitle>
                  <CardDescription className="text-base">
                    由结构化商品数据生成的机会判断、执行建议与风险提示
                  </CardDescription>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button variant="outline" onClick={() => router.push(`/policy/${product.region || "MY"}`)} className="rounded-2xl">
                    查看地区政策
                  </Button>
                  <Button variant="outline" onClick={() => router.push(`/reports/${id}`)} className="rounded-2xl">
                    查看综合报告
                  </Button>
                  <Button onClick={handleAnalyze} disabled={analysisLoading} className="rounded-2xl">
                    {analysisLoading ? "生成中..." : analysis ? "重新生成分析" : "生成 AI 分析"}
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="space-y-5">
                {analysisError && (
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                    {analysisError}
                  </div>
                )}

                {!analysis && !analysisLoading && !analysisError && (
                  <div className="rounded-2xl border bg-white p-5 text-slate-500">当前还没有 AI 分析结果。</div>
                )}

                {analysis && (
                  <>
                    <div className="grid gap-4 lg:grid-cols-3">
                      <InsightCard title="一句话结论" content={analysis.summary} />
                      <InsightCard title="机会类型" content={analysis.opportunity_type} />
                      <InsightCard title="最终建议" content={analysis.recommendation} />
                    </div>

                    <div className="grid gap-4 lg:grid-cols-2">
                      <InsightCard title="为什么能卖" content={analysis.why_hot} />
                      <InsightCard title="适合什么卖家" content={analysis.target_seller} />
                      <InsightCard title="建议切入卖点" content={analysis.selling_points} />
                      <InsightCard title="测试计划" content={analysis.test_plan} />
                    </div>

                    <div className="rounded-[24px] border border-amber-200 bg-amber-50 p-5">
                      <div className="mb-2 flex items-center gap-2 text-base font-semibold text-amber-900">
                        <ShieldAlert className="h-5 w-5" />
                        主要风险
                      </div>
                      <div className="whitespace-pre-wrap text-sm leading-7 text-amber-900">{analysis.risks || "-"}</div>
                    </div>

                    <div className="text-xs text-slate-400">
                      最近生成时间：{formatDateTime(analysis.created_at)}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-[24px] border bg-white p-5">
      <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
        {icon}
        {label}
      </div>
      <div className="text-xl font-semibold text-slate-900 break-words">{value}</div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const safe = Math.max(0, Math.min(100, Number(value || 0)));
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
        <span>{label}</span>
        <span className="font-medium text-slate-900">{safe}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-200">
        <div className="h-2 rounded-full bg-slate-900" style={{ width: `${safe}%` }} />
      </div>
    </div>
  );
}

function InsightCard({ title, content }: { title: string; content: string }) {
  return (
    <div className="rounded-[24px] border bg-white p-5">
      <div className="mb-2 text-sm font-medium text-slate-500">{title}</div>
      <div className="whitespace-pre-wrap text-sm leading-7 text-slate-900">{content || "-"}</div>
    </div>
  );
}

function MetaPill({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border bg-white px-3 py-1.5">
      {icon}
      {text}
    </span>
  );
}

function formatPercent(value: number | null) {
  if (value === null || value === undefined) return "-";
  return `${value}%`;
}

function formatNumber(value: number | null) {
  if (value === null || value === undefined) return "-";
  return String(value);
}

function formatDateTime(value: string | null) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString("zh-CN");
  } catch {
    return value;
  }
}