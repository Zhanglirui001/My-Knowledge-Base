# Web 知识库使用说明

Web 服务是本地知识库操作台，直接复用现有文件、MOC、Agent 脚本与 SQLite 索引。Markdown 等原始文件仍是唯一事实来源。

## 启动

```powershell
py -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1
```

默认地址：`http://127.0.0.1:8000`

指定端口：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1 -Port 8010
```

## 网页上传

点击页面右上角“上传文档”，或进入“收件箱”后点击“上传”。

1. 选择或拖放一个或多个文件。
2. 在“归类目录”中选择目标目录。
3. 决定是否在上传完成后更新关键词与向量索引。
4. 点击“确认上传”。

选择 `00_Inbox` 表示稍后分流。选择 `30_Resources/PDFs`、`40_Notes`、`10_Projects` 等目录表示直接归类。重名文件不会覆盖原文件，系统会自动生成唯一文件名。

单文件默认上限为 100 MB。支持 Markdown、PDF、Drawio、常见代码与文本格式、Office 文档、图片和表格文件。Office 文件可以保存和管理，但当前版本尚未抽取其正文建立语义切片。

## 检索

- 关键词：SQLite FTS5，适合精确术语、文件名和代码符号。
- 语义：Qwen3-VL-Embedding-2B，当前向量维度为 2048。
- 混合：通过排名融合组合关键词与语义结果，是默认模式。

向量数据库位于 `90_System/Agent/kb_vectors.sqlite3`，和 FTS5 数据库一样都是可重建缓存。重建不会修改原始知识文件。

默认局域网 Embedding 配置：

```text
KB_EMBEDDING_URL=http://192.168.70.249:8000/v1
KB_EMBEDDING_MODEL=./models/Qwen3-VL-Embedding-2B
```

可通过进程环境变量覆盖：

```powershell
$env:KB_EMBEDDING_URL="http://your-server/v1"
$env:KB_EMBEDDING_MODEL="your-embedding-model"
powershell -ExecutionPolicy Bypass -File scripts/start_web.ps1
```

建立向量索引时，抽取后的文档文本会发送到该 Embedding 服务。默认地址是局域网服务，不经过公开云端。

## Markdown 阅读

Markdown 文件会渲染为标题、列表、表格、引用、代码块和行内代码。YAML frontmatter 单独显示，`[[双链]]` 可以在阅读器内继续跳转。阅读器右上角可以切换富文本和 Markdown 源码。

## 任务中心

上传后索引、完整体检和手动重建索引都在后台执行。页面右上角“任务”显示排队、执行进度、完成结果和失败原因。任务状态保存在当前服务进程内，重启服务后历史任务不会保留，但索引和报告文件不会丢失。

## Diff 审批

Inbox 归档和 Agent 大纲生成不会直接修改知识库，而是先创建变更计划。进入“变更审批”可以检查目标路径与 Diff，然后选择：

- 批准并应用：执行文件移动或写入，随后后台更新索引。
- 拒绝：计划标记为已拒绝，不写入知识文件。

计划存放于 `90_System/Agent/changes/`，默认不提交 Git。审批期间目标文件若发生变化，后端会拒绝应用旧计划。

## 权限与安全

- 读取路径必须位于知识库根目录内。
- 上传只能写入 Inbox、Projects、Areas、Resources、Notes、MOCs、Outputs 和 `_assets`。
- 上传使用临时文件完成原子落盘；批量上传失败时会清理该批已经写入的文件。
- 写入、索引和体检操作需要明确确认。
- 操作记录位于 `90_System/Agent/Web操作日志.jsonl`，可能包含个人查询，默认不提交 Git。

## API

开发调试文档：`http://127.0.0.1:8000/api/docs`
