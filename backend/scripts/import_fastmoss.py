import math
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from os import getenv
from supabase import create_client, Client


load_dotenv()

SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


INPUT_FILE = r"C:\Users\Administrator\backend\data\商品搜索_商品数据_20260318_142015.xlsx"
SHEET_NAME = "FastMoss"


def parse_price(value):
    if pd.isna(value):
        return None
    s = str(value).strip()
    s = re.sub(r"[^\d.,]", "", s)

    # 处理类似 Rp25,800
    if s.count(",") > 0 and s.count(".") == 0:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")

    # 处理 1,122,333.55
    if s.count(",") > 0 and s.count(".") > 0:
        s = s.replace(",", "")

    try:
        return float(s)
    except:
        return None


def parse_percent(value):
    if pd.isna(value):
        return None
    s = str(value).strip().replace("%", "").replace(",", "")
    try:
        return float(s)
    except:
        return None


def parse_number(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    s = str(value).strip()
    s = s.replace(",", "")
    try:
        if "." in s:
            return float(s)
        return int(s)
    except:
        return None


def clean_text(value):
    if pd.isna(value):
        return None
    s = str(value).strip()
    return s if s else None


def to_record(row):
    sales_7d = parse_number(row.get("7天销量"))
    gmv_7d = parse_number(row.get("7天销售额"))
    total_sales = parse_number(row.get("总销量"))
    total_gmv = parse_number(row.get("总销售额"))
    creator_total = parse_number(row.get("带货达人总数"))
    creator_conversion_rate = parse_percent(row.get("达人出单率"))
    video_total = parse_number(row.get("带货视频总数"))
    live_total = parse_number(row.get("带货直播总数"))

    # 简单评分逻辑，可后续再优化
    trend_score = min((sales_7d or 0) / 2000 * 100, 100)
    content_score = min(((video_total or 0) + (live_total or 0)) / 2000 * 100, 100)
    competition_score = min((creator_total or 0) / 50, 100)
    risk_score = 100 - min((creator_conversion_rate or 0), 100)
    opportunity_score = round(
        trend_score * 0.35
        + content_score * 0.25
        + competition_score * 0.20
        + (100 - risk_score) * 0.20,
        2,
    )

    if opportunity_score >= 75:
        recommendation_label = "推荐"
    elif opportunity_score >= 55:
        recommendation_label = "谨慎测试"
    else:
        recommendation_label = "不推荐"

    return {
        "product_name": clean_text(row.get("商品名称")),
        "product_status": clean_text(row.get("商品状态")),
        "shop_name": clean_text(row.get("店铺名称")),
        "region": clean_text(row.get("国家/地区")),
        "category": clean_text(row.get("商品分类")),
        "price": parse_price(row.get("售价")),
        "commission_rate": parse_percent(row.get("佣金比例")),
        "sales_7d": int(sales_7d) if sales_7d is not None else None,
        "gmv_7d": float(gmv_7d) if gmv_7d is not None else None,
        "total_sales": int(total_sales) if total_sales is not None else None,
        "total_gmv": float(total_gmv) if total_gmv is not None else None,
        "creator_total": int(creator_total) if creator_total is not None else None,
        "creator_conversion_rate": float(creator_conversion_rate) if creator_conversion_rate is not None else None,
        "video_total": int(video_total) if video_total is not None else None,
        "live_total": int(live_total) if live_total is not None else None,
        "product_image_url": clean_text(row.get("商品图片")),
        "fastmoss_product_url": clean_text(row.get("FastMoss商品详情页地址")),
        "tiktok_product_url": clean_text(row.get("TikTok商品落地页地址")),
        "fastmoss_shop_url": clean_text(row.get("FastMoss店铺详情页地址")),
        "estimated_listing_time": clean_text(row.get("预估商品上架时间")),
        "recent_performance": f"近7天销量 {sales_7d or 0}，近7天销售额 {gmv_7d or 0}",
        "trend_score": round(trend_score, 2),
        "content_score": round(content_score, 2),
        "competition_score": round(competition_score, 2),
        "risk_score": round(risk_score, 2),
        "opportunity_score": opportunity_score,
        "recommendation_label": recommendation_label,
        # 兼容旧字段
        "sales": int(total_sales) if total_sales is not None else None,
        "gmv": float(total_gmv) if total_gmv is not None else None,
        "growth_rate": None,
        "creator_count": int(creator_total) if creator_total is not None else None,
        "shop_count": None,
        "video_count": int(video_total) if video_total is not None else None,
        "ad_count": None,
    }


def main():
    file_path = Path(INPUT_FILE)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    df = pd.read_excel(file_path, sheet_name=SHEET_NAME)
    df = df.loc[:, ~df.columns.isna()]
    df = df.dropna(how="all")

    records = []
    for _, row in df.iterrows():
        record = to_record(row)
        if record["product_name"]:
            records.append(record)

    print(f"准备导入 {len(records)} 条商品数据")

    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        response = supabase.table("products").insert(batch).execute()
        print(f"已导入 {i + len(batch)} / {len(records)}")

    print("导入完成")


if __name__ == "__main__":
    main()