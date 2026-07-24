# Dev_book

---



已落地第一版轻自动化，核心入口是 [scripts/kb.py](C:/Data/code/My-Knowledge-Base/scripts/kb.py)。

现在可用的命令：

```
python scripts/kb.py new-note "标题" --tags "知识管理,方法" --moc "知识管理 MOC"
python scripts/kb.py new-moc "RAG" --tags "AI,RAG"
python scripts/kb.py new-project "项目名称"
python scripts/kb.py ingest-inbox
python scripts/kb.py ingest-inbox --apply
python scripts/kb.py audit
python scripts/kb.py update-index
```

新增了这些配套文件：

- [自动化使用说明](C:/Data/code/My-Knowledge-Base/90_System/自动化使用说明.md)
- [知识库体检报告](C:/Data/code/My-Knowledge-Base/90_System/知识库体检报告.md)
- [Inbox分流报告](C:/Data/code/My-Knowledge-Base/90_System/Inbox分流报告.md)
- [自动索引 MOC](C:/Data/code/My-Knowledge-Base/50_MOCs/自动索引 MOC.md)
- [.gitignore](C:/Data/code/My-Knowledge-Base/.gitignore)

我也已经验证过：

```
缺少 frontmatter：0
缺少 tags：0
缺少 status：0
未挂 MOC 的原子笔记：0
孤立原子笔记：0
```

当前 `ingest-inbox` 默认只是预览，不会移动文件；确认分流结果没问题后再加 `--apply`。这版的边界是“自动建结构、自动归档、自动体检、自动索引”，还不做 AI 摘要和自动改写，先稳稳跑起来。



> 我希望实现**知识库 Agent 化**
> 可以做到更进一步：
> 你把 PDF、代码、drawio 扔进 Inbox，它自动识别、归档、建索引
> 自动提取 PDF 内容，生成阅读笔记和原子笔记草案
> 自动分析代码文件，提炼“代码模式 / 架构经验 / 排障记录”
> 自动维护双链关系
> 自动回答“我关于 RAG 的资料有哪些，还缺什么？”
> 自动生成某个主题的学习路线、报告、文章大纲
> 接入向量检索，支持语义搜索
> 定期给你生成知识库健康报告
> 这就是一个本地知识库智能助手了。能做，但要谨慎设计权限、确认机制和版本记录。这一个环节还是希望能实现

知识库 Agent 化”落地成第一版本地 Agent。

核心新增：

- [scripts/kb_agent.py](C:/Data/code/My-Knowledge-Base/scripts/kb_agent.py)：本地知识库 Agent 主脚本
- [Agent 使用说明](C:/Data/code/My-Knowledge-Base/90_System/Agent使用说明.md)
- [Agent 健康报告](C:/Data/code/My-Knowledge-Base/90_System/Agent/Agent健康报告.md)
- [双链建议](C:/Data/code/My-Knowledge-Base/90_System/Agent/双链建议.md)
- [问答记录](C:/Data/code/My-Knowledge-Base/90_System/Agent/问答记录.md)
- [RAG 学习路线示例](C:/Data/code/My-Knowledge-Base/60_Outputs/20260724-RAG-学习路线.md)

现在可以这样用：

```
python scripts/kb_agent.py ingest
python scripts/kb_agent.py ingest --apply --drafts
python scripts/kb_agent.py build-index
python scripts/kb_agent.py search "RAG"
python scripts/kb_agent.py ask "我关于 RAG 的资料有哪些，还缺什么？"
python scripts/kb_agent.py outline "RAG" --kind roadmap
python scripts/kb_agent.py health
```

已实现的能力包括：Inbox 识别与归档预览、资源索引、PDF/代码/drawio 草案生成、本地 SQLite FTS 检索、主题问答、学习路线/报告/文章大纲生成、双链建议、健康报告。默认是安全模式，`ingest` 不加 `--apply` 不会移动文件；生成的笔记也都是 `draft`，需要你复核后再沉淀。

验证也跑过了：脚本编译通过，`health`、`build-index`、`search RAG`、`ask`、`outline` 都能执行。检索数据库 `90_System/Agent/kb_search.sqlite3` 已加入 `.gitignore`，作为本地可重建缓存保留。

> 建议搭建web服务；在此之前先给我一个技术选型和设计方案

可以，建议做成 **本地优先的 Web 知识库 Agent**，不要一开始搞成复杂云服务。当前项目已经有 Python 脚本、SQLite FTS 检索、Markdown 文件体系，所以最稳的路线是：**FastAPI 后端 + React/Vite 前端 + SQLite/FTS5 + 文件系统作为知识本体**。

