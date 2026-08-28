# LangChain 1.0 Agent智能体中间件应用实战

---

### Agent 开发的可观测性基石

&emsp;&emsp;在对LangChain 1.0有了一定的基础了解之后，对于开发者来说，还需要进一步了解和掌握LangChain Agent必备的开发者套件。分别是LangChain Agent运行监控框架LangSmith、底层LangGraph图结构可视化与调试框架LangGraph Studio和LangGraph服务部署工具LangGraph Cli。可以说这些开发工具套件，是真正推动LangGraph的企业级应用开发效率大幅提升的关键。同时监控、调试和部署工具，也是全新一代企业级Agent开发框架的必备工具，也是开发者必须要掌握的基础工具。

#### LangGraph图结构可视化与调试框架：LangGraph Studio

&emsp;&emsp;**LangGraph Studio** 它是一个本地 Graph 可视化引擎，是一个用于可视化构建、测试、分享和部署智能体流程图的图形化 IDE + 运行平台。专注于实时的状态展示和交互式调试。对于正在开发复杂 Agent 逻辑的工程师来说，能够实时观察每个节点的执行状态、输入输出数据和中间计算结果，这种可视化的调试体验是无价的。langGraph Studio`对于`LangChian Agent`来说，则是比`LangSmith`更加方便和高效的可视化调试工具平台。

`LangGraph Studio` 在本地可视化运行时会自动把调用过程上传到 `LangSmith`；而在 `LangSmith` 网页端查看任何 `Trace` 时，又能一键`Run in Studio`回放整条执行链，所以它是通过统一 `Trace SDK` 与 `LangSmith` 紧密集成。而LangGraph CLI则是构建这个项目的关键

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251202190426330.png
" alt="image-20250626130624364" style="zoom: 70%;" />

#### LangGraph服务部署工具：LangGraph Cli

&emsp;&emsp;LangGraph CLI 是用于本地启动、调试、测试和托管 LangGraph 智能体图的开发者命令行工具。

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250626131252066.png" alt="image-20250626131252066" style="zoom:50%;" />

| 功能类别              | 命令示例                                                | 说明                                                    |
| --------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| ✅ 启动 Graph 服务     | `langgraph dev`                                         | 启动 Graph 的开发服务器，供前端（如 Agent Chat UI）调用 |
| 🧪 测试 Graph 输入     | `langgraph run graph:graph --input '{"input": "你好"}'` | 本地 CLI 输入测试，输出结果                             |
| 🧭 管理项目结构        | `langgraph init`                                        | 初始化一个标准 Graph 项目目录结构                       |
| 📦 部署 Graph（未来）  | `langgraph deploy`（预留）                              | 发布 graph 至 LangGraph 云端（已对接 Studio）           |
| 🧱 显示 Assistant 列表 | `langgraph list`                                        | 显示当前 graph 中有哪些 assistant（即 entrypoint）      |
| 🔄 重载运行时          | 自动热重载                                              | 修改 `graph.py` 时，`dev` 模式自动重启生效              |

而一旦应用成功部署上线，LangGraph Cli还会非常贴心的提供后端接口说明文档：

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251202191424859.png" alt="image-20250626132044152" style="zoom:70%;" />

而对于LangGraph构建的智能体，除了能够本地部署外，官方也提供了云托管服务，借助LangGraph Platform，开发者可以将构建的智能体 Graph部署到云端，并允许公开访问，同时支持支持长时间运行、文件上传、外部 API 调用、Studio 集成等功能。

##### 创建完整LangGraph智能体项目流程

- **Step 1. 创建一个`LangChain Agent`项目主文件夹**

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251202193605261.png" alt="image-20251028174723860" style="zoom:50%;" />

- **Step 2. 创建`requirements.txt`文件**

&emsp;&emsp;在`LangChain Chatbot`文件夹中，新建一个`requirements.txt`文件，里面需要填写在运行该项目时需要安装的依赖项(**注意**：这里的依赖可以根据自己需要的进行增加)，如下所示：

```bash
langchain
langchain-deepseek
langchain-openai
langchain-tavily
python-dotenv
langsmith
pydantic
matplotlib
seaborn
pandas
IPython

