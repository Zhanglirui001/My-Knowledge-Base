# langchian 进阶

---

## langchian1.0框架搭建智能体agent

### Agent核心概念与架构

&emsp;&emsp;Agent智能体是一种以大语言模型（LLM）为"大脑"，能够自主感知环境、进行推理规划，并调用外部工具执行复杂任务的系统。它不仅仅是简单的程序，而是具备一系列高级特征的复杂系统。根据LangChain框架的定义，Agent的核心是以大语言模型（LLM）作为其推理引擎，并依据LLM的推理结果来决定如何与外部工具进行交互以及采取何种具体行动。这种架构将LLM的强大语言理解与生成能力，与外部工具的实际执行能力相结合，从而突破了单一LLM的知识限制和功能边界。Agent的本质可以被理解为一种高级的提示工程（Prompt Engineering）应用范式，开发者通过精心设计的提示词模板，引导LLM模仿人类的思考与执行方式，使其能够自主地分解任务、选择工具、调用工具并整合结果，最终完成复杂的任务。

&emsp;&emsp;Agent（智能体）已超越传统AI模型，成为能够自主完成多步骤复杂任务的智能数字助手。其核心特征在于自主性增强、执行能力和持续学习。

<div align=center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251125212642459.png" width=80%></div>


| **对比维度** |  **传统AI模型**  |      **Agent智能体**       |
| :----------: | :--------------: | :------------------------: |
| **交互能力** | 被动响应用户输入 |      主动感知环境变化      |
| **决策模式** |   基于概率预测   |   基于目标导向的主动规划   |
| **执行能力** | 仅生成文本/内容  | 能够调用工具、访问外部系统 |
| **学习方式** |   静态知识更新   |   动态记忆积累和经验反思   |
| **任务处理** |   单次对话完成   |  支持多步骤、复杂任务序列  |
| **自主程度** | 高度依赖人类指导 | 具备一定程度的自主决策能力 |

### Agent核心特征

&emsp;&emsp;Agent智能体通常具备以下几个核心特征，这些特征共同构成了其强大的能力基础：

**自主性**

&emsp;&emsp;**自主性是Agent最核心的特征之一**，指的是Agent能够在没有人类直接干预的情况下，独立地完成任务的感知、规划、决策和行动的全过程。在LangChain框架中，这种自主性体现在Agent能够根据用户的输入，自动判断是否需要调用外部工具，选择哪个工具，以及如何组织调用参数。例如，当用户询问"北京的天气怎么样？"时，Agent能够自主识别出这是一个需要实时信息查询的任务，并自动调用天气查询工具来获取答案，而无需开发者显式地编写"如果问题是关于天气，则调用天气API"这样的硬编码逻辑。这种自主性使得Agent能够处理更加开放和动态的问题，极大地提升了应用的灵活性和智能水平。

**感知能力**

&emsp;&emsp;感知能力是指Agent获取和理解环境信息的能力。在基于LLM的Agent中，环境信息主要以文本形式存在，包括用户的输入、工具的输出以及系统状态等。Agent通过其底层的LLM来解析和理解这些文本信息，从中提取关键指令、实体和上下文。例如，在接收到用户问题后，Agent需要感知问题的意图和关键实体（如地点、时间、人物），以便决定后续的行动。LangChain框架通过提供标准化的消息格式（如`HumanMessage`, `AIMessage`）和工具描述机制，为Agent的感知能力提供了坚实的基础，使其能够清晰地理解来自不同来源的信息。

**推理与规划**

&emsp;&emsp;推理与规划是Agent智能的核心。Agent需要能够分析任务目标，并将其分解为一系列可执行的子步骤。LangChain中的Agent，特别是基于**ReAct（Reasoning and Acting）范式**的Agent，展现了强大的推理和规划能力。ReAct框架要求LLM在每一步都生成一个"思考"（Thought）过程，解释其当前的理解和下一步的计划，然后生成一个"行动"（Action），即调用某个工具。这个过程会循环进行，直到Agent认为已经收集了足够的信息来回答原始问题。例如，面对一个复杂的多步骤数学问题，Agent会先规划出解题步骤，如"首先计算A，然后用A的结果计算B"，并按此规划逐步调用计算工具来完成任务。

