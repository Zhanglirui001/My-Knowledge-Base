---
type: system
status: active
tags:
  - 知识管理
  - Agent
  - 自动化
---

# 本地知识库 Agent 使用说明

入口：

```powershell
python scripts/kb_agent.py <command>
```

这一版是本地 Agent v0，默认不联网，不调用外部大模型。它使用规则、文本抽取、关键词统计、SQLite FTS5 检索和草案生成来完成自动化。

## 能力边界

已实现：

- 识别 Inbox 里的 PDF、代码、drawio、图片等文件。
- 自动归档资源并生成资料索引。
- 为 PDF、代码、drawio 生成阅读笔记草案。
- 抽取 PDF 文本：如果本机安装了 `pypdf` 或 `PyPDF2`。
- 抽取 drawio 图中文字标签。
- 分析代码文本并生成模式/问题草案。
- 构建本地 SQLite FTS5 检索索引。
- 基于检索回答“已有资料有哪些、缺什么”。
- 生成主题学习路线、报告大纲、文章大纲。
- 生成双链建议报告。
- 生成 Agent 健康报告。

暂未做：

- 自动写回 `related` 双链。
- 自动替你把草案提升为 evergreen 笔记。
- 真正向量 embedding 检索。
- 联网或外部 LLM 摘要。

这些能力后续可以作为第二阶段增强，但建议继续保留人工确认。

## 1. Agent 摄取 Inbox

预览：

```powershell
python scripts/kb_agent.py ingest
```

执行归档、建索引、生成阅读笔记草案：

```powershell
python scripts/kb_agent.py ingest --apply --drafts
```

输出报告：

```text
90_System/Agent/Agent摄取报告.md
```

## 2. 构建检索索引

```powershell
python scripts/kb_agent.py build-index
```

索引文件：

```text
90_System/Agent/kb_search.sqlite3
```

## 3. 检索知识库

```powershell
python scripts/kb_agent.py search "RAG 向量检索"
```

## 4. 主题问答

```powershell
python scripts/kb_agent.py ask "我关于 RAG 的资料有哪些，还缺什么？"
```

输出报告：

```text
90_System/Agent/问答记录.md
```

## 5. 生成学习路线、报告或文章大纲

```powershell
python scripts/kb_agent.py outline "RAG" --kind roadmap
python scripts/kb_agent.py outline "RAG" --kind report
python scripts/kb_agent.py outline "RAG" --kind article
```

输出位置：

```text
60_Outputs/
```

## 6. 双链建议

```powershell
python scripts/kb_agent.py suggest-links
```

输出报告：

```text
90_System/Agent/双链建议.md
```

## 7. 健康报告

```powershell
python scripts/kb_agent.py health
```

会刷新：

- `90_System/知识库体检报告.md`
- `90_System/Agent/双链建议.md`
- `90_System/Agent/kb_search.sqlite3`
- `90_System/Agent/Agent健康报告.md`

## 推荐周流程

```powershell
python scripts/kb_agent.py ingest
python scripts/kb_agent.py ingest --apply --drafts
python scripts/kb_agent.py health
python scripts/kb.py update-index
```

原则：Agent 负责处理重复劳动，人负责判断价值、修正理解、决定是否沉淀为永久笔记。