```

- **Step 3. 注册LangSmith（可选）**

&emsp;&emsp;对于企业级的Agent项目，为了更好的监控智能体实时运行情况，我们可以考虑借助LangSmith进行追踪（会将智能体运行情况实时上传到LangGraph官网并进行展示）。

&emsp;&emsp;要开始使用 `LangSmith`，我们需要创建一个帐户。可以在这里注册一个免费帐户进入`LangSmith`登录页面： https://smith.langchain.com/ ， 支持使用 Google、GitHub、Discord 和电子邮件登录。

&emsp;&emsp;注册并等登录后，可以直接查看到仪表板：

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624190049558.png" alt="image-20250624190049558" style="zoom:33%;" />

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624190123279.png" alt="image-20250624190123279" style="zoom:33%;" />

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624190228537.png" alt="image-20250624190228537" style="zoom:33%;" />

&emsp;&emsp;在构建程序跟踪前，首先需要创建一个 `API` 密钥，该密钥将允许我们的项目开始向 `Langsmith` 发送跟踪数据。创建完密钥后，在后续配置环境变量环节设置开启追踪、并输入密钥即可接入LangSmith。

- **Step 4. 创建`.env`配置文件**

&emsp;&emsp;在`LangChain Chatbot`文件夹中，新建一个`.env`文件，将敏感信息（如`API`密钥）放在环境变量中而不是硬编码。如下所示：

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20251028175031725.png" alt="image-20251028175031725" style="zoom:40%;" />

这里需要注意的是，如果不设置LangSmith，则无需设置中间三个环境变量，而具体工具也可以根据实际需求进行设置。

- **Step 5. 创建`graph.py`核心文件**

&emsp;&emsp;在`LangChain Agent`文件夹中，新建一个`graph.py`文件，在该文件中编写构建图的具体运行逻辑，如状态、节点、变、图的编译等。此外，在使用LangGraph CLI创建智能体项目时，会自动设置记忆相关内容，并进行持久化记忆存储，无需手动设置。因此此时智能体代码如下所示：

```python
import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests,json

# 加载环境变量
load_dotenv(override=True)

# 内置搜索工具
search_tool = TavilySearch(max_results=5, topic="general")

class WeatherQuery(BaseModel):
    loc: str = Field(description="The location name of the city")

@tool(args_schema = WeatherQuery)
def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    :return：OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    # Step 1.构建请求
    url = "https://api.openweathermap.org/data/2.5/weather"

    # Step 2.设置查询参数
    params = {
        "q": loc,
        "appid": os.getenv("OPENWEATHER_API_KEY"),    # 输入API key
        "units": "metric",            # 使用摄氏度而不是华氏度
        "lang":"zh_cn"                # 输出语言为简体中文
    }

    # Step 3.发送GET请求
    response = requests.get(url, params=params)

    # Step 4.解析响应
    data = response.json()
    return json.dumps(data)

tools = [search_tool, get_weather]

# 创建模型
model = ChatDeepSeek(model="deepseek-chat")

prompt = """
你是一名乐于助人的智能助手，擅长根据用户的问题选择合适的工具来查询信息并回答。

当用户的问题涉及**天气信息**时，你应优先调用`get_weather`工具，查询用户指定城市的实时天气，并在回答中总结查询结果。

当用户的问题涉及**新闻、事件、实时动态**时，你应优先调用`search_tool`工具，检索相关的最新信息，并在回答中简要概述。

如果问题既包含天气又包含新闻，请先使用`get_weather`查询天气，再使用`search_tool`查询新闻，最后将结果合并后回复用户。

所有回答应使用**简体中文**，条理清晰、简洁友好。
"""