**行动能力**

&emsp;&emsp;行动能力是指Agent执行具体操作以影响环境的能力。在LangChain框架中，Agent的行动能力主要通过调用外部工具（Tools）来实现。这些工具可以是API调用、数据库查询、代码执行器，甚至是其他Agent。Agent通过LLM来决定调用哪个工具，并生成符合工具要求的输入参数。工具执行后，其输出结果会作为新的环境信息反馈给Agent，供其进行下一步的推理和决策。这种"思考-行动-观察"的循环，使得Agent能够与外部世界进行有效的交互，从而完成各种复杂的实际任务，如信息检索、数据处理和自动化流程控制。

**学习能力**

&emsp;&emsp;一个真正的智能体不仅仅是执行预设的程序，它还应该具备从经验中学习并不断优化自身行为的能力。这种学习能力通常通过**强化学习、反馈机制或记忆系统**来实现。智能体在每次行动后，会观察行动的结果，并根据结果（例如，用户的反馈或环境的奖励/惩罚信号）来调整其内部的决策模型或策略。例如，如果一个智能体推荐的商品被用户频繁购买，它就会学习到这种推荐是有效的；反之，如果推荐被用户忽略或拒绝，它就会调整其推荐策略。这种持续学习和优化的能力使得智能体能够随着时间的推移变得越来越"聪明"，更好地适应复杂多变的环境。

<div align=center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251125212642483.png" width=70%></div>

### Agent技术架构核心

&emsp;&emsp;理解 **Agent（智能体）** 最难的地方在于理解它"**如何自主决策**"。在LangChain 1.0框架中，Agent不再只是一个简单的问答机器人，它更像是一个"拥有万能工具箱的超级项目经理"。

- **LLM（大模型） = 大脑（项目经理）**：它负责思考、规划、决定下一步做什么，但它不能联网，也不能算复杂的数学（如果不借助工具）。

- **Tools（工具） = 手脚（执行专员）**：比如谷歌搜索（负责看世界）、计算器（负责算数）、数据库（负责查档案）。

- **Agent = 大脑 + 手脚 + 循环机制**：把大脑和手脚结合起来，通过不断的"思考-行动-观察"循环来解决问题。

<div align=center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251125213213813.png" width=70%></div>

&emsp;&emsp;现代Agent的技术架构由五个核心模块构成，形成完整的"感知-思考-行动"闭环。

- 感知模块 (Perception)：负责接收文本、图像、语音等多模态输入。

- 认知中枢 (Brain/Planning)：基于大语言模型（LLM）和检索增强生成（RAG）技术，进行推理和决策，弥补LLM无法获取实时信息和执行具体操作的缺陷。

- 记忆系统 (Memory)：通过短期记忆维持对话连贯，长期记忆积累经验与偏好。

- 工具生态 (Tools)：通过API调用、数据库访问等方式与外部系统交互。

- 执行引擎 (Action)：负责执行具体任务并反馈结果。

&emsp;&emsp;这一机制使得Agent能够构建一个完整的执行闭环：环境感知 → 任务规划 → 工具调用 → 执行反馈 → 自我反思 → 优化调整，从而在复杂环境中持续学习和改进。

### Agent与LangChain结合机制

&emsp;&emsp;LangChain 1.0通过将Agent的决策与LangGraph的图式执行相结合，提供了生产级的Agent运行时。其结合机制体现在以下几个方面：

**核心结合点：`create_agent` + LangGraph**

