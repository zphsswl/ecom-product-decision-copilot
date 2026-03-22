"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Globe2, Sparkles, ShieldAlert, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const REGIONS = ["", "MY", "ID", "TH", "PH", "VN"];
const CATEGORIES = ["", "美妆个护", "宠物用品", "居家日用", "服饰鞋包", "食品饮料", "电脑办公", "穆斯林时尚"];
const STATUS_LIST = ["", "在售", "下架"];

const REGION_LABEL: Record<string, string> = {
  MY: "马来西亚",
  ID: "印度尼西亚",
  TH: "泰国",
  PH: "菲律宾",
  VN: "越南",
};

export default function HomePage() {
  const router = useRouter();

  const [keyword, setKeyword] = useState("");
  const [region, setRegion] = useState("");
  const [category, setCategory] = useState("");
  const [productStatus, setProductStatus] = useState("");
  const [policyRegion, setPolicyRegion] = useState("");

  const effectivePolicyRegion = useMemo(() => policyRegion || region, [policyRegion, region]);

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (keyword.trim()) params.set("keyword", keyword.trim());
    if (region) params.set("region", region);
    if (category) params.set("category", category);
    if (productStatus) params.set("product_status", productStatus);
    router.push(`/results?${params.toString()}`);
  };

  const handlePolicyEnter = () => {
    if (!effectivePolicyRegion) return;
    router.push(`/policy/${effectivePolicyRegion}`);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="rounded-[28px] border border-slate-200 bg-white px-8 py-10 shadow-sm">
          <div className="max-w-5xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">
              <Sparkles className="h-4 w-4" />
              跨境电商选品 + 政策风险辅助决策
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-slate-900 md:text-6xl">
              跨境电商 AI 选品决策 Copilot
            </h1>

            <p className="mt-4 max-w-4xl text-lg leading-8 text-slate-600">
              从商品搜索、机会分析，到地区政策/平台风险解读，再到综合报告输出，
              帮你更快判断一个品值不值得做、该怎么切入、有哪些合规风险。
            </p>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
              <FeaturePill icon={<Search className="h-4 w-4" />} text="搜索候选商品" />
              <FeaturePill icon={<Sparkles className="h-4 w-4" />} text="生成 AI 选品分析" />
              <FeaturePill icon={<ShieldAlert className="h-4 w-4" />} text="结合地区政策输出综合报告" />
            </div>
          </div>
        </section>

        <Card className="rounded-[28px] border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Search className="h-6 w-6 text-slate-700" />
              商品搜索与筛选
            </CardTitle>
            <CardDescription className="text-base">
              保留最核心的搜索入口：先选地区、类目、商品状态，再输入关键词即可快速找品。
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="grid gap-4 md:grid-cols-3">
              <FilterSelect label="国家/地区" value={region} onChange={setRegion} options={REGIONS} />
              <FilterSelect label="商品分类" value={category} onChange={setCategory} options={CATEGORIES} />
              <FilterSelect label="商品状态" value={productStatus} onChange={setProductStatus} options={STATUS_LIST} />
            </div>

            <div className="flex flex-col gap-3 md:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSearch();
                  }}
                  placeholder="请输入商品名称或关键词，例如：soap / blender / pet food"
                  className="h-12 rounded-2xl bg-white pl-11 text-base"
                />
              </div>

              <Button onClick={handleSearch} className="h-12 rounded-2xl px-7 text-base">
                开始搜索
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Globe2 className="h-6 w-6 text-slate-700" />
              国家政策解读
            </CardTitle>
            <CardDescription className="text-base">
              查看当地跨境电商政策、平台规则、税务/清关提示，并直接进入 AI 政策问答页面。
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
              <div>
                <div className="mb-2 text-sm font-medium text-slate-700">国家/地区</div>
                <select
                  value={effectivePolicyRegion}
                  onChange={(e) => setPolicyRegion(e.target.value)}
                  className="h-12 w-full rounded-2xl border bg-white px-4 text-sm"
                >
                  <option value="">请选择国家/地区</option>
                  {REGIONS.filter(Boolean).map((code) => (
                    <option key={code} value={code}>
                      {code} · {REGION_LABEL[code] || code}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end">
                <Button
                  onClick={handlePolicyEnter}
                  disabled={!effectivePolicyRegion}
                  className="h-12 w-full rounded-2xl text-base"
                >
                  进入政策解读
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="rounded-2xl border border-dashed bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-600">
              提示：如果你上面的“商品搜索与筛选”里已经选了国家，这里也可以直接进入对应国家的政策页面。
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div>
      <div className="mb-2 text-sm font-medium text-slate-700">{label}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-12 w-full rounded-2xl border bg-white px-4 text-sm"
      >
        {options.map((option) => (
          <option key={option || "all"} value={option}>
            {option || "不限"}
          </option>
        ))}
      </select>
    </div>
  );
}

function FeaturePill({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-2xl border bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
      {icon}
      {text}
    </div>
  );
}