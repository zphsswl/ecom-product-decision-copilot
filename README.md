# Ecom Product Decision Copilot

一个基于 FastMoss 导出数据的跨境电商 AI 选品决策助手，用于将商品数据从“看数据”升级为“做决策”。

## Project Overview

FastMoss 可以帮助商家看到商品、达人、店铺和内容表现数据，但它本质上解决的是“数据查看”问题。

本项目希望进一步解决一个更实际的业务问题：

**面对一批商品数据，商家如何快速判断这个品值不值得做、风险在哪、适合谁做、应该如何切入。**

因此，这个项目尝试构建一个真正可用的 **AI 选品决策 Copilot**，将结构化商品数据转化为：

- 商品机会评分
- 风险提示
- 入场建议
- 卖点建议
- 测试策略建议

## Project Value

这个项目的核心价值不在于“再做一个数据面板”，而在于：

1. **把数据转化为决策**
   - 不只是展示 GMV、销量、增速等指标
   - 而是进一步输出“推荐 / 谨慎测试 / 不推荐”的决策结果

2. **降低选品分析门槛**
   - 帮助中小商家快速理解商品机会
   - 减少纯人工看表、做判断的时间成本

3. **补足 FastMoss 的决策层能力**
   - FastMoss 更偏数据洞察
   - 本项目更偏“基于数据给出行动建议”

4. **形成 AI 产品化能力**
   - 结合规则评分与 LLM 分析
   - 输出更像真实业务助手的选品建议报告

## Core Features

当前 MVP 计划包含以下能力：

- CSV 上传与商品数据导入
- 商品列表页与基础指标展示
- 规则驱动的机会评分
- AI 生成商品分析结论
- 风险识别与卖点建议
- 商品级选品决策报告输出

## Target Users

本项目主要面向以下用户：

- 跨境电商卖家
- TikTok Shop / 内容电商商家
- 需要做选品分析的运营人员
- 希望提升选品效率的中小团队

## MVP Scope

第一阶段只聚焦“单商品选品分析”，不做过大的系统扩展。

### Included
- 基于 FastMoss 导出 CSV 的商品数据分析
- 商品机会评分
- AI 选品建议生成
- 商品详情页与报告页

### Not Included Yet
- 实时 FastMoss API 对接
- 自动爬虫
- 多租户与权限系统
- 大规模 BI 图表系统
- 多模型路由与复杂 Agent 编排

## Tech Stack

Planned stack:

- **Frontend:** Next.js + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI
- **Database:** Supabase / PostgreSQL
- **AI Layer:** OpenAI API
- **Data Processing:** pandas

## Workflow

The planned workflow is:

1. Upload FastMoss-exported CSV
2. Parse and clean structured product data
3. Generate rule-based opportunity scores
4. Call LLM for product analysis and decision suggestions
5. Show results in product list / detail / report pages

## Current Status

This project is currently in early MVP building stage.

Current progress:
- [x] Repository initialized
- [x] Project direction defined
- [ ] Frontend project setup
- [ ] Backend API setup
- [ ] Database schema setup
- [ ] CSV upload pipeline
- [ ] Opportunity scoring
- [ ] AI analysis pipeline
- [ ] Report generation

## Future Plans

- Add product comparison
- Add comment/review summarization
- Add prompt evaluation and bad case analysis
- Deploy a demo version
- Improve scoring strategy with more business signals

## Author Note

This project is built as an AI product / data product MVP focused on real cross-border e-commerce selection workflows.

It is also intended as a portfolio project demonstrating:
- AI product thinking
- data-to-decision workflow design
- MVP scoping ability
- practical LLM application design
