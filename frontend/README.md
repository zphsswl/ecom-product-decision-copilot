# Frontend - Ecom Product Decision Copilot

这是项目的前端部分，基于 **Next.js + TypeScript + Tailwind CSS + shadcn/ui** 构建。

## 主要页面

- 首页：商品搜索与国家政策入口
- 搜索结果页：候选商品列表与推荐标签
- 商品详情页：核心经营指标 + AI 商品分析
- 政策解读页：地区政策摘要 + AI 政策问答
- 综合选品报告页：商品分析 + 地区政策分析 + 综合建议

## 技术栈

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide Icons

## 本地启动

```bash
*前端
npm install
npm run dev -- --hostname 0.0.0.0

*后端
uvicorn main:app --reload