**推荐技术选型**

后端：

```
FastAPI
SQLite + FTS5
Python 标准 pathlib/shutil/sqlite3
可选：pypdf / PyPDF2
可选：sentence-transformers 或外部 embedding API
```

理由：

- 当前自动化脚本已经是 Python，迁移成本最低。
- FastAPI 适合做本地 API 服务，也方便暴露 OpenAPI 文档。
- SQLite 单文件部署简单，FTS5 适合本地全文检索。
- FastAPI 官方也支持静态文件服务，后期可以把前端构建产物直接挂载到后端服务里。参考：FastAPI StaticFiles 文档 https://fastapi.tiangolo.com/tutorial/static-files/
- SQLite FTS5 是官方全文检索扩展，适合当前规模。参考：https://www.sqlite.org/fts5.html

前端：

```
React + TypeScript + Vite
```

理由：

- Vite 开发服务器启动快，适合本地工具型应用。
- React 生态适合做知识库面板、文件树、搜索结果、草案编辑器。
- Vite 官方支持 React/TypeScript 模板。参考：https://vite.dev/guide/

**总体架构**

```
My-Knowledge-Base/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # FastAPI 入口
│  │  ├─ config.py            # 路径、权限、Agent 配置
│  │  ├─ models.py            # Pydantic 请求/响应模型
│  │  ├─ services/
│  │  │  ├─ kb_files.py       # 文件读写、目录扫描
│  │  │  ├─ search.py         # SQLite FTS 检索
│  │  │  ├─ ingest.py         # Inbox 摄取
│  │  │  ├─ agent.py          # 问答、双链建议、大纲生成
│  │  │  └─ audit.py          # 健康检查
│  │  └─ routers/
│  │     ├─ files.py
│  │     ├─ search.py
│  │     ├─ ingest.py
│  │     ├─ agent.py
│  │     └─ system.py
├─ frontend/
│  ├─ src/
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ api/
│  │  └─ App.tsx
├─ scripts/
│  ├─ kb.py
│  └─ kb_agent.py
```

**核心页面设计**

1. **Dashboard**
   - 知识库健康状态
   - Inbox 待处理数量
   - 最近更新笔记
   - 孤立笔记数量
   - 检索索引状态
2. **Inbox**
   - 展示 `00_Inbox/` 文件
   - 一键预览摄取计划
   - 手动确认后执行 `apply`
   - 生成资料索引和草案笔记
3. **Search**
   - 全文检索
   - 按类型过滤：MOC、note、resource-index、report、project
   - 显示命中片段
   - 点击打开 Markdown 内容
4. **Notes / MOC**
   - 文件树
   - Markdown 预览
   - Frontmatter 展示
   - related / moc 链接展示
5. **Agent**
   - 问答输入框
   - “我关于 X 有哪些资料，还缺什么？”
   - 生成学习路线、报告大纲、文章大纲
   - 双链建议
6. **Health**
   - 体检报告
   - 标签统计
   - 缺失元数据
   - 未挂 MOC 笔记
   - 可能过大的笔记

**API 设计**

```
GET  /api/system/status
GET  /api/files/tree
GET  /api/files/read?path=
POST /api/files/write

POST /api/search
POST /api/index/rebuild

GET  /api/inbox/items
POST /api/inbox/preview
POST /api/inbox/apply

POST /api/agent/ask
POST /api/agent/outline
POST /api/agent/suggest-links

POST /api/audit
GET  /api/reports/health
```

**权限与安全设计**

这个很重要。建议默认规则：

```
1. Web 服务只允许访问当前知识库根目录。
2. 所有写操作必须经过 preview -> apply 两步。
3. 禁止任意路径读取，比如 ../../../。
4. 不直接删除文件，只移动到 90_Archive 或生成变更计划。
5. 每次 Agent 写入都生成报告。
6. 后续可加 Git checkpoint：写入前自动检测 git status。
```

**第一版落地范围**

我建议 Web v0 先做这些：

```
1. FastAPI 服务启动
2. React/Vite 前端启动
3. 文件树浏览
4. Markdown 阅读
5. 搜索
6. Inbox 摄取预览
7. 健康报告刷新
8. Agent 问答和大纲生成
```

暂时不做：

```
1. 富文本编辑器
2. 真向量数据库
3. 多用户权限
4. 云同步
5. 外部 LLM 自动改写
```

**启动方式预期**

开发阶段：

```
# 后端
uvicorn backend.app.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

生产/本地一体化阶段：

```
npm run build
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

后端挂载前端 `dist/`，浏览器打开：

```
http://127.0.0.1:8000
```

