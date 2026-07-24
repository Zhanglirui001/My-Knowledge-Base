# Web v0 使用说明

Web v0 是知识库的本地操作台，直接复用 `scripts/kb.py` 与 `scripts/kb_agent.py`，不会创建第二套知识数据。

## 启动

```powershell
py -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1
```

默认地址：`http://127.0.0.1:8000`

也可以指定端口：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1 -Port 8010
```

## 已实现

- 概览：文档、原子笔记、MOC、Inbox 与索引状态。
- 检索：SQLite FTS5 全文检索，结果可直接打开原文。
- 资料库：按知识库目录树浏览 Markdown、代码和结构化文本。
- Inbox：预览分流，确认后归档、建索引并生成阅读笔记草案。
- Agent：基于本地索引回答问题，生成学习路线、报告或文章大纲。
- 健康度：查看报告，重建索引，运行完整体检。

## 权限边界

只读操作可以直接执行。归档、生成大纲、重建索引和完整体检必须在界面中二次确认。服务只允许读取知识库根目录内的文本文件，路径越界请求会被拒绝。

写操作记录在 `90_System/Agent/Web操作日志.jsonl`。该文件可能包含个人查询内容，默认不提交 Git。

## 数据说明

`90_System/Agent/kb_search.sqlite3` 仍然只是可重建的检索缓存。Web 服务不会把笔记正文存入另一套主数据库，原始文件依然是唯一事实来源。

## API

开发调试文档：`http://127.0.0.1:8000/api/docs`
