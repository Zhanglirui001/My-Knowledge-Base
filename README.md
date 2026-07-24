# My Knowledge Base

这是一个基于本地文件夹、Markdown、Git、MOC、卡片盒笔记法和本地 Agent 自动化的个人知识库。

目标不是把资料“存起来”，而是把零散信息逐步加工成可检索、可复用、可持续迭代的知识资产。

## 快速入口

- [知识库总览 MOC](./50_MOCs/知识库总览%20MOC.md)
- [技术学习 MOC](./50_MOCs/技术学习%20MOC.md)
- [工作项目 MOC](./50_MOCs/工作项目%20MOC.md)
- [自动索引 MOC](./50_MOCs/自动索引%20MOC.md)
- [标签规范](./90_System/标签规范.md)
- [每周维护流程](./90_System/每周维护流程.md)
- [自动化使用说明](./90_System/自动化使用说明.md)
- [本地知识库 Agent 使用说明](./90_System/Agent使用说明.md)

## 目录结构

```text
00_Inbox/                临时收集箱，所有未处理内容先放这里
10_Projects/             有明确目标和结束时间的项目
20_Areas/                长期维护的领域、责任区和主题首页
30_Resources/            PDF、书籍、论文、代码、drawio、网页剪藏等原始资料
40_Notes/                原子笔记、永久笔记、卡片盒核心区
50_MOCs/                 内容地图，用来组织路径、主题和索引
60_Outputs/              文章、报告、方案、课件、总结等输出物
90_Archive/              已完成、过期或暂不维护的内容
90_System/               模板、规范、维护流程、Agent 报告
_assets/                 图片、附件、drawio 导出图等资源
scripts/                 自动化脚本
```

## 使用原则

1. 文件夹管理生命周期：资料处在收集、项目、领域、沉淀、输出还是归档阶段。
2. 标签管理横向关系：主题、类型、状态、用途都用标签连接。
3. MOC 管理导航路径：每个重要主题都应该能从 MOC 找到入口。
4. 卡片管理可复用知识：一张卡片只表达一个清晰概念、方法、经验或问题。
5. Agent 做重复劳动：识别、归档、建索引、生成草案、检索、体检和建议连接。

## 基础自动化

```powershell
python scripts/kb.py new-note "标题" --tags "知识管理,方法" --moc "知识管理 MOC"
python scripts/kb.py ingest-inbox
python scripts/kb.py audit
python scripts/kb.py update-index
```

## 本地 Agent

```powershell
python scripts/kb_agent.py ingest
python scripts/kb_agent.py ingest --apply --drafts
python scripts/kb_agent.py build-index
python scripts/kb_agent.py ask "我关于 RAG 的资料有哪些，还缺什么？"
python scripts/kb_agent.py outline "RAG" --kind roadmap
python scripts/kb_agent.py health
```

默认策略：预览优先，写入需要 `--apply`。Agent 生成的阅读笔记都是 `draft`，需要人工复核。

## 日常流程

```text
收集 -> Agent 预览 -> 人工确认 -> 自动归档/草案 -> 人工提炼 -> MOC 输出 -> 复盘
```

1. 任何新材料先进入 `00_Inbox/`。
2. 用 `python scripts/kb_agent.py ingest` 预览处理结果。
3. 确认后用 `python scripts/kb_agent.py ingest --apply --drafts` 归档并生成草案。
4. 用 `python scripts/kb_agent.py ask "主题问题"` 检索已有资料和缺口。
5. 用 `python scripts/kb_agent.py outline "主题" --kind report` 生成输出草案。
6. 每周运行 `python scripts/kb_agent.py health` 生成健康报告。

## 新笔记从哪里开始

- 临时记录：使用 [Inbox 模板](./90_System/Templates/Inbox模板.md)
- 原子笔记：使用 [原子笔记模板](./90_System/Templates/原子笔记模板.md)
- MOC：使用 [MOC 模板](./90_System/Templates/MOC模板.md)
- 资料索引：使用 [资料索引模板](./90_System/Templates/资料索引模板.md)