&emsp;&emsp;`create_agent`作为上层统一入口，其内部实现依赖于LangGraph。当调用`create_agent`时，LangChain会自动构建一个基于ReAct（推理+行动）范式的图结构。这个图包含了Agent决策、工具调用、状态更新等核心节点，并通过边来控制逻辑流转。这种设计将Agent的"思考"过程映射为图的遍历，使得整个执行流程变得透明、可控。

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20251028154837987.png" alt="image-20251028154837987" style="zoom:50%;" />

LangChain 1.0 的 create_agent 通过这 9 个核心参数，实现了从快速原型到生产部署的全覆盖，开发者可根据场景灵活组合。

* create_agent 的核心价值在于它通过 "三要素 + 三扩展" 的极简抽象，彻底重构了 Agent 的开发范式。所谓三要素，即模型（Model）、工具（Tools）与提示词（System Prompt），这三者构成了 Agent 的"灵魂"——决定了它能思考什么、能做什么以及行为边界何在。而三扩展——中间件（Middleware）、内存管理（Memory）与状态管理（State）——则构建了 Agent 的"神经系统"，使其具备生产级应用所需的可靠性、可观测性与可维护性。

* 这一设计将开发者从繁琐的 ReAct 循环手写、工具调用异常处理、上下文压缩等底层细节中解放出来，转而采用声明式编程模式：只需描述"Agent 应该做什么"，框架自动编译为高效、可靠、安全的执行计划。其本质是 LangGraph 的编译器前端 ，将高层意图转换为优化的图结构，自动集成持久化、流式输出、断点恢复等运行时能力。
这种架构带来了三重革命性影响：首先，开发效率提升 10 倍，10 行代码即可构建一个可投产的智能客服或数据分析 Agent；其次，运维成本降低 60%，中间件机制将 PII 检测、人工审批、自动重试等横切关注点解耦，无需侵入业务代码；最后，可扩展性实现质的飞跃，通过 TypedDict 扩展 State，可无缝集成用户画像、多模态输入、性能监控等复杂场景。

| 参数              | 类型      | 必填 | 默认值     | 核心作用   | 最佳实践                 |
| ----------------- | --------- | ---- | ---------- | ---------- | ------------------------ |
| `model`           | str/实例  | ✅    | -          | 推理引擎   | 生产环境实例化配置       |
| `tools`           | list      | ✅    | \[]        | 执行能力   | 描述清晰，按需添加       |
| `system_prompt`   | str       | ❌    | None       | 行为准则   | 明确角色和约束           |
| `middleware`      | list      | ❌    | \[]        | 功能扩展   | 组合日志、安全、摘要     |
| `checkpointer`    | Saver     | ❌    | None       | 短期记忆   | 生产用 PostgresSaver     |
| `store`           | Store     | ❌    | None       | 长期记忆   | 跨会话用 PostgresStore   |
| `state_schema`    | TypedDict | ❌    | AgentState | 扩展状态   | 用 TypedDict 非 Pydantic |
| `context_schema`  | TypedDict | ❌    | None       | 动态上下文 | 配合 middleware 使用     |
| `response_format` | BaseModel | ❌    | None       | 结构化输出 | API 对接场景启用         |

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,                    # 模型
    tools=[order_query_tool],       # 工具
    system_prompt="你是一个订单查询助手，能够查询订单状态和明细。" , # 系统提示
    middlewares=[order_query_middleware],                    # 中间件
    checkpointer=checkpointer,      # 检查点短期记忆
    store=store,                    # 状态存储长期记忆
    state_schema=OrderQueryState,   # 扩展状态（如需要）
    context_schema=AgentContext,    # 上下文状态（如需要）
    response_format=ResponseModel   # 结构化输出（如需要）
)

# ============ 限制最大 3 次循环 ============
config = {
    "configurable": {"thread_id": "limit_demo"}, # 限制thread_id 线程ID
    "recursion_limit": 3  # 最多 3 次迭代，或使用中间件进行精确跟踪和终止循环
}

