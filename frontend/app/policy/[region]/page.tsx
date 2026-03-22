"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, FileWarning, Globe2, ShieldAlert, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { apiUrl } from "@/lib/api";

type PolicySummaryResponse = {
  region: string;
  region_name: string;
  overview: string;
  platform_rules: string[];
  tax_and_customs: string[];
  restricted_categories: string[];
  ai_summary: string;
};

type PolicyAskReference = {
  document_id: string;
  chunk_id: string;
  chunk_index: number;
  section_title: string | null;
  similarity: number;
  content: string;
  source_name: string | null;
  document_type: string | null;
  source_type: string | null;
  publish_date: string | null;
};

type PolicyAskResponse = {
  region: string;
  region_name: string;
  query: string;
  summary: string;
  answer: string;
  references: PolicyAskReference[];
};

const CURATED_MY_RISK = [
  "平台不支持：汽车整车与部分汽配、酒精、婴儿配方奶、二手商品、虚拟商品、服务、盲盒、活体动物等。",
  "Invite-only：汽车电池及配件、配方奶/母婴部分品类、药品与医疗器械、保健补充剂、贵金属、部分二手商品、SIM 卡、TV Box 等。",
  "Restricted：如 Streaming Media Devices（TV Box）等需要先完成资质审批后才能卖。",
  "美妆个护重点：避免医疗/治疗功效宣称，标签、成分、用途说明要清晰。",
];

export default function PolicyPage() {
  const params = useParams();
  const router = useRouter();
  const region = params.region as string;

  const [summaryData, setSummaryData] = useState<PolicySummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const [askResult, setAskResult] = useState<PolicyAskResponse | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        setError("");

        const res = await fetch(apiUrl(`/policy/${region}`));
        if (!res.ok) throw new Error("获取政策页面失败");

        const json: PolicySummaryResponse = await res.json();
        setSummaryData(json);
      } catch {
        setError("获取政策摘要失败，请检查后端或地区参数。");
      } finally {
        setLoading(false);
      }
    };

    if (region) fetchSummary();
  }, [region]);

  const handleAsk = async () => {
    if (!question.trim()) {
      setAskError("请输入问题");
      return;
    }

    try {
      setAsking(true);
      setAskError("");
      setAskResult(null);

      const res = await fetch(apiUrl(`/policy/${region}/ask`), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question.trim(),
          top_k: 3,
          provider: "deepseek",
          include_references: true,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "政策问答失败");
      }

      const json: PolicyAskResponse = await res.json();
      setAskResult(json);
    } catch {
      setAskError("政策问答失败，请检查后端日志或模型配置。");
    } finally {
      setAsking(false);
    }
  };

  const curatedRiskList = useMemo(() => {
    if ((summaryData?.region || "").toUpperCase() === "MY") return CURATED_MY_RISK;
    return summaryData?.restricted_categories?.length ? summaryData.restricted_categories : ["暂无结构化禁限售摘要"];
  }, [summaryData]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              {summaryData ? `${summaryData.region_name} 政策解读` : "地区政策解读"}
            </h1>
            <p className="mt-2 text-slate-600">查看平台规则、税务清关提示，并直接提问政策 / 合规问题</p>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => router.push("/")} className="rounded-2xl">
              返回首页
            </Button>
            <Button variant="outline" onClick={() => router.back()} className="rounded-2xl">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回上一页
            </Button>
          </div>
        </div>

        {loading && (
          <Card className="rounded-[28px]">
            <CardContent className="py-8 text-slate-600">正在加载政策页面...</CardContent>
          </Card>
        )}

        {error && (
          <Card className="rounded-[28px] border-red-200">
            <CardContent className="py-8 text-red-600">{error}</CardContent>
          </Card>
        )}

        {!loading && !error && summaryData && (
          <>
            <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
              <Card className="rounded-[28px] border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Globe2 className="h-5 w-5" />
                    平台规则重点
                  </CardTitle>
                  <CardDescription>更适合快速浏览，而不是堆整段概述</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(summaryData.platform_rules || []).map((item, index) => (
                    <SimpleListCard key={index} text={item} />
                  ))}
                </CardContent>
              </Card>

              <Card className="rounded-[28px] border-slate-200 shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Truck className="h-5 w-5" />
                    税务 / 清关要点
                  </CardTitle>
                  <CardDescription>适合跨境物流、申报和税务判断</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(summaryData.tax_and_customs || []).length ? (
                    summaryData.tax_and_customs.map((item, index) => (
                      <SimpleListCard key={index} text={item} />
                    ))
                  ) : (
                    <div className="rounded-2xl border bg-white p-4 text-sm text-slate-500">暂无数据</div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card className="rounded-[28px] border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <FileWarning className="h-5 w-5" />
                  禁限售 / 高风险类目
                </CardTitle>
                <CardDescription>
                  直接显示更有用的结构化提示，而不是仅仅显示“暂无数据”
                </CardDescription>
              </CardHeader>

              <CardContent className="grid gap-4 md:grid-cols-2">
                {curatedRiskList.map((item, index) => (
                  <div key={index} className="rounded-2xl border bg-white p-4">
                    <div className="flex gap-3">
                      <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600" />
                      <div className="text-sm leading-7 text-slate-800">{item}</div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="rounded-[28px] border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <ShieldAlert className="h-5 w-5" />
                  AI 政策问答
                </CardTitle>
                <CardDescription>
                  直接提问该地区的政策、平台规则、标签、禁限售、合规风险等问题
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-5">
                <div className="flex flex-col gap-3 md:flex-row">
                  <Input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleAsk();
                    }}
                    placeholder={`例如：${summaryData.region_name}卖护肤品需要注意什么？`}
                    className="h-12 rounded-2xl bg-white text-base"
                  />
                  <Button onClick={handleAsk} disabled={asking} className="h-12 rounded-2xl px-7 text-base">
                    {asking ? "解读中..." : "AI 解读"}
                  </Button>
                </div>

                {askError && (
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                    {askError}
                  </div>
                )}

                {askResult && (
                  <div className="space-y-4">
                    <SectionBlock title="一句话总结" content={askResult.summary} />
                    <SectionBlock title="详细解读" content={askResult.answer} />
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}

function SimpleListCard({ text }: { text: string }) {
  return <div className="rounded-2xl border bg-white p-4 text-sm leading-7 text-slate-800">{text}</div>;
}

function SectionBlock({ title, content }: { title: string; content: string }) {
  return (
    <div className="rounded-[24px] border bg-white p-5">
      <div className="mb-2 text-sm font-medium text-slate-500">{title}</div>
      <div className="whitespace-pre-wrap text-sm leading-7 text-slate-900">{content || "-"}</div>
    </div>
  );
}