我的建议：下一步先实现 **FastAPI 后端 + 最小 React 前端**，把当前 `scripts/kb_agent.py` 的能力包装成 API。这样不推翻已有成果，只是给它套一个更舒服的操作界面。

> 尝试将web v0落地；我对最终成品的要求比较高，希望你作为一个优秀的工程师和ui设计师不会让我太失望。

Web v0 已落地并正在运行：

**http://127.0.0.1:8000**

当前已经具备概览、全文检索、目录浏览、文件预览、Inbox 分流、Agent 问答、大纲生成、索引重建和知识库体检。

写入类操作均需要二次确认，并记录本地操作日志；路径越界、未经确认的请求会被后端拒绝。知识文件仍是唯一数据源，SQLite 只是可重建的检索缓存。

核心文件：

- [后端服务](/C:/Data/code/My-Knowledge-Base/backend/app/main.py)
- [Web 界面](/C:/Data/code/My-Knowledge-Base/web/index.html)
- [界面样式](/C:/Data/code/My-Knowledge-Base/web/styles.css)
- [交互逻辑](/C:/Data/code/My-Knowledge-Base/web/app.js)
- [启动脚本](/C:/Data/code/My-Knowledge-Base/scripts/start_web.ps1)
- [使用说明](/C:/Data/code/My-Knowledge-Base/90_System/Web服务说明.md)

已验证 13 个 API 路由、Agent 问答、索引重建、完整体检、Inbox 预览、路径权限和前端脚本。当前索引包含 24 项，服务进程 PID 为 `37680`。

由于当前会话没有可用的内置浏览器，没能完成截图级视觉验收；响应式布局、DOM 完整性和脚本引用已经通过静态检查。下一版最值得补的是 Markdown 富文本渲染、任务进度中心、变更 Diff 审批和真正的向量语义检索

> 继续优化，包括完成截图级视觉验收；响应式布局、DOM 完整性和脚本引用已经通过静态检查。以及 Markdown 富文本渲染、任务进度中心、变更 Diff 审批和真正的向量语义检索。并且文档上传的方式是什么？希望可以再网页中上传文档并支持选择归类到对应的目录下。

Web v1 功能已经完成并运行在：

**http://127.0.0.1:8000**
当前服务进程：`39660`

已经落地：

- Markdown 富文本阅读、源码切换、Frontmatter 展示与双链跳转。
- 网页多文件上传、拖放、目标目录选择、重名保护和 100 MB 限制。
- FTS5 + Qwen Embedding 混合检索，当前为 24 份文档、30 个切片、2048 维向量。
- 后台任务中心，显示索引、体检等任务的进度和错误。
- Inbox 与 Agent 大纲的 Diff 审批，支持批准、拒绝和文件变化检测。
- 桌面、平板、移动端响应式界面重构。

上传文档时，点击右上角“上传文档”或收件箱中的“上传”，拖入文件并选择 `00_Inbox`、`30_Resources/PDFs`、`40_Notes` 等目录。选择 Inbox 后，可生成归档 Diff，再审批移动到目标区域；也可以直接上传到指定目录。

已通过语义召回、混合检索、真实上传、审批执行/拒绝、非法扩展名、未确认写入、路径越界、DOM 引用和脚本语法测试。详细说明见 [Web服务说明.md](/C:/Data/code/My-Knowledge-Base/90_System/Web服务说明.md)。

唯一未完成的是截图级视觉验收：当前 Codex 浏览器运行时没有提供任何浏览器实例，因此无法合规地执行截图和像素检查。请在 Codex 中打开或启用内置浏览器面板后回复“浏览器已就绪”，我会继续完成桌面、平板和移动端截图验收并针对视觉问题迭代。

> 上传似乎没有很大改善，并且能不能再问价上传给一些提示，进度条或者成功或者失败点提示

**1. 支持 `.ipynb` 上传** (backend)

- `UPLOAD_EXTENSIONS` 已加入 `.ipynb`。

**2. 上传进度条 + 成功/失败提示** (frontend)

- 改用 `XMLHttpRequest`,能读取真实上传进度,显示 `正在上传 800 KB / 1.5 MB(53%)` 这类文字 + 进度条动画。
- 成功: 进度条变绿,显示 `✓ 已上传 N 个文件`,1.2 秒后自动关闭对话框。
- 失败: 进度条变红,显示**明确的错误原因**(如 `✕ 不支持上传该类型:xxx` 或 `✕ 超过 100 MB`),且**不会自动消失**,方便你看清。
- 切换文件 / 关闭对话框时会清空上次的进度状态

> 资料库中不支持pdf、ipynb等类型文件的预览吗？