# LangChain

---

## langchain 框架介绍

&emsp;&emsp;LangChain 是一个**构建 LLM 应用的框架**，目标是把 LLM 与外部工具、数据源和复杂工作流连接起来 —— 支持从简单的 prompt 封装到复杂的 Agent（能够调用工具、做决策、执行多步任务）。它不仅仅是对LLM API的封装，而是提供了一套完整的工具和架构，让开发者能够更轻松地构建**上下文感知**和**具备推理能力**的AI应用。LangChain 1.0 版本把“Agent 的稳定化、结构化输出、可观测性与生产化”作为核心改进目标。

> **langchain可以做什么？**

- 构建 Retrieval-Augmented Generation（RAG）问答系统

- 把 LLM 当作“Agent”去调用外部 API（搜索、数据库、文件系统）并返回任务结果

- 组织 prompt → 模型 → 后处理 的可复用流水线（Chains）

- 实现多轮对话带记忆（Memory）与长会话管理

- 在生产中管理可观测性与评估（配合 LangSmith/LangGraph）



&emsp;&emsp;1.0 的架构风格可以用一句话概括:以“**统一智能体抽象 + 标准化内容表示 + 可插拔治理中间件**”为设计骨干,以 LangGraph 为底座运行时,实现“开发简单性”与“生产可控性”的兼顾。它一方面通过 create_agent 提供低门槛的构建入口,另一方面保留足够的钩子点与下探能力,以满足复杂工作流与高标准治理的需求。

```plain
你要做什么AI应用？
│
├─ 只想简单调用模型聊天（翻译/问答）
│   └─> 直接用OpenAI SDK（更轻量，无需LangChain）
│
├─ 需要联网查资料、执行代码、操作数据库
│   └─> 用LangChain 1.0（快速搭建Agent）
│       └─> 参考：客服机器人、数据分析助手
│
├─ 流程很复杂（多人审批/定时任务/状态分支）
│   └─> 用LangGraph 1.0（精确控制每个步骤）
│       └─> 参考：自动化工作流、ERP系统集成
│
└─ 不确定，先试试想法
    └─> 用LangChain 1.0快速验证，后期可无缝迁移到LangGraph
```

### LangChain 生态概览 

>  **模型层（Models）**

LangChain 1.0 的统一模型抽象层，为所有模型提供标准化调用，覆盖文本、多模态、Embedding、Rerank 等多类型模型，实现跨供应商一致体验

- 统一抽象：init_chat_model() 适配20+模型厂商

- 异步/流式/批处理：ainvoke()，stream(), batch()

- 执行方式：完全兼容 LCEL 与 LangGraph

- 扩展能力：with_structured_output()、Tool Calling、多模态 Content Blocks

> **工具层（Tools）**

工具系统提供统一 Tool 抽象，支持所有主流模型的 Tool Calling，深度集成 LangGraph，构建可执行 agent 环境的关键能力层

- 内置工具：搜索、计算、代码执行等100+工具

- 自定义工具：@tool装饰器 / BaseTool / ToolNode

- 工具包：Toolkit（如GitHub、Slack集成）

> **记忆层（Memory）**

记忆层提供统一 State 管理、对话记录、长期检索、多模态 Memory 等能力，支持持久化与复杂工作流状态流转

- 短期记忆：消息历史自动管理 

- 长期记忆：向量数据库存储（Chroma, Pinecone）

- 存储接口：Store（跨会话持久化）

>  **Agent层（Agents）**

LangChain 1.0 Agents系统实现从碎片化到标准化升级，以create_agent为核心接口，基于LangGraph构建统一Agent抽象，10行代码即可创建基础Agent，封装"模型调用→工具选择→执行→结束"闭环流程

- 核心API：create_agent() 

- 执行引擎：LangGraph Runtime（自动持久化）

- 中间件：Middleware（HITL、压缩、路由）

>  **工作流层（Workflows）**