# 创建图
graph = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt)
```

这里的代码编写时需要注意，如果需要使用langgraph studio进行可视化调试，则需要注意下面两点：

* 1、使用create_agent创建的对象名称必须是graph，与langgraph.json中后缀定义的名称要一致（graph.py:graph）

* 2、create_agent创建时不可以加checkpointer记忆参数，否则langgraph studio会报错

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624191412113.png" alt="image-20250624191412113" style="zoom:33%;" />

- **Step 6. 创建`langgraph.json`文件**

&emsp;&emsp;在`LangChain Agent`文件夹中，新建一个`langgraph.json`文件，在该`json`文件中配置项目信息，遵循规范如下所示：

- 必须包含 `dependencies` 和 `graphs` 字段
- `graphs` 字段格式："图名": "文件路径:变量名"
- 配置文件必须放在与Python文件同级或更高级的目录

&emsp;&emsp;注意: 项目文件的名称必须为`langgraph.json`。如下所示：

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624191532218.png" alt="image-20250624191532218" style="zoom:33%;" />

```josn
{
  "dependencies": ["./"],
  "graphs": {
    "chatbot": "./graph.py:graph"
  },
  "env": ".env"
}
```

&emsp;&emsp;其中：
- `dependencies`: ["./"] - 告诉`LangGraph`在当前目录查找依赖项（会自动读取`requirements.txt`）
- `chatbot`: "./graph.py:graph" - 定义图名为`chatbot`，来自`graph.py`文件中的`graph`变量
- `env`: ".env" - 指定环境变量文件位置

&emsp;&emsp;最终完整项目结构如下所示：

```json
    ./langraph_chatbot/
    ├── graph.py              # 对应官方的 agent.py
    ├── requirements.txt      # ✅ 依赖管理
    ├── langgraph.json       # ✅ 配置文件
    └── .env                 # ✅ 环境变量
```

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20250624191613003.png" alt="image-20250624191613003" style="zoom:50%;" />

- **Step 7. 安装`langgraph-cli`以及其他依赖**

```python
!pip install -U "langgraph-cli[inmem]"
```

&emsp;&emsp;然后，安装`langgraph-cli`依赖，执行如下代码：

```bash
    pip install -U "langgraph-cli[inmem]"
```

```bash
    pip install -r requirements.txt
```

执行`LangGraph dev`即可启动项目

```bash
    langgraph dev
