"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Search,
  MapPin,
  Store,
  Package2,
  TrendingUp,
  Users,
  PlaySquare,
  Radio,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { apiUrl } from "@/lib/api";

const REGIONS = ["", "MY", "ID", "TH", "PH", "VN"];
const CATEGORIES = ["", "美妆个护", "宠物用品", "居家日用", "服饰鞋包", "食品饮料", "电脑办公", "穆斯林时尚"];
const STATUS_LIST = ["", "在售", "下架"];

type Product = {
  id: string;
  product_name: string;
  product_name_zh: string | null;
  product_status: string | null;
  shop_name: string | null;
  shop_name_zh: string | null;
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
  opportunity_score: number | null;
  recommendation_label: string | null;
};

type SearchResponse = {
  count: number;
  items: Product[];
};

export default function ResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [keyword, setKeyword] = useState(searchParams.get("keyword") || "");
  const [region, setRegion] = useState(searchParams.get("region") || "");
  const [category, setCategory] = useState(searchParams.get("category") || "");
  const [productStatus, setProductStatus] = useState(searchParams.get("product_status") || "");

  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (keyword.trim()) params.set("keyword", keyword.trim());
    if (region) params.set("region", region);
    if (category) params.set("category", category);
    if (productStatus) params.set("product_status", productStatus);
    return params.toString();
  }, [keyword, region, category, productStatus]);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError("");

        const url = apiUrl(`/products/search?${queryString}`);
        console.log("请求地址:", url);
        console.log("当前页面地址:", window.location.href);
        console.log("当前 origin:", window.location.origin);

        const res = await fetch(url, {
          method: "GET",
        });

        console.log("响应状态:", res.status, res.statusText);

        const rawText = await res.text();
        console.log("原始返回文本:", rawText);

        if (!res.ok) {
          throw new Error(`请求失败: ${res.status} ${rawText}`);
        }

        const json: SearchResponse = JSON.parse(rawText);
        console.log("解析后的 JSON:", json);

        setData(json);
      } catch (err) {
        console.error("搜索结果抓取失败:", err);
        setError("获取搜索结果失败，请检查浏览器控制台日志");
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [queryString]);

  const handleSearch = () => {
    router.push(`/results?${queryString}`);
  };

  const handleBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
    } else {
      router.push("/");
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <Card className="rounded-[28px] border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-2xl">商品搜索结果</CardTitle>
                <CardDescription>
                  调整筛选条件后可重新搜索，推荐标签已统一为固定胶囊样式
                </CardDescription>
              </div>

              <Button
                type="button"
                variant="outline"
                className="rounded-2xl"
                onClick={handleBack}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                返回
              </Button>
            </div>
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
                  placeholder="请输入商品名称或关键词"
                  className="h-12 rounded-2xl bg-white pl-11 text-base"
                />
              </div>

              <Button onClick={handleSearch} className="h-12 rounded-2xl px-7 text-base">
                重新搜索
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-between px-1">
          <div className="text-sm text-slate-600">
            {loading ? "正在加载..." : `共找到 ${data?.count ?? 0} 个商品`}
          </div>
        </div>

        {error && (
          <Card className="rounded-[28px] border-red-200">
            <CardContent className="py-8 text-red-600">{error}</CardContent>
          </Card>
        )}

        {loading ? (
          <Card className="rounded-[28px]">
            <CardContent className="py-8 text-slate-600">正在加载搜索结果...</CardContent>
          </Card>
        ) : (
          <div className="space-y-5">
            {data?.items?.map((item) => (
              <ProductResultCard
                key={item.id}
                item={item}
                onDetail={() => router.push(`/products/${item.id}`)}
              />
            ))}

            {!data?.items?.length && !error && (
              <Card className="rounded-[28px]">
                <CardContent className="py-10 text-center text-slate-500">
                  没有找到符合条件的商品，试试放宽关键词或切换类目。
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

function ProductResultCard({
  item,
  onDetail,
}: {
  item: Product;
  onDetail: () => void;
}) {
  return (
    <Card className="rounded-[28px] border-slate-200 shadow-sm transition hover:shadow-md">
      <CardContent className="p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="text-[30px] font-semibold leading-tight text-slate-900">
              {item.product_name}
            </div>
            {item.product_name_zh && (
              <div className="text-base text-slate-500">中文：{item.product_name_zh}</div>
            )}
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {item.region || "未知地区"}
              </span>
              <span className="inline-flex items-center gap-1">
                <Package2 className="h-4 w-4" />
                {item.category || "未分类"}
              </span>
              <span className="inline-flex items-center gap-1">
                <Store className="h-4 w-4" />
                {item.shop_name || "未知店铺"}
              </span>
            </div>
            {item.shop_name_zh && (
              <div className="text-sm text-slate-500">店铺中文：{item.shop_name_zh}</div>
            )}
          </div>

          <RecommendationBadge label={item.recommendation_label} />
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <MetricMini icon={<TrendingUp className="h-4 w-4" />} label="7天销量" value={formatNumber(item.sales_7d)} />
          <MetricMini icon={<TrendingUp className="h-4 w-4" />} label="7天销售额" value={formatNumber(item.gmv_7d)} />
          <MetricMini icon={<Users className="h-4 w-4" />} label="达人总数" value={formatNumber(item.creator_total)} />
          <MetricMini icon={<Users className="h-4 w-4" />} label="达人出单率" value={formatPercent(item.creator_conversion_rate)} />
          <MetricMini icon={<PlaySquare className="h-4 w-4" />} label="视频总数" value={formatNumber(item.video_total)} />
          <MetricMini icon={<Radio className="h-4 w-4" />} label="直播总数" value={formatNumber(item.live_total)} />
          <MetricMini icon={<Package2 className="h-4 w-4" />} label="售价" value={item.price ?? "-"} />
          <MetricMini icon={<Package2 className="h-4 w-4" />} label="佣金比例" value={formatPercent(item.commission_rate)} />
        </div>

        <div className="mt-5 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            机会评分：<span className="font-medium text-slate-900">{item.opportunity_score ?? "-"}</span> · 商品状态：
            <span className="font-medium text-slate-900"> {item.product_status || "-"}</span>
          </div>

          <Button onClick={onDetail} className="rounded-2xl px-5">
            查看详情
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RecommendationBadge({ label }: { label: string | null }) {
  const text = label || "观察";
  const styleMap: Record<string, string> = {
    推荐: "bg-emerald-900 text-white",
    谨慎测试: "bg-amber-900 text-white",
    不推荐: "bg-slate-800 text-white",
    观察: "bg-slate-800 text-white",
  };

  return (
    <div
      className={`inline-flex min-w-[92px] justify-center rounded-full px-4 py-2 text-sm font-semibold shadow-sm ${styleMap[text] || styleMap["观察"]}`}
    >
      {text}
    </div>
  );
}

function MetricMini({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl border bg-white p-4">
      <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
        {icon}
        {label}
      </div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
    </div>
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

function formatPercent(value: number | null) {
  if (value === null || value === undefined) return "-";
  return `${value}%`;
}

function formatNumber(value: number | null) {
  if (value === null || value === undefined) return "-";
  return String(value);
}