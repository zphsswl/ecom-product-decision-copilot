"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, BadgeDollarSign, TrendingUp, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

type Product = {
  id: string;
  product_name: string;
  product_name_zh: string | null;
  region: string | null;
  category: string | null;
  price: number | null;
  sales_7d: number | null;
  gmv_7d: number | null;
  recommendation_label: string | null;
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
} | null;

type PolicyAnalysis = {
  region: string | null;
  region_name: string;
  policy_summary: string;
  risk_points: string;
  action_suggestions: string;
};

type IntegratedReportResponse = {
  product: Product;
  analysis: Analysis;
  policy_analysis: PolicyAnalysis;
  report_text: string;
};

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [report, setReport] = useState<IntegratedReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchedRef = useRef(false);

  useEffect(() => {
    if (!id || fetchedRef.current) return;
    fetchedRef.current = true;

    const fetchReport = async () => {
      try {
        setLoading(true);
        setError("");

        const url = `http://127.0.0.1:8000/products/${id}/integrated-report?provider=deepseek`;
        console.log("report fetch url =", url);

        const res = await fetch(url, {
          method: "GET",
          cache: "no-store",
        });

        console.log("report status =", res.status, res.statusText);

        const rawText = await res.text();
        console.log("report rawText =", rawText);

        if (!res.ok) {
          throw new Error(rawText || "获取综合报告失败");
        }

        const json: IntegratedReportResponse = JSON.parse(rawText);
        console.log("report json =", json);

        setReport(json);
      } catch (err) {
        console.error("综合报告抓取失败:", err);
        setError(`获取综合报告失败：${err instanceof Error ? err.message : "未知错误"}`);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [id]);

  const decisionTag = useMemo(() => {
    const label = report?.analysis?.recommendation || report?.product?.recommendation_label || "观察";
    const map: Record<string, string> = {
      推荐: "bg-emerald-900 text-white",
      谨慎测试: "bg-amber-900 text-white",
      不推荐: "bg-slate-800 text-white",
      观察: "bg-slate-800 text-white",
    };
    return { text: label, cls: map[label] || map["观察"] };
  }, [report]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">综合选品报告</h1>
            <p className="mt-2 text-slate-600">商品机会分析 + 地区政策/合规分析 + 综合建议</p>
          </div>

          <Button variant="outline" onClick={() => router.back()} className="rounded-2xl">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
        </div>

        {loading && (
          <Card className="rounded-[28px]">
            <CardContent className="py-8 text-slate-600">正在加载综合报告...</CardContent>
          </Card>
        )}

        {!!error && (
          <Card className="rounded-[28px] border-red-200">
            <CardContent className="py-8 text-red-600">{error}</CardContent>
          </Card>
        )}

        {!loading && !error && !report && (
          <Card className="rounded-[28px] border-amber-200">
            <CardContent className="py-8 text-amber-700">
              综合报告暂无数据。请打开浏览器控制台查看 report fetch 日志。
            </CardContent>
          </Card>
        )}

        {!loading && !error && report && (
  <>
    <Card className="rounded-[28px] border-slate-200 shadow-sm">
      <CardHeader>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle className="text-[34px] leading-tight">
              {report.product.product_name_zh || report.product.product_name}
            </CardTitle>
            <CardDescription className="mt-3 text-base">
              地区：{report.policy_analysis.region_name || report.product.region || "未知"} / 类目：{report.product.category || "未分类"}
            </CardDescription>
          </div>

          <div className={`inline-flex rounded-full px-4 py-2 text-sm font-semibold shadow-sm ${decisionTag.cls}`}>
            {decisionTag.text}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard
            icon={<BadgeDollarSign className="h-4 w-4" />}
            label="价格"
            value={report.product.price ?? "-"}
          />
          <MetricCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="7天销量"
            value={formatNumber(report.product.sales_7d)}
          />
          <MetricCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="7天销售额"
            value={formatNumber(report.product.gmv_7d)}
          />
        </div>
      </CardContent>
    </Card>

    <Card className="rounded-[28px] border-slate-200 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <CheckCircle2 className="h-5 w-5" />
          综合决策建议
        </CardTitle>
        <CardDescription>
          已融合 AI 选品判断与地区政策风险，帮助你快速决定这个商品值不值得做
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="rounded-[24px] border bg-white p-6">
          <div className="whitespace-pre-wrap text-[15px] leading-8 text-slate-800">
            {report.report_text || "-"}
          </div>
        </div>
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
      <div className="text-xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function ReportBlock({ title, content }: { title: string; content: string }) {
  return (
    <div className="rounded-[24px] border bg-white p-5">
      <div className="mb-2 text-sm font-medium text-slate-500">{title}</div>
      <div className="whitespace-pre-wrap text-sm leading-7 text-slate-900">{content || "-"}</div>
    </div>
  );
}

function formatNumber(value: number | null) {
  if (value === null || value === undefined) return "-";
  return String(value);
}