```

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20251028175822701.png" alt="image-20251028175822701" style="zoom:50%;" />

&emsp;&emsp;启动成功后能看到三个连接，其中第一个连接是当前部署完成后的服务端口，第二个是LangGraph Studio的可视化页面，第三个端口是端口说明。这里点击第二个链接进入Langgraph Studio的页面：

<center>
<img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/image-20251028175752261.png" alt="image-20251028175752261" style="zoom:40%;" />

### LangChain1.0中间件概览

&emsp;&emsp;接下来将深入探讨 LangChain 1.0 中间件体系的设计原理、实际应用和最佳实践，帮助开发者构建更加稳定、安全、可控的 AI Agent 系统。我们将从基础概念出发，逐步深入到具体的实现细节和高级应用场景，为读者提供一个完整的技术指南。

#### **中间件架构原理**

LangChain 1.0其核心创新之一便是引入了中间件（Middleware）系统，旨在解决早期版本中Agent抽象无法灵活定制的痛点。
在LangChain 1.0及后续版本中，中间件（Middleware）被正式定义为一种用于拦截、修改、控制和增强Agent执行流程的机制。它借鉴了Web开发（如Express/Django）中的中间件模式，允许开发者在模型调用前后、Agent启动前后或工具调用前后插入自定义逻辑，从而实现日志记录、权限控制、上下文压缩等功能，而无需修改Agent的核心业务逻辑。

* 核心设计目标：

    * 关注点分离：每个中间件只处理单一功能

    * 可组合性：多个中间件可链式调用

    * 可测试性：支持独立单元测试

    * 生产就绪：内置隐私保护、成本管控等企业级能力

&emsp;&emsp;要理解中间件的工作原理，我们可以将其比作一个洋葱。每一层中间件都包裹着核心的 Agent 功能，就像洋葱的每一层都有其特定的作用。当用户请求到达时，它必须逐层通过这些中间件，每一层都会对请求进行特定的处理，然后将其传递给下一层。简而言之，借助中间件，一个React Agent的运行模型，就可以由这种：

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/core_agent_loop.png" alt="核心代理循环图" style="zoom:100%;" />

变为这种：

<center><img src="https://ml2022.oss-cn-hangzhou.aliyuncs.com/img/middleware_final.png" alt="中间件流程图" style="zoom:100%;" />

#### **中间件的作用**

&emsp;&emsp;中间件（Middleware）作为 Agent 运行时的「横切能力层」，负责在 模型调用、工具调用、状态流转 等关键环节之间插入可控的拦截与增强逻辑。它不改变 Agent 的核心推理机制，而是作为运行时治理与智能行为优化的重要组件，提供了比普通提示工程更系统、更可控的能力。它就像给 Agent 装上了 "可插拔的增强模块" ，让 AI 系统既能保持核心简洁，又能进行排列组合，根据企业需求自由组合出百变的超能力。它从工程角度解决了 Agent 不稳定、难调试、不安全、不可控、难复用 等长期痛点。

* 过去： Agent 的行为像一条笔直的高速公路，从用户提问到模型回答，所有车辆只能按固定路径行驶。一旦需要安全检查、成本限制或性能监控，只能在每个出口强行加装收费站，导致代码臃肿、逻辑混乱、难以维护。

* 现在： 中间件如同立体交通网络，在不修改主干道的前提下，在关键枢纽注入智能管控层，优雅地解决了五大顽疾：

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251203004252471.png" alt="中间件概念图" style="zoom:40%;" />

* 中间件主要解决了Agent在生产环境落地时的“不可控”问题：

    * 成本风险：1.上下文失控解决对话历史过长导致的Token溢出（通过自动摘要中间件）。2.根据用户提问的复杂度判断使用不同类型的模型

    * 安全风险：解决泄露（PII）手机号、身份证号等敏感信息、或恶意工具调用（通过审批中间件）。

    * 调试黑盒：解决Agent思考过程难以追踪的问题（通过监控中间件）。

    * 死循环：Agent 调用工具时可能陷入无限循环，调用中间件可以使系统会自动触发熔断。

#### **核心设计理念的深度解析**

&emsp;&emsp;中间件的设计严格遵循了 SOLID 原则，这些原则不仅仅是理论概念，而是实际指导开发的行动准则。

&emsp;&emsp;**单一职责原则**（Single Responsibility Principle：SRP）在中间件中得到了完美的体现。每一个中间件都专注于一个特定的横切关注点，比如 `SummarizationMiddleware` 只负责处理上下文压缩，`CostTrackingMiddleware` 只负责成本统计。这种设计使得每个中间件的职责边界清晰，便于测试、维护和重用。

&emsp;&emsp;**开闭原则**（Open/Closed Principle：OCP）的应用使得系统具备了良好的扩展性。`ModelSelectorMiddleware` 可以通过配置来支持不同的模型选择策略，而无需修改代码本身。这意味着当有新的模型或者新的选择策略出现时，我们可以通过配置文件来适应，而不是修改核心代码。

&emsp;&emsp;**里氏替换原则**（Liskov Substitution Principle：LSP）是子类必须能够替换其父类而不破坏程序的正确性，DatabaseAuthMiddleware 和 JWTAuthMiddleware 可互相替换，Agent 无差别运行。

&emsp;&emsp;**装饰器模式**（Interface Segregation Principle：ISP）是中间件架构中的核心模式。通过 `wrap_model_call`，我们可以在不修改原始 Agent 代码的情况下，为其添加额外的功能。这种无侵入性的扩展方式使得 Agent 的核心逻辑保持简洁，而功能的增强通过中间件来实现。

&emsp;&emsp;**责任链模式**（Dependency Inversion Principle：DIP）则体现在多个中间件的顺序处理中。每个中间件都有机会处理请求，然后将请求传递给下一个中间件。这种模式提供了极大的灵活性，我们可以根据具体需求调整中间件的执行顺序，甚至动态地添加或删除中间件。

#### **性能考量与优化策略**

&emsp;&emsp;在设计中间件时，性能是必须考虑的重要因素。不同的中间件类型对系统性能的影响是不同的。监控类中间件通常对性能影响最小，因为它们主要是记录信息而不进行复杂的处理。修改类中间件的影响相对较大，因为它们需要对数据进行处理和转换。控制类中间件可能会引入一些延迟，因为它们需要等待外部决策（如人工审批）。强制类中间件则可能涉及复杂的验证逻辑，对性能有一定影响。

&emsp;&emsp;优化策略需要从多个层面进行考虑。延迟优化可以通过异步处理来实现，对于那些不直接影响主流程的操作（如日志记录、性能统计），我们可以采用异步方式处理。批处理是另一个重要的优化手段，特别是对于那些需要对多个请求进行相似处理的中间件。

&emsp;&emsp;内存管理同样重要。中间件可能会创建大量的中间对象，如果管理不当，容易导致内存泄漏。对象池技术可以帮助我们重用常用的对象，减少创建和销毁的开销。

&emsp;&emsp;CPU 优化则需要从算法层面考虑。选择时间复杂度更低的算法可以显著提高性能。在可能的情况下，利用多核 CPU 进行并行处理也是一个有效的策略。

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251203004427606.png" alt="中间件性能热力图" style="zoom:35%;" />

| 中间件类型                                   | 典型场景           | 响应时间增加                       | 吞吐量衰减                        | 资源消耗                     | 性能瓶颈点                 | 优化策略             |
| -------------------------------------------- | ------------------ | ---------------------------------- | --------------------------------- | ---------------------------- | -------------------------- | -------------------- |
| **日志监控中间件**<br>`@after_model`         | 请求日志、指标统计 | **< 1 ms**                         | **< 5%**                          | CPU 1-3%<br>内存 10-50MB     | 磁盘 I/O<br>（异步后极小） | 异步写入、采样率 10% |
| **安全脱敏中间件**<br>`@before_model`        | PII 脱敏、权限检查 | **1-5 ms**                         | **5-10%**                         | CPU 5-10%<br>内存 20-100MB   | 正则表达式<br>字符串拷贝   | 编译缓存、原地修改   |
| **参数校验中间件**<br>`@before_model`        | 输入验证、格式检查 | **1-3 ms**                         | **3-8%**                          | CPU 3-8%<br>内存 10-30MB     | 复杂校验规则               | 缓存校验结果         |
| **对话总结中间件**<br>`@before_model`        | 长文本压缩         | **50-200 ms**                      | **15-30%**                        | CPU 20-40%<br>内存 100-500MB | 模型调用<br>token 计算     | 仅在消息数>10 触发   |
| **缓存中间件**<br>`@wrap_model_call`         | 结果缓存           | **0.5-2 ms**<br>（缓存命中）       | **-50% ~ +10%**<br>（命中时提升） | 内存 50-200MB                | 缓存命中率                 | LRU 策略、TTL 设置   |
| **模型降级中间件**<br>`@wrap_model_call`     | 动态切换模型       | **5-10 ms**                        | **10-15%**                        | CPU 2-5%<br>内存 10-20MB     | 模型初始化<br>API 调用     | 模型池化、预热       |
| **限流中间件**<br>`@wrap_model_call`         | QPS 限制、熔断     | **0.1-1 ms**                       | **< 5%**                          | CPU 1-2%<br>内存 5-10MB      | 原子计数器<br>锁竞争       | 滑动窗口算法         |
| **工具审计中间件**<br>`@wrap_tool_call`      | 调用记录、熔断     | **2-8 ms**                         | **8-15%**                         | CPU 5-12%<br>内存 30-80MB    | 数据库写入<br>网络请求     | 异步批量写入         |
| **工具重试中间件**<br>`@wrap_tool_call`      | 失败重试           | **10-50 ms**<br>（视重试次数）     | **20-50%**                        | CPU 10-20%<br>内存 20-50MB   | 重试延迟<br>指数退避       | 限制重试次数≤3       |
| **外部 API 调用中间件**<br>`@wrap_tool_call` | 调用第三方服务     | **100-500 ms**<br>（网络延迟主导） | **30-70%**                        | CPU 5-10%<br>内存 10-30MB    | 网络 I/O<br>超时设置       | 连接池、超时 3s      |
| **消息队列中间件**<br>`@before_model`        | 异步任务解耦       | **5-20 ms**<br>（仅入队）          | **10-25%**                        | CPU 10-15%<br>内存 50-150MB  | 消息序列化<br>队列持久化   | 批量发送、压缩       |
| **注册中心中间件**<br>`@before_agent`        | 服务发现           | **10-30 ms**<br>（首次查询）       | **5-15%**                         | CPU 5-10%<br>内存 20-60MB    | DNS 查询<br>缓存过期       | 本地缓存 60s         |

### **中间件的分类与应用场景**

#### 中间件四大分类

&emsp;&emsp;中间件的四大分类——监控类、修改类、控制类和强制类——每一种都有其独特的定位和应用场景。这种分类不是人为的划分，而是基于实际需求和功能特性的自然归类。

| **分类**             | **核心功能**              | **解决的问题**             | **典型应用场景**                                             |
| -------------------- | ------------------------- | -------------------------- | ------------------------------------------------------------ |
| **Monitor (监控类)** | 观察执行状态、日志记录    | 调试困难、缺乏可观测性     | 记录所有的Prompt和Response、性能分析、成本核算。             |
| **Modify (修改类)**  | 修改输入/输出、上下文管理 | 上下文窗口溢出、Prompt优化 | **SummarizationMiddleware**（自动压缩历史对话）、动态注入System Prompt。 |
| **Control (控制类)** | 流程阻断、人工介入        | AI幻觉、高风险操作失控     | **HumanInTheLoopMiddleware**（敏感操作需人工审批）、重试机制。 |
| **Enforce (强制类)** | 安全过滤、限流、合规检查  | 数据泄露、API滥用          | **PIIMiddleware**（敏感信息脱敏）、**ModelCallLimit**（防止死循环）。 |

&emsp;&emsp;**1.监控类中间件**是最基础也是最重要的类型。它们像是系统的"观察者"，默默记录着系统运行的每一个细节。性能监控中间件不仅记录响应时间和资源使用，更重要的是它们能够自动检测性能异常，就像一个细心的医生能够从细微的症状中发现潜在的问题。成本追踪中间件则像是系统的"会计师"，精确记录着每一个 Token 的消耗，帮助团队了解系统的真实运营成本。

&emsp;&emsp;**2.修改类中间件**是系统的"优化师"。它们不仅仅是记录信息，更重要的是它们能够主动改变数据的处理方式。智能摘要中间件是最典型的例子，它们通过复杂的算法分析对话内容，保留最重要的信息，过滤掉冗余的内容。这就像是一个经验丰富的信息处理专家，能够在保持信息完整性的同时，最大程度地减少处理成本。

&emsp;&emsp;**3.控制类中间件**是系统的"指挥官"。它们负责管理系统的行为，确保所有操作都在预定的规则范围内进行。人工介入中间件通过智能识别需要人工审批的敏感操作，在保持系统自动化的同时，确保关键操作的安全性。流量控制中间件则像是交通指挥员，确保系统的"流量"不会超出承受能力。

&emsp;&emsp;**4.强制类中间件**是系统的"守护者"。它们负责保护系统免受各种威胁，安全强制执行中间件就像是系统的安保系统，对每一个输入输出进行全方位的安全检查。合规检查中间件则像是法律顾问，确保系统的所有操作都符合相关法规要求。

#### 深入生命周期 - 中间件的 6 个切入点 (Hooks)

##### Hook 执行顺序的深层逻辑

&emsp;&emsp;中间件的 6 个 Hook 点——before_agent、before_model、wrap_model_call、wrap_tool_call、after_model 和 after_agent——不仅仅是一个执行顺序，更是一个精心设计的数据流处理流程。这个流程体现了从输入处理到输出生成的完整生命周期。

&emsp;&emsp;在 Agent 执行的最开始，**before_agent** Hook 提供了全局初始化的机会。这个阶段通常用于设置全局状态、检查环境配置、初始化资源等。就像一个大型演出的开场准备，确保所有必要的准备工作都已经就绪。

&emsp;&emsp;**before_model** 阶段是输入预处理的关键节点。在这个阶段，中间件可以对输入数据进行预处理、验证、清洗等操作。这是确保数据质量的第一道防线，任何在这个阶段发现的问题都可以避免后续的无谓计算。

&emsp;&emsp;**wrap_model_call** 是最核心的 Hook，它包装了实际的模型调用过程。这个阶段的处理逻辑决定了如何与底层模型交互，是实现高级功能（如缓存、重试、熔断等）的关键位置。

&emsp;&emsp;**wrap_tool_call** 是用于拦截和控制工具的实际执行过程的Hook，它包装了每次工具调用。这个阶段的处理逻辑可以是权限、重试、日志、审批。

&emsp;&emsp;**after_model** 阶段则处理模型返回的原始结果。这个阶段的任务是验证输出质量、进行格式转换、提取关键信息等。由于模型输出往往包含大量无用信息，这个阶段的处理对于提高整体效率至关重要。

&emsp;&emsp;最后的 **after_agent** 阶段是整个生命周期的收尾工作。在这个阶段，系统需要清理资源、记录最终状态、生成报告等。这是确保系统处于良好状态，为下一次请求做好准备的关键步骤。

##### 数据传递机制的复杂性

&emsp;&emsp;Hook 间的数据传递是一个精妙而复杂的机制。每个 Hook 都能访问和修改共享的上下文对象，这个对象就像是整个处理过程的"记忆"。上下文对象不仅包含请求信息和响应数据，还包含运行时状态、中间计算结果、元数据等。

&emsp;&emsp;元数据传递机制允许中间件在不直接共享状态的情况下传递信息。例如，一个中间件可以在元数据中标记某个输入是 VIP 用户的请求，后续的中间件可以根据这个标记来调整处理策略。

&emsp;&emsp;状态管理是另一个重要方面。中间件需要维护状态，但这些状态可能会因为各种原因而发生变化。错误处理机制、回滚机制、事务性操作等都需要在状态管理中得到体现。

##### 高级 Hook 使用模式的深度解析

&emsp;&emsp;在实际应用中，Hook 的使用往往比基本的执行顺序更加复杂。**条件 Hook 执行**是高级使用模式中最常见的一种。它通过智能的条件判断来决定是否执行特定的 Hook，这样可以提高处理效率，避免不必要的计算。

&emsp;&emsp;想象一个场景：一个电商推荐系统的 Agent。对于 VIP 用户，系统可能需要启用更复杂的推荐算法、调用更多的数据源、提供更个性化的服务。而对普通用户，则可以使用更简单、更快速的推荐策略。这种差异化的处理需要通过条件 Hook 来实现。

&emsp;&emsp;**错误恢复 Hook**的设计体现了系统的韧性。不同层级的错误需要不同的恢复策略。有些错误可以通过简单的重试来解决，有些错误需要切换到备用模型，还有些错误需要人工介入。通过在不同 Hook 层级实现恢复机制，系统可以在不同层次上处理错误，提高整体的可靠性。

&emsp;&emsp;**性能优化 Hook**则关注系统的运行效率。缓存 Hook 通过在 `wrap_model_call` 阶段检查缓存来决定是否直接返回缓存结果，避免重复的模型调用。预加载 Hook 则通过预测用户需求，提前加载可能需要的数据和资源。

### 中间件集成工具使用

```python
!python --version
```

```python
!pip list | grep langchain
```

#### before_model 模型调用前

<center><img src="https://zrj18330672592.oss-cn-beijing.aliyuncs.com/20251203102617580.png" alt="before_model" style="zoom:80%;" />

SummarizationMiddleware 上下文压缩