Workflows 体系实现从 线性链式（Chain）到图结构（Graph） 的范式转移，以 StateGraph 为核心画布，将业务逻辑解耦为 "节点（Node）+ 边（Edge）+ 状态（State）"，原生支持循环（Loop）与条件分支，完美适配复杂任务编排、容错重试及长会话保持。

- 简单链：Chain（快速串联）

- 复杂图：LangGraph（条件分支、循环）

- 模板库：LangChain Hub（共享Agent模板）

>  **调试监控层（Debugging）**

LangChain 1.0 调试监控层实现了从 日志黑盒到全链路可观测性（Observability） 的质变，深度集成 LangSmith 平台，自动捕获链（Chain）与图（Graph）的每一步骤状态、Token 消耗及延迟，支持"Trace → Playground"一键回放调试，彻底解决复杂 Agent 逻辑难以排查的痛点。

- 本地日志：verbose=True

- 云端平台：LangSmith（可视化链路追踪）

- 评估工具：LangChain Evaluate（效果评估）

>  **其他关键组件 (LangGraph & LangServe)**

- **langgraph**: 这是一个底层的**Agent 调度框架** (Agent Runtime)，是一个相对“低级”（Low-level）的编排框架，它专注于解决复杂的“控制流”问题，用于构建健壮且有状态的多角色 LLM 应用程序。LangChain 1.0 中的新 Agents (通过 create_agent()) 就是建立在 LangGraph 之上的。

- **langserve**: 用于将任何 LangChain chain 或 agent **部署为 REST API** 的包，方便快速将应用投入生产环境。

### **LangChain 1.0 底层运行架构**

```
# 简化版架构示意图
┌─────────────────────────────────────────┐
│        LangChain 1.0 应用层              │
│  (create_agent, 工具和中间件)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│        LangGraph 编排层                  │
│  (StateGraph, Nodes, Edges, Checkpoints)│
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│        LCEL 运行时层                     │
│  (Runnable接口, |运算符, 流式/批处理)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│        大语言模型API(OpenAI/DeepSeek)    │
└─────────────────────────────────────────┘
```

* LCEL：提供Runnable接口（invoke, stream, batch）和组合原语（|运算符），是无状态的函数式编排，构建“流水线（pipeline）”的工具

* LangGraph：在LCEL基础上增加状态管理（State）、循环控制（Cycles）、持久化（Checkpoints），是有状态的图结构编排，构建“流程图（workflow/graph）”的工具

### Runnable底层执行引擎

Runnable 是 LangChain 1.0 的“统一接口标准”，任何可以运行的组件——模型、Prompt、工具、解析器、Memory、Graph 节点——在 1.0 中都被抽象为 Runnable。

Runnable 使所有 LangChain 组件能够以统一接口组合、执行、链式调用，并支撑 LCEL（LangChain Expression Language）的整个运行语义，支撑可组合、可并行、可路由的链式执行，是 LangChain 1.0 的核心底座之一。

核心思想：Runnable 抽象与可组合链（Composable Chains）

* **LangChain 1.0** 将所有链式元素统一为 Runnable（执行模型）：

  - LLM（OpenAI、vLLM、Ollama……）

  - Prompt

  - Parser

  - Retriever

  - Tool

  - Agent

  - 自定义函数

所有对象都可以 .invoke()、.batch()、.stream()、.astream_events()，这实现了真正的统一调用接口。

* 工程价值：

  - 链路清晰。

  - 任意组件之间可无缝组合。

  - 所有执行方式（同步 / 异步 / 批处理 / 事件流）统一。

  - 这是 LangChain 1.0 最具革命性的改变，使其成为“模型调用管道”的事实标准。

| 方法                    | 核心概念       | 输入           | 输出                                   | 异步版本             |
| :---------------------- | :------------- | :------------- | :------------------------------------- | :------------------- |
| **`.invoke()`**         | **单次调用**   | 单个输入       | 单个完整输出                           | .ainvoke()           |
| **`.batch()`**          | **批量处理**   | 多个输入的列表 | 多个输出的列表                         | .abatch()            |
| **`.stream()`**         | **流式传输**   | 单个输入       | 输出结果的**数据流**（按块产出）       | .astream()           |
| **`.astream_events()`** | **异步事件流** | 单个输入       | 执行过程中的**事件流**（包含中间步骤） | 此方法仅支持**异步** |

