# Cross-border E-commerce AI Product Decision Copilot

一个面向跨境电商卖家的 **AI 选品决策 Copilot**。  
它不仅帮助用户看商品数据，还进一步结合 **地区政策 / 平台规则 / 合规风险**，生成更完整的综合决策建议。

当前 MVP 重点聚焦 **马来西亚（MY）市场**，验证从：

**商品搜索 → 商品分析 → 政策解读 → 综合报告** 的完整闭环。

---

## Project Overview

在跨境电商选品过程中，商家通常会看到很多结构化数据，例如：

- 商品销量
- 销售额
- 达人带货表现
- 店铺信息
- 视频与直播数据

但“看数据”不等于“做决策”。

一个商品值不值得做，不仅取决于销量和热度，还要综合考虑：

- 这个品有没有持续机会
- 适合什么类型的卖家进入
- 应该从什么卖点切入
- 存在哪些竞争与内容风险
- 目标地区是否有政策 / 平台 / 标签 / 清关方面的限制

本项目希望解决的就是这个问题：

> 把商品数据、AI 商品分析和地区政策分析结合起来，帮助卖家更快做出跨境选品判断。

---

## Current MVP Scope

当前版本主要验证以下能力：

- 基于商品结构化数据进行搜索和详情展示
- 基于 LLM 生成 AI 商品分析
- 基于政策文档知识库做地区政策解读
- 支持 AI 政策问答
- 将商品分析和政策分析合并成综合选品报告

当前重点地区：

- **MY / 马来西亚**

---

## Core Features
### 0. 全流程演示
<img width="1800" height="7663" alt="ecom_copilot_flow_showcase_v3" src="https://github.com/user-attachments/assets/63c0d01a-53be-40ff-8ad1-7867c11c082e" />

### 1. 商品搜索与筛选
用户可以按国家/地区、类目、商品状态和关键词搜索候选商品。

### 2. 商品详情页
展示商品的核心经营指标，例如：

- 价格
- 7天销量
- 7天销售额
- 总销量 / 总销售额
- 达人数 / 达人出单率
- 视频总数 / 直播总数

### 3. AI 商品分析
基于商品结构化数据生成：

- 一句话结论
- 为什么能卖
- 机会类型
- 适合什么卖家
- 建议切入卖点
- 风险提示
- 测试计划
- 最终建议

### 4. 国家政策解读
用户可以进入指定国家/地区的政策页面，查看：

- 平台规则重点
- 税务 / 清关要点
- 禁限售 / 高风险类目
- AI 政策问答

### 5. 政策知识库 + RAG
后端支持：

- 政策文档导入
- 文档切分
- embedding 入库
- 向量检索
- 检索增强生成（RAG）

当前已接入部分 **MY 市场**的真实政策/平台规则文档，用于政策问答与综合报告生成。

### 6. 综合选品报告
将：

- AI 选品分析
- 地区政策 / 合规分析

整合成一个更适合业务判断的综合报告页面。

---

## Product Flow

### 用户路径

1. 在首页搜索候选商品  
2. 进入搜索结果页查看候选商品  
3. 进入商品详情页查看核心经营指标  
4. 生成 AI 商品分析  
5. 查看目标地区政策解读  
6. 最终生成综合选品报告  

---

## Tech Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide Icons

### Backend
- FastAPI
- Python

### Database / Storage
- Supabase

### AI / LLM
- DeepSeek
- Gemini

### Embedding / Retrieval
- Gemini Embedding
- policy_documents / policy_chunks
- 向量检索 + 检索增强生成（RAG）

---

## Repository Structure

```text
.
├─ frontend/         # Next.js 前端
├─ backend/          # FastAPI 后端
├─ docs/
│  └─ images/        # 页面截图
├─ README.md
└─ .gitignore