result = agent.invoke(
        {"messages": [{"role": "user", "content": "LangChain 1.0 发布日期"}]},
        config=config
    )
```

 **ReAct范式与执行循环**

&emsp;&emsp;ReAct(Reasoning + Acting)范式强调"推理—行动—观察"的闭环:Agent先形成Thought(推理),据此选择并调用工具(Action),再吸收工具返回的Observation(观察),进入下一轮决策。闭环在达到最终答案、迭代上限或时间上限时终止。在LangGraph中,这一闭环由状态机与检查点驱动,保证每次行动的原子性、状态的可见性与轨迹的可回放性。并且推理与规划不是代码逻辑，而是LLM的生成行为，关键的 Thought: 步骤并非由确定性算法执行，而是prompt触发LLM生成推理文本。模型能力是ReAct性能的天花板

<div align=center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251125215020369.png" width=60%></div>

Agent的认知循环本质上是一个闭环反馈系统。每一次"行动"的执行结果都会作为新的输入反馈到系统，影响下一轮的"思考"和"行动"。这种反馈机制使得Agent能够动态调整策略，应对不确定的环境和复杂任务。在LangChain中，这一循环被实现为：

1. **Thought (推理)**：大模型基于当前输入和历史记录进行思考，决定下一步行动。

2. **Action (行动)**：大模型选择一个工具并构造输入参数，形成一个`AgentAction`。

3. **Observation (观察)**：工具被执行，其返回结果作为观察值，并与`AgentAction`一起被添加到中间步骤（intermediate_steps）中。

4. **循环决策**：Agent将新的观察结果纳入上下文，进入下一轮"推理-行动"循环，直至达到最终目标或触发终止条件（如达到最大迭代次数）。

### 工具（Tools）的集成与调用

&emsp;&emsp;工具是Agent与外部世界交互的桥梁。在LangChain中，工具的`name`、`description`和`args_schema`至关重要，它们共同决定了模型是否以及如何选择和调用工具。一个设计良好的工具描述是提示工程的关键部分。

- **工具注册**：通过`@tool`装饰器或继承`BaseTool`类来定义工具。

- **工具调用**：Agent在决策时，会根据工具描述选择最合适的工具。执行引擎负责调用该工具并处理其返回结果或异常。

- **安全与治理**：在生产环境中，应对工具的调用进行严格的风险控制，如速率限制、权限隔离、输入校验等，这些可以通过中间件或在工具实现中直接加入。

- LangChain内置工具列表：https://python.langchain.com/docs/integrations/tools/


|     **工具名**      |     **Python 类**     |      **作用**      |
| :-----------------: | :-------------------: | :----------------: |
|   **python_repl**   |   `PythonREPLTool`    |    执行 Python     |
|      **shell**      |      `ShellTool`      |     执行命令行     |
|      **human**      |      `HumanTool`      |      人工输入      |
|  **requests_get**   |   `RequestsGetTool`   |      GET 请求      |
|  **requests_post**  |  `RequestsPostTool`   |     POST 请求      |
|   **bing_search**   |    `BingSearchRun`    |     Bing 搜索      |
|     **serper**      |   `GoogleSerperRun`   |    Google 搜索     |
|  **tavily_search**  | `TavilySearchResults` |    Tavily 搜索     |
|   **web_loader**    |    `WebBaseLoader`    |      网页加载      |
|      **apify**      |   `ApifyActorTool`    |      网页爬虫      |
|      **gmail**      |      Gmail 工具       |      邮件管理      |
| **google_calendar** |  GoogleCalendar 工具  |      日程管理      |
|   **python_ast**    |   PythonAstREPLTool   | 数据分析安全执行器 |
|    **read_file**    |     ReadFileTool      |      读取文件      |
|   **write_file**    |     WriteFileTool     |      写入文件      |
|  **sql_db_query**   | QuerySQLDatabaseTool  |      SQL 查询      |
|    **retriever**    |    VectorStoreTool    |      RAG 检索      |