- 简单的单次调用，用 **`invoke`**。
- 批量处理独立任务，用 **`batch`**。
- 需要实时反馈最终结果，用 **`stream`**。
- 需要监控复杂内部流程或进行调试，用 **`astream_events`**。

另外，还有一个 `.astream_log()` 方法，它介于 `.stream()` 和 `.astream_events()` 之间，主要用于流式输出中间步骤和最终输出。 

Runnable 接口的所有方法都接受一个可选的 `config` 参数，用于配置执行、添加标签和元数据等，可以把 `RunnableConfig` 理解为一个字典，你可以在调用 `.invoke()`, `.batch()` 等方法时，通过这个字典传入各种配置。



**Prompt Runnable**

```python
from langchain_core.prompts import ChatPromptTemplate

# 1. 定义一个 Prompt (Runnable)
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")

# Prompt 也可以调用 invoke/stream
print(prompt.invoke({"topic": "ice cream"})) 

```

 **Tool Runnable**

```python
from langchain_core.tools import tool

# 2. 定义一个简单的 Tool (Runnable)
@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b

# Tool 也可以调用 invoke/batch
print(multiply.invoke({"a": 2, "b": 3})) 

# Tool 也可以调用 batch (自动并行)
print(multiply.batch([{"a": 2, "b": 3}, {"a": 4, "b": 5}]))
# 输出: [6, 20]
```

**Runnable = LCEL 的语法基础**

LCEL（| 运算符）是由 Runnable 定义的组合语义：

```python
chain = prompt | model | StrOutputParser()
output = chain.invoke({"topic": "LangChain"})
```

这三者本质都是 Runnable：

```python
PromptTemplate   → Runnable
Model            → Runnable
Parser           → Runnable
```

任何 LCEL chain = 多个 Runnable 的组合。

| 技术                | 在 LangChain 1.0 的角色                            |
| ------------------- | -------------------------------------------------- |
| **LangChain**       | 构建 LLM + prompt + tool + outputparser 的组件生态 |
| **LangGraph**       | 构建 Agent / 多步工作流 / 状态机的框架             |
| **LCEL / Runnable** | LangChain 的底层执行引擎，依然核心                 |



## **LangChain 模块化管理的定位与描述**

---

&emsp;&emsp;LangChain 把“核心抽象”与“具体实现/第三方集成/历史实现”拆分成多个包，以实现更清晰的 API 边界、减小核心包体积、并把社区贡献与厂商集成模块化管理。主要目标是：**核心更稳定、可维护；集成可按需安装。**

###  LangChain 1.0 核心依赖包及作用


|                 **依赖包名称**                  |       **核心作用**       |                       **详细功能介绍**                       |
| :---------------------------------------------: | :----------------------: | :----------------------------------------------------------: |
|               **langchain-core**                |  **核心抽象层和 LCEL**   | 定义所有组件（如模型、消息、提示词模板、工具、运行环境）的标准接口和基本抽象。它包含了 **LangChain 表达式语言 (LCEL)**，这是构建链式应用的基础。这是一个**轻量级**、**不含第三方集成**的基石包。 |
|                  **langchain**                  | **应用认知架构（主包）** | 包含构建 LLM 应用的**通用高阶逻辑**，如 Agents (如新的 create_agent() 函数)、Chains 和通用的检索策略 (Retrieval Strategies)。它建立在 langchain-core 之上，是用于组合核心组件的“胶水”层。 |
|             **langchain-community**             |    **社区第三方集成**    | 包含由 LangChain 社区维护的**非核心或不太流行的**第三方集成，例如：大部分的文档加载器 (Document Loaders)、向量存储 (Vector Stores)、不太流行的 LLM/Chat Model 集成等。为了保持包的轻量，所有依赖项都是可选的。 |
| **langchain-openai** / **langchain-[厂商名称]** |   **特定厂商深度集成**   | 针对 **关键合作伙伴** 的集成包（如 langchain-openai, langchain-anthropic）。它们被单独分离出来，以提供**更好的支持、可靠性**和**更轻量级的依赖**。它们只依赖于 langchain-core。 |
|              **langchain-classic**              |      **旧版本兼容**      | 包含 LangChain v0.x 版本中的**已弃用 (deprecated) 或旧版功能**，如旧的 LLMChain、旧版 Retrievers、Indexing API 和 Hub 模块。它的主要作用是为用户提供一个**平稳的迁移期**，确保旧代码在升级到 v1.0 后仍能运行。 |

 **langchain-core**

- 包含 **核心抽象与接口**：LLM/ChatModel 抽象、Prompt 抽象、Chain/Agent 的基类、schema、消息格式等。

- **不包含**具体厂商的实现（例如没有 OpenAI client 的封装），而是定义“合同（interfaces）”，其他包在此之上实现具体功能。

- 这是构建 LangChain 应用生态的最小公共底座。

```python
# 安装：pip install langchain
from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    "为生产{product}的公司起一个好名字？"
)

formatted_prompt = prompt_template.format(product="智能水杯")

response = model.invoke(formatted_prompt)
```

 **langchain 主包**

- **对外的主入口包**：把 `langchain-core` 的核心抽象与“常用实现”组合在一起，便于快速上手。

- 在 v1.0 中，`langchain` 的命名空间被 **显著精简**，只保留构建 agent 的关键 API（更轻、更专注）。官方建议大多数用户直接使用此主包以获得“开箱即用”的体验。


|          模块           |                   核心内容                   |         来源说明         |
| :---------------------: | :------------------------------------------: | :----------------------: |
|   `langchain.agents`    |         `create_agent`, `AgentState`         |      智能体创建核心      |
|  `langchain.messages`   | `AIMessage`, `HumanMessage`, `trim_messages` | 从langchain-core重新导出 |
|    `langchain.tools`    |             `@tool`, `BaseTool`              | 从langchain-core重新导出 |
| `langchain.chat_models` |      `init_chat_model`, `BaseChatModel`      |      统一模型初始化      |
| `langchain.embeddings`  |              `init_embeddings`               |       嵌入模型管理       |

```python
from langchain.agents import create_agent

# 创建智能体
agent_executor = create_agent(llm, tools)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "会议决定：张三需要在下周一前完成项目报告"
    }]
})
```

**langchain-community 第三方集成库**

&emsp;&emsp;langchain-community 作为 LangChain 1.0 的“功能扩展层”，通过社区贡献的非官方集成组件显著扩展了主包的功能边界，其核心价值体现在工具类组件与平台集成两大维度。工具类组件覆盖文档处理全流程，包括 **DirectoryLoader** 文档加载器（支持 PDF、文本等多格式文件批量导入）、**RecursiveCharacterTextSplitter** 文本分割器（按语义边界将文档切分为检索友好的 Chunk）、**PGVector** 向量存储（PostgreSQL 生态的向量数据库适配）及 **HuggingFaceEmbeddings** 嵌入模型（本地部署模型的向量化能力），这些组件共同构成了 RAG 应用的技术基础。平台集成方面，支持与 DeepSeek、阿里云通义千问等模型的对接，例如通过 langchain_community.chat_models.ChatTongyi 类初始化通义千问模型，或利用 Ollama 类调用本地部署的 DeepSeek-R1 模型。

- 收集并维护 **社区/第三方贡献的集成**（例如某些云厂商、开源向量库、特殊工具适配器等）。这些集成**实现了 **`langchain-core`** 定义的接口**，但不属于主包维护范畴。官方会把这些放到 `langchain-community` 仓库/包，便于社区共同维护。

&emsp;&emsp;**包含内容**：

   - **数据库**：MySQL, PostgreSQL, MongoDB, Neo4j等连接器

   - **存储服务**：AWS S3, 阿里云OSS, Google Cloud Storage

   - **工具集成**：Slack, Notion, GitHub, ArXiv, YouTube等API

   - **向量数据库**：Chroma, Pinecone, Qdrant, Milvus等

   - **文档加载器**：PDF, CSV, HTML, Markdown解析器

&emsp;&emsp;**特点**：

- **质量参差不齐**：社区贡献，需自行验证稳定性

- **更新滞后**：依赖社区维护，响应速度慢于官方包

- **功能丰富**：覆盖95%的第三方服务集成需求

```python
# 安装：pip install langchain-community
from langchain_community.document_loaders import NotionDBLoader

# 从Notion数据库加载文档
loader = NotionDBLoader(
    integration_token="secret_...",
    database_id="your-db-id"
)
documents = loader.load()
print(f"加载了{len(documents)}条文档")
```

**langchain-openai（厂商/提供者集成包）**

&emsp;&emsp;厂商特定集成包（如 langchain-openai、langchain-anthropic、langchain-google 等）通过封装 API 细节，为开发者提供“零适配成本”的模型对接方案，其核心价值在于简化特定 API 对接流程，使开发者能够直接使用厂商特有功能。以 langchain-openai 为例，其关键组件包括模型客户端、工具调用适配和多模型支持三大模块。

&emsp;&emsp;此外，该类还支持通过配置 openai_api_base 和 openai_api_key 参数对接兼容 OpenAI API 格式的第三方模型，如 DeepSeek 模型

- **专门负责把 OpenAI 的 SDK 与 LangChain 抽象连接起来**：提供 `ChatOpenAI`、`OpenAIEmbeddings`、`OpenAI`等类的实现。

- 这类包通常是 “按厂商拆分”：`langchain-openai`、`langchain-azure`、`langchain-anthropic`、`langchain-deepseek`等。

- **官方深度集成**特定LLM提供商，更新频繁，功能最全.

```python
#!pip install langchain-openai
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")

question = "你好，请你介绍一下你自己。"

result = model.invoke(question)
print(result.content)
```

&emsp;&emsp;**主流厂商包列表**：

- `langchain-openai`：OpenAI, Azure OpenAI

- `langchain-anthropic`：Claude系列

- `langchain-google`：Gemini, Vertex AI

- `langchain-deepseek`：DeepSeek模型

- `langchain-ollama`：本地Ollama部署

&emsp;&emsp;**与**`langchain-community`**的区别**：


|  **维度**  |       `langchain-openai`       | `langchain-community`<br/>**中的OpenAI** |
| :--------: | :----------------------------: | :--------------------------------------: |
|   维护方   |   OpenAI官方 + LangChain团队   |                 社区维护                 |
|  更新频率  |        即时跟进API更新         |                 延迟数周                 |
| 功能完整性 | 支持所有新特性（如音频、视觉） |                仅基础功能                |
| 生产可用性 |           ✅ 强烈推荐           |                ⚠️ 谨慎使用                |

&emsp;&emsp;为什么要单独拆出来？

- 让 `langchain` 主包保持轻量（不强制安装所有厂商 SDK）；

- 用户按需安装对应厂商，例如你只用 OpenAI，就只装 `langchain-openai`。

&emsp;&emsp;**最佳实践**：

- **生产环境务必使用厂商包**：享受最新功能

- **开发环境可用community**：快速验证想法

- **多厂商切换用**`init_chat_model`：业务代码无需改动



 **langchain-classic**

- **兼容包 / 迁移包**：把 LangChain v0.x 中的“老 API / legacy 功能”搬到单独包里，以便 v1.0 保持精简，但仍给用户向后兼容的迁移通道。

- 包含如：老的 Chain 实现、旧版 retrievers、索引 API、hub 模块等被标记为“legacy”的功能。

  - 旧版`AgentExecutor`

  - Legacy Chains（`LLMChain`, `SequentialChain`等）

```python
#!pip intsall langchain-classic
from langchain_classic.chat_models import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")
res = model.invoke("请介绍一下你自己")
```

## 核心概念与组件

---

### LLM / ChatModel 大模型接口