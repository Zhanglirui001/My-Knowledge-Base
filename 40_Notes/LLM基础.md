# LLM基础

----

### 大模型接入 chat Completions API

---

#### 环境与依赖安装

```python
!pip install openai transformers tiktoken python-dotenv requests httpx
```

**包说明**：

- `openai`: OpenAI Python 官方 SDK，用于调用大模型 API

- `transformers`: Hugging Face Transformers 库，用于加载 tokenizer

- `tiktoken`: OpenAI 官方 tokenizer 工具

- `python-dotenv`: 环境变量加载工具,加载 .env 文件中的环境变量

- `requests`: HTTP 请求库

- `httpx`: HTTP 客户端库（支持异步）

**查看当前版本**：

```python
# 查看已安装的依赖包版本
import importlib.metadata

# 定义需要检查的包列表
packages = ['openai', 'transformers', 'tiktoken', 'python-dotenv', 'requests', 'httpx']

# 循环检查每个包的版本
for package in packages:
    try:
        version = importlib.metadata.version(package)
        print(f'{package:<20} v{version}')
    except importlib.metadata.PackageNotFoundError:
        print(f'{package:<20} 未安装')
```

&emsp;&emsp;如果导入成功并显示版本号，说明依赖库已经正确安装。`openai` 库的版本应该在 1.0 以上，这是支持最新 API 格式的版本。

**配置 .env 文件**

&emsp;&emsp;现在我们需要在 `.env` 文件中，存储所有在第1章中获取的 API Key。这个文件应该放在项目根目录，内容如下：

```python
# 示例：创建 .env 文件（实际使用时请替换为真实的 API Key）
env_content = """
# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx

# DeepSeek API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 阿里云百炼 API Key
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 智谱 AI API Key
ZHIPUAI_API_KEY=xxxxxxxxxxxxxxxx
"""

# 写入 .env 文件
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content.strip())

print("✅ .env 文件已创建，请替换为你的真实 API Key")
```

#### 第一个API调用

---

现在环境已经准备就绪，我们将编写第一个真正的 API 调用代码。我们选择 DeepSeek 作为起点，因为它<font color=red>注册简单、免费额度充足、响应速度快</font>，非常适合新手练习。

&emsp;通过一个最简单的"问答"任务：向模型提问"你是谁？"，并接收模型的回复。通过这个例子，你将理解 API 调用的核心流程、消息结构，以及如何解析响应结果。

&emsp;&emsp;下面是一个完整的 API 调用示例。我们会使用 DeepSeek 的 `deepseek-chat` 模型，向它提问"你是谁？"：

```python
from openai import OpenAI

# 创建客户端，指向 DeepSeek 平台
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 调用 API
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "你是谁？"}
    ]
)

# 提取回复内容
answer = response.choices[0].message.content
print("模型回复：")
print(answer)
```

&emsp;&emsp;这段代码完成了以下几个关键步骤：

1. **创建客户端**：使用 `OpenAI()` 创建一个客户端对象，通过 `api_key` 指定身份凭证，通过 `base_url` 指定 DeepSeek 的 API 地址。

2. **构造请求**：调用 `client.chat.completions.create()`，指定模型名称和消息列表。

3. **解析响应**：从 `response.choices[0].message.content` 中提取模型生成的文本。

&emsp;&emsp;运行后，你应该会看到类似"我是 DeepSeek，一个由深度求索开发的 AI 助手..."这样的回复。这标志着你已经成功完成了第一次 API 调用！

**三角色对话模型**

&emsp;&emsp;在上面的代码中，`messages` 参数是一个列表，包含了对话中的所有消息。<font color=red>每条消息都是一个字典，必须包含 `role` 和 `content` 两个字段</font>。

&emsp;&emsp;OpenAI API 定义了三种角色：

- **`system`**：系统角色，用于设定 AI 的行为规范、角色定位、回复风格等。这是"幕后导演"，用户看不到，但会影响整个对话的基调。

- **`user`**：用户角色，代表人类的提问或输入。

- **`assistant`**：助手角色，代表 AI 的回复。在构造多轮对话时，需要手动添加历史回复。

&emsp;&emsp;让我们通过一个更完整的例子来理解这三种角色的作用：

```python
# 使用三角色构造一个完整的对话
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一位专业的 Python 编程导师，擅长用简洁明了的语言解释复杂概念。"},
        {"role": "user", "content": "什么是列表推导式？"},
    ]
)

print("模型回复：")
print(response.choices[0].message.content)
```

&emsp;&emsp;在这个例子中，我们通过 `system` 消息告诉模型："你是一位 Python 导师"。这会影响模型的回复风格——它会倾向于用教学的口吻、提供代码示例、避免过于学术化的表达。

&emsp;&emsp;`system` 消息的作用非常强大，可以用来：

- 设定角色（如"你是一位律师"、"你是一位翻译专家"）

- 规定输出格式（如"请用 JSON 格式回复"、"只回答是或否"）

- 限制回复范围（如"只回答 Python 相关问题"）

- 设定语言和风格（如"用口语化的方式回复"、"用英文回复"）

&emsp;&emsp;在实际应用中，<font color=red>合理使用 `system` 消息可以显著提升 AI 的回复质量和可控性</font>。

**解析相应结果：理解response对象**

&emsp;&emsp;API 返回的 `response` 对象包含了丰富的信息。让我们完整地查看一下它的结构：

```python
# 完整查看 response 对象
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "用一句话介绍 Python"}]
)

print("=" * 60)
print("Response 对象结构：")
print("=" * 60)
print(f"模型名称: {response.model}")
print(f"响应 ID: {response.id}")
print(f"创建时间: {response.created}")
print(f"对象类型: {response.object}")
print()
print("消息内容:")
print(f"  角色: {response.choices[0].message.role}")
print(f"  内容: {response.choices[0].message.content}")
print()
print("Token 使用情况:")
print(f"  输入 Token: {response.usage.prompt_tokens}")
print(f"  输出 Token: {response.usage.completion_tokens}")
print(f"  总计 Token: {response.usage.total_tokens}")
```

#### 核心参数调优

---

在掌握了基本的 API 调用流程后，现在我们需要学习如何通过参数来控制模型的行为。<font color=red>最重要的两个参数是 `temperature` 和 `max_tokens`</font>——前者控制输出的随机性和创造性，后者限制输出的最大长度。

&emsp;&emsp;理解并合理使用这两个参数，可以让你精确控制模型的输出风格和成本。不同的应用场景需要不同的参数配置：严肃的文档生成需要低 temperature，创意写作需要高 temperature；简短回复需要小 max_tokens，长文本生成需要大 max_tokens。

&emsp;&emsp;`temperature` 参数控制模型输出的随机性，取值范围通常是 0 到 2（有些平台支持更高值）：

- **temperature = 0**：输出最确定，每次运行结果几乎相同，适合需要稳定输出的场景（如数据提取、代码生成）

- **temperature = 0.7**（默认值）：平衡了创造性和稳定性，适合大多数场景

- **temperature = 1.5 或更高**：输出高度随机和创造性，适合创意写作、头脑风暴

&emsp;&emsp;让我们通过对比实验来理解 temperature 的影响：

```python
# 对比不同 temperature 的输出
prompt = "用一句话描述春天"

# 定义待测试的不同温度值，用于对比输出的随机性
temperatures = [0, 0.7, 1.5]

for temp in temperatures:
    # 调用 API，传入不同的 temperature 参数
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=temp
    )
    
    # 格式化打印输出结果，便于观察对比
    print(f"\n{'='*60}")
    print(f"Temperature = {temp}")
    print(f"{'='*60}")
    print(response.choices[0].message.content)
```

&emsp;&emsp;在实际应用中，推荐的 temperature 配置：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>不同场景的 Temperature 推荐值</font></p>
<div class="center">

| 应用场景           | 推荐值    | 原因                         |
| ------------------ | --------- | ---------------------------- |
| 数据提取、信息查询 | 0 - 0.3   | 需要准确、一致的结果         |
| 代码生成、翻译     | 0.3 - 0.5 | 需要确定性，但允许少量灵活性 |
| 对话、问答         | 0.7 - 1.0 | 平衡准确性和自然度           |
| 创意写作、头脑风暴 | 1.2 - 2.0 | 需要多样性和创造性           |



&emsp;&emsp;`max_tokens` 参数限制模型生成的最大 Token 数量。<font color=red>这是控制成本的关键参数</font>，因为输出 Token 的价格通常比输入高 3-5 倍。

&emsp;&emsp;需要注意的是：
- `max_tokens` 只是**上限**，模型可能生成更短的内容

- 如果回复在达到 `max_tokens` 时被截断，`response.choices[0].finish_reason` 会是 `"length"`

- 不同语言的 Token 消耗不同（回顾第1.1节：中文约 1.5-2 Token/字，英文约 0.75 Token/词）

&emsp;&emsp;让我们通过实验来理解 `max_tokens` 的作用：

```python
# 测试不同 max_tokens 的效果
prompt = "详细介绍 Python 的历史发展"

# 定义不同的最大 token 限制进行测试
token_limits = [50, 200, 500]

for max_tok in token_limits:
    # 调用 API，通过 max_tokens 参数限制生成内容的长度上限
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tok      # 注意：max_tokens 仅为上限，模型可能提前结束生成
    )
    
    # 解析响应中的内容、结束原因及实际消耗的 token 数
    content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason
    actual_tokens = response.usage.completion_tokens
    
    # 打印格式化的输出结果及元数据
    print(f"\n{'='*60}")
    print(f"max_tokens = {max_tok}")
    print(f"实际输出 Token: {actual_tokens}")
    print(f"结束原因: {finish_reason}")
    print(f"{'='*60}")
    print(content)
    
    # 判断是否因达到 token 上限而导致内容未生成完毕
    if finish_reason == "length":
        print("\n⚠️ 输出被截断！考虑增加 max_tokens")
```

&emsp;&emsp;从输出可以看到：

- 当 `max_tokens=50` 时，回复明显被截断，`finish_reason` 为 `"length"`

- 当 `max_tokens=200` 时，可能刚好够用，或仍然被截断

- 当 `max_tokens=500` 时，回复通常能够完整，`finish_reason` 为 `"stop"`（模型主动结束）

&emsp;&emsp;在实际应用中，推荐的 `max_tokens` 配置策略：

- **简短回复（摘要、标题）**：50-100 tokens

- **中等回复（问答、对话）**：200-500 tokens

- **长文本生成（文章、报告）**：1000-4000 tokens

- **如果不确定长度**：可以设置较大值（如 2000），让模型自行决定何时结束

> &emsp;**成本优化技巧**：如果只需要简短回复，务必设置合理的 `max_tokens`，避免模型生成不必要的长文本浪费费用。

### &emsp;多平台兼容

---

 OpenAI SDK 兼容格式的概念。现在是时候实践这个强大的特性了——<font color=red>通过修改 `api_key`、`base_url` 和 `model` 三个参数，我们可以用同一套代码调用不同平台的模型</font>。

&emsp;&emsp;这一节我们会演示如何快速切换 DeepSeek、OpenRouter、阿里百炼、智谱 AI 等平台，并通过配置字典的方式实现批量测试。掌握这个技巧后，你可以轻松对比不同模型的能力和价格。

```python
# 多平台配置字典
PLATFORM_CONFIGS = {
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat"
    },
    "openrouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-5-mini"  # 使用免费或低价模型
    },
    "dashscope": {
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo"
    },
    "zhipu": {
        "api_key": os.getenv("ZHIPUAI_API_KEY"),
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4"
    }
}

print("✅ 平台配置字典已创建")
```

&emsp;&emsp;有了这个配置字典，我们可以编写一个通用的调用函数：

```python
def call_llm(platform_name, prompt, temperature=0.7, max_tokens=200):
    """
    通用的大模型调用函数
    
    Args:
        platform_name: 平台名称（deepseek/openrouter/dashscope/zhipu）
        prompt: 用户输入
        temperature: 温度参数
        max_tokens: 最大输出 Token 数
    
    Returns:
        模型回复内容
    """
    # 获取对应平台的配置信息
    config = PLATFORM_CONFIGS[platform_name]
    
    # 初始化 OpenAI 客户端（大多数国产大模型 API 均兼容 OpenAI 格式）
    client = OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"]
    )
    
    # 调用大模型聊天接口
    response = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # 返回模型生成的文本内容
    return response.choices[0].message.content

# 测试：使用相同 prompt 调用不同平台
test_prompt = "用一句话解释什么是 AI"

print("使用 dashscope:")
print(call_llm("dashscope", test_prompt))
print("\n" + "="*60 + "\n")
```

#### 流式输出

---

&emsp;&emsp;在前面的所有示例中，我们都是等待模型生成完整回复后才显示结果。但在实际应用中（如聊天机器人、AI 助手），<font color=red>用户更希望看到"打字机效果"——文字逐字逐句出现</font>，而不是长时间等待后突然显示一大段文字。

&emsp;&emsp;OpenAI API 提供了 **流式输出（Streaming）** 功能，通过设置 `stream=True`，可以让模型边生成边返回内容。这不仅提升了用户体验，还能让用户在生成过程中提前终止，节省成本。

```python
import time

# 创建客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 流式调用
print("模型正在生成回复（流式输出）：\n")

stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "用三句话介绍人工智能的发展历程"}],
    stream=True  # 启用流式输出
)

# 逐块接收并打印
for chunk in stream:
    # 提取增量内容
    delta_content = chunk.choices[0].delta.content
    
    if delta_content:
        print(delta_content, end="", flush=True)  # 实时打印，不换行
        time.sleep(0.1)  # 模拟打字机效果（可选）

print("\n\n✅ 流式输出完成")
```

&emsp;&emsp;这段代码的关键点：

1. **`stream=True`**：告诉 API 使用流式模式返回结果

2. **迭代 stream 对象**：返回值是一个迭代器，每次返回一小块内容

3. **`chunk.choices[0].delta.content`**：提取增量内容（注意是 `delta` 而不是 `message`）

4. **`print(..., end="", flush=True)`**：实时打印不换行，`flush=True` 确保立即显示

&emsp;&emsp;运行后，你会看到文字逐字出现，体验类似 ChatGPT 的打字机效果。

**流式输出的完整处理**

&emsp;&emsp;在实际应用中，我们通常需要在流式输出的同时保存完整内容，以便后续处理。下面是一个更完整的示例：

```python
def stream_chat(prompt, model="deepseek-chat"):
    """
    流式聊天函数，边生成边显示，同时返回完整内容
    
    Args:
        prompt: 用户输入
        model: 模型名称
    
    Returns:
        完整的生成内容
    """
    # 初始化 OpenAI 客户端，配置 DeepSeek 的 API Key 和 Base URL
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    # 发起流式对话请求，开启 stream 模式
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    # 用于保存完整内容
    full_content = ""  
    
    print("AI: ", end="", flush=True)
    
    # 遍历流式响应
    for chunk in stream:
        delta_content = chunk.choices[0].delta.content
        
        # 如果有内容，打印并保存
        if delta_content:
            print(delta_content, end="", flush=True)
            full_content += delta_content
    
    print("\n")  # 换行
    
    return full_content

# 测试
user_input = "写一个 Python 的 Hello World 程序"
result = stream_chat(user_input)

print(f"完整内容已保存，共 {len(result)} 个字符")
```

&emsp;&emsp;这个封装后的函数同时实现了：
- 实时显示流式输出（用户体验）
- 保存完整内容（便于后续处理）
- 返回生成结果（可用于日志、数据库存储等）

&emsp;&emsp;流式输出特别适合以下场景：
- **聊天机器人**：用户看到逐字生成，体验更自然
- **长文本生成**：用户可以边看边等，不会觉得卡顿
- **交互式应用**：用户可以在生成过程中判断是否继续等待

> &emsp;**注意**：流式模式下无法直接获取 `usage` 信息（Token 统计），如果需要统计成本，建议在非流式模式下测试，或使用第1.1节介绍的 tiktoken 本地估算。

#### **错误处理**

---

&emsp;&emsp;在实际应用中，API 调用可能遇到各种异常：<font color=red>API Key 错误、余额不足、网络超时、请求频率超限</font>等。如果不做错误处理，程序会直接崩溃，用户体验极差。

&emsp;&emsp;这一节我们会学习如何优雅地处理这些异常，包括分类捕获不同错误、实现自动重试机制，以及提供友好的错误提示。掌握这些技巧后，你的应用将更加健壮和可靠。

**常见错误类型与分类捕获**

&emsp;&emsp;OpenAI SDK 定义了多种异常类型，我们可以分类捕获并给出不同的处理方式：

```python
from openai import (
    OpenAI,
    AuthenticationError,  # 认证错误（API Key 无效）
    RateLimitError,       # 速率限制错误（请求过快）
    APIConnectionError,   # 网络连接错误
    APIError              # 通用 API 错误
)

def safe_call_llm(prompt, max_retries=3):
    """
    带错误处理的 API 调用
    
    Args:
        prompt: 用户输入
        max_retries: 最大重试次数
    
    Returns:
        模型回复或错误信息
    """
    # 初始化 OpenAI 客户端，配置 DeepSeek 的 API Key 和 Base URL
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    # 循环尝试 API 调用，最多重试 max_retries 次
    for attempt in range(max_retries):
        try:
            # 发起 API 调用
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0  # 设置超时时间（秒）
            )
            return response.choices[0].message.content
        
        except AuthenticationError as e:
            # 认证错误，无需重试
            return f"❌ API Key 无效或已过期，请检查环境变量配置"
        
        except RateLimitError as e:
            # 速率限制，等待后重试
            wait_time = 2 ** attempt  # 指数退避：1秒、2秒、4秒...
            print(f"⚠️ 请求过快，等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            continue
        
        except APIConnectionError as e:
            # 网络错误，重试
            print(f"⚠️ 网络连接失败（第 {attempt+1}/{max_retries} 次），重试中...")
            time.sleep(1)
            continue
        
        except APIError as e:
            # 通用 API 错误
            return f"❌ API 调用失败: {str(e)}"
        
        except Exception as e:
            # 其他未知错误
            return f"❌ 未知错误: {str(e)}"
    
    return f"❌ 重试 {max_retries} 次后仍然失败，请检查网络或稍后再试"

# 测试错误处理
test_prompt = "用一句话介绍一下 Python"
result = safe_call_llm(test_prompt)
print(result)
```

&emsp;&emsp;这个函数实现了以下错误处理策略：

- **AuthenticationError**：API Key 无效，直接返回错误提示，不重试（因为重试也无意义）

- **RateLimitError**：请求频率超限，使用**指数退避**策略重试（等待时间逐次翻倍）

- **APIConnectionError**：网络连接失败，等待 1 秒后重试

- **APIError**：通用 API 错误，返回具体错误信息

- **Exception**：兜底捕获所有未知错误

&emsp;&emsp;指数退避（Exponential Backoff）是一种常用的重试策略：首次重试等待 1 秒，第二次等待 2 秒，第三次等待 4 秒……这样可以避免在高峰期持续发送请求加剧服务器压力。

**常见错误场景与排查方法**

&emsp;&emsp;在实际使用中，你可能会遇到以下错误场景。我们通过一个对比表格来总结常见错误及其解决方法：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>常见 API 错误与排查方法</font></p>
<div class="center">

| 错误类型                      | 典型提示            | 可能原因               | 解决方法                      |
| ----------------------------- | ------------------- | ---------------------- | ----------------------------- |
| **401 Unauthorized**          | Invalid API Key     | API Key 错误或过期     | 检查 .env 文件，确认 Key 正确 |
| **429 Rate Limited**          | Rate limit exceeded | 请求频率过快           | 降低请求频率，或升级套餐      |
| **400 Bad Request**           | Invalid model name  | 模型名称错误           | 查阅平台文档，确认模型名      |
| **500 Internal Server Error** | Server error        | 平台服务异常           | 等待一段时间后重试            |
| **Timeout**                   | Request timeout     | 网络慢或模型响应慢     | 增加 timeout 参数，或优化网络 |
| **Insufficient Balance**      | Quota exceeded      | 余额不足或免费额度用完 | 充值或等待额度刷新            |

</div>

&emsp;&emsp;当遇到错误时，推荐的排查步骤：

**步骤一：查看完整错误信息**

&emsp;&emsp;不要只看错误类型，完整的错误信息通常包含了具体原因。可以通过 `str(e)` 打印完整错误：

```python
except APIError as e:
    print(f"完整错误信息: {str(e)}")
```

**步骤二：检查基础配置**

- API Key 是否正确（复制时没有多余空格）

- base_url 是否正确（注意 http/https、末尾是否有斜杠）

- model 名称是否正确（区分大小写）

**步骤三：测试网络连接**

&emsp;&emsp;可以用简单的测试验证网络是否通畅：

```python
import requests
import os

# 获取 API Key (建议从环境变量获取，或者直接填入)
# api_key = "sk-xxxxxxxxxxxx" 
api_key = os.getenv("DEEPSEEK_API_KEY") 

if not api_key:
    print("错误：未找到 API Key")
else:
    # DeepSeek 基础 URL
    base_url = "https://api.deepseek.com"
    
    # 构造请求头，注意 Bearer 后面的空格
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # 尝试访问 /models 端点，这是标准的验证连接方式
        response = requests.get(f"{base_url}/models", headers=headers)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("连接成功！可用模型列表:", response.json())
        else:
            print("连接失败:", response.text)
            
    except Exception as e:
        print(f"发生错误: {e}")
```

**步骤四：查看平台控制台**

&emsp;&emsp;登录平台控制台，查看：
- 余额是否充足

- API Key 是否被禁用

- 是否有调用记录（如果有，说明网络和认证都正常）

&emsp;&emsp;通过这些步骤，大部分问题都能快速定位和解决。

### Chat Completions API进阶使用

---

&emsp;&emsp;在掌握了基础的 API 调用流程后，现在我们需要解锁更高级的功能，让你的应用能够实现更复杂、更智能的交互。<font color=red>这一章我们会学习五个进阶能力：多轮对话、Function Calling、多模态输入、提示词工程、异步批处理</font>。

&emsp;&emsp;这些能力是构建实用 AI 应用的关键。

* 多轮对话让 AI 能够记住上下文，实现连贯的交流；

* Function Calling 让 AI 能够调用外部工具，突破纯文本生成的限制；

* 多模态输入让 AI 能够"看图说话"，理解视觉信息；

* 提示词工程教你如何写出高质量的 Prompt，最大化模型能力；

* 异步批处理则通过并发调用大幅提升效率。

&emsp;&emsp;掌握这些技能后，你将能够构建真正实用的 AI 应用——从简单的聊天机器人，到能查询天气、搜索信息的智能助手，再到能分析图片、生成报告的多模态应用。让我们开始这段进阶之旅。

#### 多轮对话

---

&emsp;&emsp;在第3章的所有示例中，我们都是单轮对话——提一个问题，得到一个回答，然后结束。但在实际应用中，<font color=red>用户往往希望 AI 能够记住之前的对话内容，实现连贯的多轮交互</font>。

&emsp;&emsp;例如，用户可能先问"北京的天气怎么样？"，然后问"那上海呢？"。第二个问题中的"上海"指的是"上海的天气"，需要结合上文理解。如果 AI 没有上下文记忆，就无法正确回答。

&emsp;&emsp;实现多轮对话的核心思路是：<font color=red>将历史对话以 `messages` 列表的形式传递给 API</font>。每次调用时，都把之前的所有消息（包括用户的提问和 AI 的回复）一起发送，这样模型就能"看到"完整的对话历史。

**基础多轮对话实现**

&emsp;&emsp;让我们通过一个完整的例子来理解多轮对话的实现逻辑：

```python
# 初始化对话历史
conversation_history = [
    {"role": "system", "content": "你是一位友好的 AI 助手，擅长回答各种问题。"}
]

# 创建客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 第一轮对话
user_message_1 = "我叫张三，今年25岁"
conversation_history.append({"role": "user", "content": user_message_1})

# 调用 API 获取第一轮对话回复
response_1 = client.chat.completions.create(
    model="deepseek-chat",
    messages=conversation_history
)

# 提取并保存 AI 的回复内容
assistant_message_1 = response_1.choices[0].message.content

# 将 AI 的回复添加到对话历史中，以维持上下文连贯性
conversation_history.append({"role": "assistant", "content": assistant_message_1})

# 打印第一轮对话的用户输入和 AI 回复
print(f"用户: {user_message_1}")
print(f"AI: {assistant_message_1}\n")

# 第二轮对话（测试是否记住了用户信息）
user_message_2 = "我叫什么名字？"
conversation_history.append({"role": "user", "content": user_message_2})

# 调用 API 获取第二轮对话回复
response_2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=conversation_history
)

# 提取并保存 AI 的回复内容
assistant_message_2 = response_2.choices[0].message.content
conversation_history.append({"role": "assistant", "content": assistant_message_2})

print(f"用户: {user_message_2}")
print(f"AI: {assistant_message_2}\n")

# 查看完整的对话历史
print("=" * 60)
print("完整对话历史：")
print("=" * 60)
for i, msg in enumerate(conversation_history):
    print(f"{i}. [{msg['role']}] {msg['content']}")
```

&emsp;&emsp;这段代码展示了多轮对话的核心逻辑：

1. **初始化对话历史**：创建一个列表 `conversation_history`，包含 system 消息

2. **每次用户提问前**：将用户消息追加到 `conversation_history`

3. **调用 API**：将完整的 `conversation_history` 传递给模型

4. **收到回复后**：将 AI 的回复也追加到 `conversation_history`

&emsp;&emsp;这样，每次调用 API 时，模型都能"看到"完整的对话历史，从而实现上下文记忆。在第二轮对话中，AI 能够正确回答"你叫张三"，说明它成功记住了第一轮对话的内容。

**交互式多轮对话**

&emsp;&emsp;在实际应用中，我们通常需要一个循环，让用户可以持续输入，AI 持续回复。下面是一个更实用的交互式多轮对话示例：

```python
def chat_loop(system_prompt="你是一位友好的 AI 助手。", max_rounds=5):
    """
    交互式多轮对话函数
    
    Args:
        system_prompt: 系统提示词
        max_rounds: 最大对话轮数
    """
    # 初始化对话历史
    conversation_history = [
        {"role": "system", "content": system_prompt}
    ]
    
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    print("=" * 60)
    print("多轮对话开始（输入 'quit' 退出）")
    print("=" * 60)
    
    for round_num in range(1, max_rounds + 1):
        # 获取用户输入
        user_input = input(f"\n[轮次 {round_num}] 你: ").strip()
        
        # 检查是否退出
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n对话已结束")
            break
        
        if not user_input:
            print("输入不能为空，请重新输入")
            continue
        
        # 添加用户消息到历史
        conversation_history.append({"role": "user", "content": user_input})
        
        # 调用 API
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=conversation_history,
                max_tokens=300
            )
            
            assistant_message = response.choices[0].message.content
            
            # 添加 AI 回复到历史
            conversation_history.append({"role": "assistant", "content": assistant_message})
            
            print(f"\nAI: {assistant_message}")
            print(f"\n[Token 消耗] 输入: {response.usage.prompt_tokens}, "
                  f"输出: {response.usage.completion_tokens}, "
                  f"总计: {response.usage.total_tokens}")
        
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            # 移除刚才添加的用户消息
            conversation_history.pop()
            continue
    
    return conversation_history

# 运行对话（在 Jupyter Notebook 中可以交互）
# 注意：这个函数需要用户输入，如果在 Notebook 中运行，会弹出输入框
# history = chat_loop(max_rounds=3)

print("✅ 交互式对话函数已定义，可以调用 chat_loop() 开始对话")
```

✅ 交互式对话函数已定义，可以调用 chat_loop() 开始对话

```python
history = chat_loop(max_rounds=3)
```

&emsp;&emsp;这个函数实现了一个完整的多轮对话循环，包括：

- **输入验证**：检查用户输入是否为空

- **退出机制**：用户输入 `quit` 或 `exit` 可以退出

- **错误处理**：如果 API 调用失败，撤销刚才添加的消息

- **Token 统计**：每轮对话后显示 Token 消耗

&emsp;&emsp;使用这个函数，你可以快速构建一个简单的聊天机器人。只需调用 `chat_loop()`，然后在弹出的输入框中与 AI 对话即可。

**上下文长度管理：滑动窗口与摘要压缩**

&emsp;&emsp;多轮对话虽然强大，但也带来了一个严重的问题：<font color=red>随着对话轮数增加，`conversation_history` 会越来越长，消耗的 Token 也会急剧增加</font>。

&emsp;&emsp;假设每轮对话平均消耗 100 个 Token（输入 + 输出），那么：

- 第 1 轮：100 tokens

- 第 2 轮：200 tokens（包含第 1 轮的历史）

- 第 3 轮：300 tokens

- 第 10 轮：1000 tokens

&emsp;&emsp;可以看到，<font color=red>Token 消耗呈线性增长，成本也随之上升</font>。更严重的是，当对话历史超过模型的上下文限制（如 128K tokens），API 调用会直接失败。

&emsp;&emsp;解决这个问题有两种常用策略：

**策略一：滑动窗口（Sliding Window）**

&emsp;&emsp;只保留最近 N 轮对话，丢弃更早的历史。这是最简单的方法：

```python
def manage_conversation_history(history, max_turns=5):
    """
    使用滑动窗口管理对话历史
    
    Args:
        history: 对话历史列表
        max_turns: 保留的最大对话轮数（不包括 system 消息）
    
    Returns:
        压缩后的对话历史
    """
    # 提取 system 消息（通常是第一条）
    system_messages = [msg for msg in history if msg["role"] == "system"]
    
    # 提取对话消息（user 和 assistant）
    dialog_messages = [msg for msg in history if msg["role"] != "system"]
    
    # 只保留最近 max_turns 轮对话（每轮包含 user + assistant）
    # 每轮 = 2 条消息，所以保留 max_turns * 2 条
    recent_messages = dialog_messages[-(max_turns * 2):]
    
    # 重新组合：system + 最近的对话
    return system_messages + recent_messages

# 示例：模拟一个很长的对话历史
long_history = [
    {"role": "system", "content": "你是 AI 助手"},
    {"role": "user", "content": "第1轮用户消息"},
    {"role": "assistant", "content": "第1轮AI回复"},
    {"role": "user", "content": "第2轮用户消息"},
    {"role": "assistant", "content": "第2轮AI回复"},
    {"role": "user", "content": "第3轮用户消息"},
    {"role": "assistant", "content": "第3轮AI回复"},
    {"role": "user", "content": "第4轮用户消息"},
    {"role": "assistant", "content": "第4轮AI回复"},
    {"role": "user", "content": "第5轮用户消息"},
    {"role": "assistant", "content": "第5轮AI回复"},
]

# 只保留最近 2 轮
compressed_history = manage_conversation_history(long_history, max_turns=2)

print("原始历史长度:", len(long_history))
print("压缩后长度:", len(compressed_history))
print("\n压缩后的内容:")
for msg in compressed_history:
    print(f"  [{msg['role']}] {msg['content']}")
```

&emsp;&emsp;上面的代码实现了一个简洁的滑动窗口策略：首先将 `system` 消息与对话消息分离，然后只保留最近 `max_turns` 轮的 `user` + `assistant` 消息对，最后将 `system` 消息重新拼接到前面。从输出可以看到，原始 11 条消息被压缩为 5 条（1 条 system + 2 轮 × 2 条），第 1~3 轮的历史被直接丢弃。

&emsp;&emsp;滑动窗口的优点是<font color=red>实现简单、效果可预测、不消耗额外 Token</font>。但它有一个明显的缺陷：**早期对话中的关键信息会被永久丢失**。比如用户在第 1 轮说了"我叫张三，是一名后端工程师"，到第 10 轮时如果窗口只保留最近 3 轮，AI 就完全不知道用户是谁了。这在客服、咨询等需要长期记忆的场景中是不可接受的。

&emsp;&emsp;那有没有一种方法，既能控制 Token 消耗，又能保留早期对话的核心信息？这就是我们接下来要讲的第二种策略——摘要压缩。

**策略二：摘要压缩（Summary Compression）**

&emsp;&emsp;摘要压缩的核心思路是：<font color=red>不是简单地丢弃早期对话，而是用大模型把早期对话"浓缩"成一段摘要</font>，然后用这段摘要替代原始的冗长历史。这样既控制了 Token 数量，又保留了关键信息（如用户身份、讨论过的核心结论、达成的共识等）。

&emsp;&emsp;具体流程分为三步：第一步，当对话历史超过设定的阈值时，触发压缩；第二步，将需要压缩的早期对话发送给大模型，让它生成一段精炼的摘要；第三步，用这段摘要替换掉原始的早期对话，与最近几轮的完整对话拼接在一起，作为新的上下文继续对话。

&emsp;&emsp;下面我们来实现这个策略：

```python
from openai import OpenAI
import os

# 创建客户端（复用前面的 DeepSeek 配置）
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def summarize_history(client, messages_to_summarize, model="deepseek-chat"):
    """
    调用大模型，将一段对话历史压缩为一段摘要
    
    Args:
        client: OpenAI 客户端
        messages_to_summarize: 需要压缩的对话消息列表
        model: 用于生成摘要的模型
    
    Returns:
        摘要文本字符串
    """
    # 将对话历史格式化为可读文本
    conversation_text = ""
    for msg in messages_to_summarize:
        role_label = {"user": "用户", "assistant": "AI助手"}.get(msg["role"], msg["role"])
        conversation_text += f"{role_label}: {msg['content']}\n"
    
    # 构造摘要请求
    summary_response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个对话摘要助手。请将以下对话历史压缩为一段简洁的摘要，"
                           "必须保留：1）用户的身份信息 2）讨论过的核心话题和结论 "
                           "3）用户明确表达的偏好或需求。摘要应使用第三人称描述。"
            },
            {
                "role": "user",
                "content": f"请将以下对话压缩为摘要：\n\n{conversation_text}"
            }
        ],
        temperature=0.3  # 低温度，确保摘要准确稳定
    )
    
    return summary_response.choices[0].message.content


def manage_history_with_summary(client, history, max_turns=3, model="deepseek-chat"):
    """
    使用摘要压缩管理对话历史
    
    Args:
        client: OpenAI 客户端
        history: 完整对话历史列表
        max_turns: 保留最近几轮完整对话（不压缩的部分）
        model: 用于生成摘要的模型
    
    Returns:
        压缩后的对话历史
    """
    # 分离 system 消息和对话消息
    system_messages = [msg for msg in history if msg["role"] == "system"]
    dialog_messages = [msg for msg in history if msg["role"] != "system"]
    
    # 如果对话轮数不超过阈值，无需压缩
    total_turns = len(dialog_messages) // 2
    if total_turns <= max_turns:
        print(f"当前 {total_turns} 轮对话，未超过阈值 {max_turns} 轮，无需压缩")
        return history
    
    # 计算需要压缩的部分和保留的部分
    keep_count = max_turns * 2  # 保留最近 max_turns 轮（每轮 2 条）
    messages_to_summarize = dialog_messages[:-keep_count]  # 早期对话 → 压缩
    messages_to_keep = dialog_messages[-keep_count:]        # 最近对话 → 保留
    
    print(f"总对话轮数: {total_turns}")
    print(f"压缩前 {len(messages_to_summarize)} 条早期消息，保留最近 {len(messages_to_keep)} 条")
    
    # 调用大模型生成摘要
    summary = summarize_history(client, messages_to_summarize, model)
    print(f"\n生成的摘要:\n{summary}\n")
    
    # 将摘要作为 system 消息的补充，拼接新的对话历史
    # 原始 system prompt + 摘要 + 最近的完整对话
    summary_message = {
        "role": "system",
        "content": f"{system_messages[0]['content']}\n\n"
                   f"【以下是之前对话的摘要，请基于这些信息继续对话】\n{summary}"
    }
    
    compressed_history = [summary_message] + messages_to_keep
    print(f"压缩后历史长度: {len(compressed_history)} 条（1条含摘要的system + {len(messages_to_keep)}条最近对话）")
    
    return compressed_history


# ========== 测试摘要压缩 ==========

# 模拟一段包含关键信息的长对话
long_history = [
    {"role": "system", "content": "你是一位友好的 AI 助手，擅长回答各种问题。"},
    # 第 1 轮：用户自我介绍（关键信息！）
    {"role": "user", "content": "你好，我叫张三，是一名 Python 后端工程师，在北京工作。"},
    {"role": "assistant", "content": "你好张三！很高兴认识你。作为 Python 后端工程师，你平时主要用什么框架呢？"},
    # 第 2 轮：技术偏好（关键信息！）
    {"role": "user", "content": "我主要用 FastAPI 和 Django，最近在学习大模型相关的开发。"},
    {"role": "assistant", "content": "FastAPI 和 Django 都是很好的选择！大模型开发现在确实很火，你对哪个方向比较感兴趣？"},
    # 第 3 轮：学习目标（关键信息！）
    {"role": "user", "content": "我想学习 RAG 技术，把大模型集成到我们公司的知识库系统中。"},
    {"role": "assistant", "content": "RAG 是非常实用的方向！结合你的 FastAPI 经验，可以很快搭建一个 RAG 服务。"},
    # 第 4 轮：闲聊
    {"role": "user", "content": "对了，今天北京天气怎么样？"},
    {"role": "assistant", "content": "抱歉，我无法获取实时天气信息。建议你查看天气预报应用。"},
    # 第 5 轮：继续技术讨论
    {"role": "user", "content": "好的，那我们继续聊 RAG 吧，向量数据库你推荐哪个？"},
    {"role": "assistant", "content": "对于入门，我推荐 FAISS 或 Chroma。如果是生产环境，可以考虑 Milvus 或 Qdrant。"},
]

print("=" * 60)
print("摘要压缩演示")
print("=" * 60)

# 只保留最近 2 轮完整对话，其余压缩为摘要
compressed = manage_history_with_summary(client, long_history, max_turns=2)
```

&emsp;&emsp;我们来拆解这段代码的核心逻辑。整个摘要压缩分为两个函数协作完成：

&emsp;&emsp;`summarize_history` 负责"浓缩"工作——它将早期对话格式化为可读文本，然后通过一个专门的 `system prompt` 指导大模型生成摘要。这里有两个关键设计：一是摘要提示词明确要求保留用户身份、核心话题和偏好需求，避免模型只提取表面信息；二是 `temperature=0.3`，用低温度确保摘要的准确性和稳定性，而不是追求创意表达。

&emsp;&emsp;`manage_history_with_summary` 负责"调度"工作——它先判断当前对话轮数是否超过阈值，如果超过，就把对话历史切成两部分：早期部分送去压缩，最近 `max_turns` 轮保持原样。最终，<font color=red>压缩后的摘要被注入到 `system` 消息中</font>，与原始的系统提示词合并。这样 AI 在后续对话中既能看到"之前聊过什么"的概要，又能看到最近几轮的完整细节。

&emsp;&emsp;从测试结果可以看到，原本 5 轮共 10 条对话消息，经过压缩后变成了 1 条含摘要的 `system` 消息 + 4 条最近对话（第 4、5 轮），总共 5 条。而关键信息——张三的身份、技术栈偏好、RAG 学习目标——都被保留在了摘要中，不会因为窗口滑动而丢失。

&emsp;&emsp;光看摘要生成还不够，我们需要验证一个关键问题：<font color=red>经过摘要压缩后，AI 还能"记住"早期对话中的关键信息吗？</font>下面我们用压缩后的历史继续对话，故意问一些只有早期对话才提到过的信息：

```python
# 用压缩后的历史继续对话，验证摘要是否保留了关键信息
test_question = "你还记得我叫什么名字吗？我是做什么工作的？"

# 将测试问题加入压缩后的历史
compressed.append({"role": "user", "content": test_question})

# 调用 API
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=compressed
)

answer = response.choices[0].message.content
print(f"用户: {test_question}")
print(f"AI: {answer}")
print(f"\n--- 验证结果 ---")
print(f"压缩后的上下文仅 {len(compressed)} 条消息，但 AI 仍能回忆早期信息")
print(f"这就是摘要压缩相比滑动窗口的核心优势：关键信息不会丢失")
```

&emsp;&emsp;从验证结果可以看到，尽管用户的自我介绍发生在第 1 轮（已经被压缩为摘要），AI 依然能够准确回答用户的名字和职业。这证明摘要压缩确实保留了早期对话中的关键信息。如果换成滑动窗口（只保留最近 2 轮），AI 对这个问题将完全无法回答。

&emsp;&emsp;当然，摘要压缩也不是没有代价。<font color=red>每次触发压缩都需要额外调用一次 API 来生成摘要，这意味着额外的延迟和 Token 消耗</font>。此外，摘要本身是模型生成的，存在信息遗漏或理解偏差的风险——虽然概率不高，但在对精确性要求极高的场景（如法律咨询、医疗问诊）中需要格外注意。

&emsp;&emsp;那么在实际项目中，应该选择滑动窗口还是摘要压缩？我们用一张表来对比：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>滑动窗口 vs 摘要压缩：两种上下文管理策略对比</font></p>
<div class="center">

| 对比维度        | 滑动窗口                   | 摘要压缩                       |
| --------------- | -------------------------- | ------------------------------ |
| 实现复杂度      | 低，纯本地截断             | 中，需额外调用 API             |
| 额外 Token 消耗 | 无                         | 每次压缩消耗约 200~500 tokens  |
| 早期信息保留    | ❌ 完全丢失                 | ✅ 关键信息保留在摘要中         |
| 延迟影响        | 无额外延迟                 | 压缩时增加一次 API 调用延迟    |
| 信息准确性      | 保留部分 100% 准确         | 摘要可能存在轻微偏差           |
| 适用场景        | 闲聊、短对话、对历史不敏感 | 客服、咨询、需要长期记忆的场景 |
| 推荐使用        | 对话轮数少、成本敏感       | 对话轮数多、信息连续性要求高   |

</div>

> &emsp;**实战建议**：在实际项目中，这两种策略并不互斥。一种常见的做法是<font color=red>组合使用</font>：先用摘要压缩处理早期历史，再对摘要后的结果应用滑动窗口作为兜底保护，确保 Token 总量始终在可控范围内。

#### Function Calling

---

&emsp;&emsp;大模型虽然强大，但本质上只能生成文本，<font color=red>无法直接查询实时数据、执行计算、调用外部 API</font>。例如，如果你问"北京现在的天气"，模型只能根据训练数据猜测，无法获取真实的天气信息。

&emsp;&emsp;**Function Calling**（函数调用）功能解决了这个问题。它让 AI 能够：

- 识别用户意图需要调用哪个工具

- 从用户输入中提取参数

- 返回一个"调用请求"（而不是直接调用）

- 由你的代码执行实际的函数调用

- 将结果返回给 AI，让它生成最终回复

&emsp;&emsp;这个过程是<font color=red>人机协作</font>：AI 负责理解意图和提取参数，你的代码负责执行实际操作。通过这种方式，AI 可以查天气、搜索资料、操作数据库、调用任意 API。

**Function Calling 的核心流程**

&emsp;&emsp;Function Calling 的完整流程包括以下步骤：

1. **定义工具（tools）**：告诉 AI 你有哪些函数可以调用，每个函数的参数是什么

2. **第一次调用 API**：AI 分析用户输入，决定是否需要调用函数

3. **检查响应**：如果 AI 返回了 `tool_calls`，说明它想调用函数

4. **执行函数**：根据 AI 的请求，执行实际的函数调用

5. **第二次调用 API**：将函数执行结果返回给 AI

6. **AI 生成最终回复**：结合函数结果，生成用户可读的回答

&emsp;&emsp;让我们通过一个完整的天气查询示例来理解这个流程。

**完整示例：天气查询工具**

&emsp;&emsp;首先，我们定义一个获取天气的函数（这里用 Mock 数据模拟真实 API）：

```python
import json

def get_weather(city: str, unit: str = "celsius") -> str:
    """
    获取指定城市的天气信息（Mock 函数，实际应调用天气 API）
    
    Args:
        city: 城市名称
        unit: 温度单位（celsius 或 fahrenheit）
    
    Returns:
        天气信息的 JSON 字符串
    """
    # 模拟天气数据
    weather_data = {
        "北京": {"temperature": 15, "condition": "晴天", "humidity": 45},
        "上海": {"temperature": 20, "condition": "多云", "humidity": 60},
        "深圳": {"temperature": 28, "condition": "小雨", "humidity": 75},
    }
    
    # 检查城市是否存在于模拟数据中
    if city in weather_data:
        data = weather_data[city]
        # 如果单位为华氏度，则进行温度单位转换
        if unit == "fahrenheit":
            data["temperature"] = int(data["temperature"] * 9/5 + 32)
        
        # 返回包含详细天气信息的 JSON 字符串
        return json.dumps({
            "city": city,
            "temperature": data["temperature"],
            "unit": unit,
            "condition": data["condition"],
            "humidity": data["humidity"]
        }, ensure_ascii=False)
    else:
        # 若城市未在数据中定义，返回错误信息
        return json.dumps({"error": f"未找到 {city} 的天气数据"}, ensure_ascii=False)

# 测试函数
print("测试天气查询函数：")
print(get_weather("北京"))
print(get_weather("上海", "fahrenheit"))
```

&emsp;&emsp;接下来，我们需要定义工具的 schema（描述），告诉 AI 这个函数的作用、参数类型等信息：

```python
# 定义工具 schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的实时天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、深圳"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，celsius（摄氏度）或 fahrenheit（华氏度）"
                    }
                },
                "required": ["city"]  # city 是必填参数，unit 是可选参数
            }
        }
    }
]

print("✅ 工具 schema 已定义")
```

&emsp;&emsp;这个 schema 使用 JSON Schema 格式，包含：

- **name**：函数名称（必须与实际函数名一致）

- **description**：函数的作用描述（AI 根据这个描述判断是否调用）

- **parameters**：参数定义（类型、描述、是否必填）

&emsp;&emsp;现在，让我们完整实现 Function Calling 流程：

```python
# 创建客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 用户提问
user_query = "北京现在的天气怎么样？"

# 初始化消息
messages = [
    {"role": "system", "content": "你是一个友好的天气助手，可以查询天气信息。"},
    {"role": "user", "content": user_query}
]

print(f"用户: {user_query}\n")

# 第一次调用：让 AI 决定是否需要调用工具
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,  # 传递工具定义
    tool_choice="auto"  # auto: AI 自动决定是否调用；也可以设为 "none" 或强制调用某个工具
)

# 检查 AI 是否想调用函数
if response.choices[0].message.tool_calls:
    print("AI 决定调用工具：")
    
    # 提取工具调用信息
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    print(f"  函数名: {function_name}")
    print(f"  参数: {function_args}\n")
    
    # 执行实际的函数调用
    if function_name == "get_weather":
        function_result = get_weather(**function_args)
        print(f"函数执行结果: {function_result}\n")
        
        # 将函数结果添加到消息历史
        messages.append(response.choices[0].message)  # AI 的工具调用请求
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": function_result
        })
        
        # 第二次调用：让 AI 根据函数结果生成最终回复
        final_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        
        final_answer = final_response.choices[0].message.content
        print(f"AI 最终回复: {final_answer}")
    
else:
    # AI 认为不需要调用工具，直接回复
    print(f"AI 直接回复: {response.choices[0].message.content}")
```

&emsp;&emsp;这段代码展示了完整的 Function Calling 流程：

1. **第一次 API 调用**：传递 `tools` 参数，AI 分析用户意图

2. **检查 `tool_calls`**：如果存在，说明 AI 想调用函数

3. **提取参数**：从 `tool_call.function.arguments` 中提取 JSON 格式的参数

4. **执行函数**：调用实际的 Python 函数

5. **第二次 API 调用**：将函数结果以 `role="tool"` 的消息返回给 AI

6. **AI 生成回复**：结合天气数据，生成自然语言回答

&emsp;&emsp;运行后，AI 会回复类似"北京现在的天气是晴天，温度 15℃，湿度 45%"这样的完整回答。

**Function Calling 的实际应用**

&emsp;&emsp;Function Calling 的应用场景非常广泛：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Function Calling 典型应用场景</font></p>
<div class="center">

| 应用场景     | 工具函数示例                            | 用途                     |
| ------------ | --------------------------------------- | ------------------------ |
| **信息查询** | get_weather、search_web、query_database | 查询实时数据、搜索资料   |
| **计算任务** | calculate、solve_equation、convert_unit | 精确计算、单位转换       |
| **数据操作** | create_record、update_user、delete_item | 操作数据库、CRUD 操作    |
| **外部集成** | send_email、create_ticket、post_message | 调用第三方 API、发送通知 |
| **文件操作** | read_file、write_file、list_files       | 读写文件、文件管理       |

</div>

&emsp;&emsp;通过 Function Calling，你可以让 AI 从"只会聊天"变成"能做事"的智能助手。例如：

- **客服机器人**：查询订单状态、修改地址、申请退款

- **数据分析助手**：查询数据库、生成报表、发送邮件

- **开发助手**：搜索文档、执行代码、部署应用

> &emsp;**注意**：**并非所有模型都支持 Function Calling**。虽然目前为止大部分的大模型都支持 Function Calling，但使用前还是需要查阅平台文档确认支持情况。

#### 多模态输入

---

&emsp;&emsp;到目前为止，我们一直在使用纯文本与 AI 交互。但在实际应用中，<font color=red>用户往往需要让 AI 理解图片、音频、视频等多模态内容</font>。例如，上传一张产品图片让 AI 写商品描述，或者拍摄一道菜的照片让 AI 识别菜名。

&emsp;&emsp;**多模态模型**（Multimodal Model）可以同时处理文本和图像输入。目前支持视觉理解的主流模型包括：

- **gpt-5 / GPT-5 nano**：OpenAI 的多模态模型，图像理解能力强

- **Claude 4.5 Sonnet/Opus**：Anthropic 的多模态模型，代码图像分析出色

- **Gemini 3.0 Pro**：Google 的多模态模型，支持超长上下文

- **Qwen-VL-Plus**：阿里通义千问视觉版，国内可直接使用

&emsp;&emsp;这一节我们会演示如何通过 OpenRouter 调用 gpt-5，让 AI 分析图片内容。

**图片传递方式一：URL链接**

&emsp;&emsp;最简单的方式是通过 URL 传递图片。只要图片在公网可访问，就可以直接将 URL 传给 API：

模型地址：https://openrouter.ai/openai/gpt-5-nano

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20260123112311636.png" width=80%></div>

```python
# 使用 OpenRouter 调用 gpt-5（支持视觉理解）
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# 一张公开的图片 URL（示例）
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

# 构造包含图片的消息
response = client.chat.completions.create(
    model="openai/gpt-4o",  # 使用支持视觉的模型
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片里有什么？请详细描述。"},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }
    ],
    max_tokens=500
)

print("AI 对图片的描述：")
print(response.choices[0].message.content)
```

&emsp;&emsp;关键点：

1. **content 变成列表**：不再是单纯的字符串，而是包含多个元素的列表

2. **text 元素**：`{"type": "text", "text": "..."}`，表示文本输入

3. **image_url 元素**：`{"type": "image_url", "image_url": {"url": "..."}}`，表示图片 URL

&emsp;&emsp;AI 会分析图片内容，然后用自然语言描述它看到的内容。这种方式适合图片已经托管在云存储、CDN 或公开网站上的场景。

**图片传递方式二：Base64编码**

&emsp;&emsp;如果图片在本地，或者不方便通过 URL 访问，可以将图片编码为 Base64 字符串后传递：

```python
!pip install Pillow
```

```python
# 方法2：使用base64编码本地图片
print("=" * 60)
print("方法2：通过base64编码传递本地图片")
print("=" * 60)

from PIL import Image
import io
import base64

def compress_image(image_path, max_size=(800, 800)):
    """压缩图片到合适大小"""
    with Image.open(image_path) as img:
        # 保持宽高比缩放
        img.thumbnail(max_size)
        
        # 保存为JPEG并压缩
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        
        # 编码为base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

# 使用压缩后的图片
b64_image = compress_image("/Users/mac/大模型资料/大模型基础入门/images/zhipu_model_plaza.png")
print(f"压缩后大小: {len(b64_image)/1024:.2f} KB")  # 确保 <500KB

# ✅ 这样更有可能成功
messages=[{
    "role": "user",
    "content": [
        {"type": "text", "text": "描述图片"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
    ]
}]

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=messages,
    max_tokens=100
)

print(f"AI回复：{response.choices[0].message.content}")
```



```python
from IPython.display import Image, display

# 展示图片内容
display(Image(url="/Users/mac/大模型资料/大模型基础入门/images/zhipu_model_plaza.png"))
```

&emsp;&emsp;Base64 编码的要点：

1. **格式**：必须以 `data:image/jpeg;base64,` 开头，然后跟 Base64 字符串

2. **压缩**：大图片会导致 Token 消耗激增，建议压缩到 1024x1024 以内

3. **适用场景**：本地图片、用户上传的图片、临时图片

> &emsp;**成本提示**：图片输入会消耗大量 Token。以 gpt-5.2 为例，一张 1024x1024 的图片约消耗 765 tokens。因此，使用多模态功能时要特别注意成本控制。

**多模态图片生成**

&emsp;&emsp;接下来我们体验 `Google` 最新的 `Gemini 3` 多模态模型在 `OpenRouter` 上的使用。`Gemini 3 Pro` 是 `Google` 的旗舰级模型，具备强大的文本处理和多模态（包含图像、视频、音频）理解能力。据 `OpenRouter` 提供的信息，其中代号为 `Nano Banana Pro` 的 `Gemini 3` 图像模型，可以根据文字生成高质量图像，并支持复杂的多元素组合。下面我们以调用这个图像模型为例，请它生成一张图像。

&emsp;&emsp;模型地址：https://openrouter.ai/google/gemini-3-pro-image-preview

<div align=center><img src="https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202512301203446.png" width=80%></div>

```python
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"), # 这里替换为你的 OpenRouter API Key
)

# 用 Gemini 3 图像生成模型（Nano Banana Pro）
response = client.chat.completions.create(
  model="google/gemini-3-pro-image-preview",
  messages=[
          {
            "role": "user",
            "content": "请生成一张夕阳下群山的风景图片。"
          }
        ],
  extra_body={"modalities": ["image", "text"]}
)

# 提取返回的图像数据（Base64 编码）
response = response.choices[0].message
if response.images:
  for image in response.images:
    image_url = image['image_url']['url'] 
    print(f"Generated image: {image_url[:50]}...")
```



```python
from IPython.display import Image, display

display(Image(url=image_url))
```

&emsp;&emsp;我们将 `model` 参数设为了 `google/gemini-3-pro-image-preview`，也就是 `Google Gemini 3 Pro` 的图像模型。
在 `messages` 中，我们给模型一个用户指令，描述希望生成的图像场景。由于图像模型的回复是图片数据，所以 `response.choices[0].message.content` 将包含图像的编码数据（通常为 `Base64` 字符串）。我们将其提取到 `image_base64` 变量中。

&emsp;&emsp;如何使用返回的图片？ 我们可以将得到的 `Base64` 字符串转换为图片文件保存下来，或在前端页面将其显示为图片。具体而言，在`Python`中可以用 `base64` 库解码字符串并保存为 `.png` 文件。在网页端则可直接将 `Base64` 数据前缀为 `data:image/png;base64`, 后用于展示。通过 `OpenRouter` 这个统一接口，我们成功地让 `Google` 的 `Gemini` 模型根据中文描述生成了图像。这对于需要多模态内容生成的应用来说非常方便强大！

&emsp;&emsp;国内在多模态领域（Multimodal）已经形成了“视觉理解（让 AI 看懂）”与“视觉生成（让 AI 绘画）”两大核心流派。比如目前Qwen-VL (阿里通义)的多模态模型、GLM-4V & CogView (智谱 AI)的模型、以及我们今天介绍的 Gemini 3 Pro等模型，都是属于“视觉生成”这一流派。

**多模态应用场景**

&emsp;&emsp;多模态能力开辟了许多新的应用场景：

- **电商**：上传商品图片，AI 自动生成商品描述、提取卖点

- **教育**：拍摄数学题照片，AI 解题并给出步骤

- **医疗**：分析医学影像，辅助诊断（需专业模型）

- **内容审核**：检测图片中的违规内容

- **辅助工具**：帮助视障人士"看"图片，描述场景

- **代码理解**：分析 UI 截图，生成对应的 HTML/CSS 代码

&emsp;&emsp;掌握多模态输入后，你的 AI 应用将从"只能聊天"进化到"能看会说"，大大拓展了应用边界。

#### 提示词工程

---

同样的问题，不同的提示词（Prompt）会得到截然不同的回答质量。<font color=red>提示词工程（Prompt Engineering）是一门让 AI 更准确理解你意图的艺术</font>。这里分享四个实用技巧。

&emsp;&emsp;**技巧1：明确角色与行为规范**&emsp;&emsp;

System Prompt（系统提示词）中的"角色与行为规范"是提升大模型输出质量的核心技巧之一。它的核心逻辑是：通过明确告诉模型"你是谁"以及"你应该怎么做"，来约束和引导模型的行为。

&emsp;&emsp;具体来说，我们可以在 System Prompt 中定义模型的身份（比如"你是一位资深的 Python 技术导师"）、输出风格（比如"解释简洁易懂，避免术语堆砌"）、以及具体的行为规范（比如"必须提供可运行的代码示例"）。这些规则会在整个对话过程中持续生效，成为模型回答的"行为准则"。

&emsp;&emsp;为什么这个技巧有效？因为大模型本质上是一个"角色扮演者"，它会根据你赋予的角色来调整语气、专业度和回答深度。如果你不定义角色，模型就会用默认的通用风格回答，可能过于笼统或不符合预期。而一旦你明确了角色，模型就会"入戏"，输出更加专业、风格一致的内容。

好的角色定义通常包含三个要素：身份定位、专业领域、以及输出约束。这三者缺一不可，共同构成了一个清晰的"人设"。

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ❌ 糟糕的提示词
bad_prompt = {"role": "user", "content": "解释一下装饰器"}

# ✅ 优秀的提示词（明确角色）
good_system = """你是一个专业的Python技术导师。
特点：
- 解释简洁易懂，避免术语堆砌
- 提供可运行的代码示例
- 指出常见错误和注意事项
- 语气友好，鼓励学习"""

good_prompt = {"role": "user", "content": "请解释Python装饰器的原理"}

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": good_system},
        good_prompt
    ]
)

print(response.choices[0].message.content)
```

&emsp;&emsp;**技巧2：要求格式化输出**

&emsp;&emsp;格式化输出是让大模型返回结构化数据的核心技巧。它的核心逻辑是：通过在 System Prompt 中明确指定输出格式（如 JSON、Markdown 表格等），让模型的回答变得可预测、可解析。

&emsp;&emsp;为什么需要格式化输出？因为大模型默认会生成自然语言文本，虽然读起来流畅，但很难被程序自动处理。想象一下，如果你让模型"分析这段代码的问题"，它可能会返回一大段散文式的描述。但如果你要求它返回 JSON 格式，包含 error_type、location、suggestion 等字段，你的程序就能直接解析并执行后续操作。

&emsp;&emsp;实现格式化输出的关键在于两点：第一是提供清晰的格式模板，让模型知道期望的结构；第二是给出一个具体的输出示例，这比纯文字描述更能让模型"理解"你的意图。

&emsp;&emsp;常见的格式包括 JSON（最适合程序解析）、Markdown（适合文档生成）、以及自定义分隔符格式（适合简单场景）。选择哪种格式取决于你的下游需求：如果要接入自动化流程，优先选 JSON；如果是给人看的报告，Markdown 更合适。

```python
# 要求JSON格式输出
system_prompt = """请以JSON格式返回结果，严格遵循以下格式：
{
    "summary": "核心要点（一句话）",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "code_example": "代码示例",
    "common_mistakes": ["常见错误1", "常见错误2"]
}"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "如何使用Python读取CSV文件？"}
    ],
    temperature=0  # 确定性输出
)

print(response.choices[0].message.content)
```

&emsp;&emsp;**技巧3：少样本学习（Few-Shot Learning）**

&emsp;&emsp;Few-Shot Learning（少样本学习）是一种通过在提示中嵌入少量示例，让大模型"临时学会"特定任务的技术。它的核心逻辑可以用"先示范、再提问"来概括。

&emsp;&emsp;具体来说，我们不是直接把问题抛给模型，而是先在对话历史中构造几组"用户提问 → 助手回答"的示例对话。这些示例就像是给模型看的"参考答案"，模型会从中推断出输入和输出之间的映射规则——比如输入是一段文本，输出应该是"正面"或"负面"这样的固定格式。

&emsp;&emsp;当模型看到最后一个真正需要回答的新问题时，它会模仿前面示例的模式来生成答案。这就是"少样本"的精髓：我们不需要对模型进行任何微调或额外训练，只需要在提示词中提供几个高质量的示例，就能让模型按照期望的格式和风格输出。

&emsp;&emsp;示例的数量通常在 2-5 个之间，太少可能让模型"学不会"，太多则会消耗过多 Token 并增加成本。选择具有代表性、边界清晰的示例，是 Few-Shot 成功的关键。

* Few-Shot 的核心逻辑

| 角色                                | 作用                                                         |
| :---------------------------------- | :----------------------------------------------------------- |
| `system`                            | 定义任务，告诉模型"你要做什么"                               |
| `user` + `assistant` 对（重复多次） | **这就是 few-shot 的关键**——通过示例让模型"学习"输入输出的映射关系 |
| 最后一个 `user`                     | 真正需要模型回答的新问题                                     |

```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============ Few-Shot Learning 示例 ============
# 任务：情感分类（正面/负面/中性）

messages = [
    # 系统角色定义任务
    {"role": "system", "content": "你是一个情感分析助手。请根据用户输入的文本，判断情感倾向，只输出：正面、负面 或 中性。"},
    
    # ========== Few-Shot 示例开始 ==========
    # 示例 1：正面
    {"role": "user", "content": "这家餐厅的服务太棒了，菜品也很美味！"},
    {"role": "assistant", "content": "正面"},
    
    # 示例 2：负面
    {"role": "user", "content": "等了一个小时外卖还没到，客服态度也很差。"},
    {"role": "assistant", "content": "负面"},
    
    # 示例 3：中性
    {"role": "user", "content": "今天天气一般，不冷也不热。"},
    {"role": "assistant", "content": "中性"},
    # ========== Few-Shot 示例结束 ==========
    
    # 真正需要模型处理的新问题
    {"role": "user", "content": "这个产品质量不错，但是价格有点贵。"}
]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0  # 降低随机性，让分类更稳定
)

print("情感分析结果：", response.choices[0].message.content)
```

&emsp;&emsp;**技巧4：链式思考（Chain of Thought）**

&emsp;&emsp;链式思考（Chain of Thought，简称 CoT）是一种让大模型"逐步推理"的提示技术。它的核心逻辑是：通过要求模型先展示思考过程，再给出最终答案，从而提升复杂问题的回答准确率。

&emsp;&emsp;为什么需要链式思考？因为大模型在处理复杂问题时，如果直接跳跃到答案，容易出错。比如一道数学应用题，模型可能会"想当然"地给出一个错误结果。但如果你要求它"一步一步分析"，它就会被迫展开中间推理过程，每一步都基于前一步的结论，最终答案的准确性会大幅提升。

&emsp;&emsp;实现链式思考有两种方式：第一种是在提示词中直接加上"请一步一步思考"或"Let's think step by step"这样的指令；第二种是通过 Few-Shot 示例，给模型展示几个带有详细推理过程的样例，让它学会这种输出风格。

&emsp;&emsp;链式思考特别适合解决需要多步推理的问题，比如数学计算、逻辑推断、代码调试等。但对于简单问答类任务，使用 CoT 可能会增加不必要的 Token 消耗，因此需要根据具体场景权衡使用。

```python
# 让AI展示推理过程
prompt = """请一步步分析以下问题：
问题：一个班级有30名学生，其中60%是女生。如果再加入5名男生，女生占比是多少？

请按以下格式作答：
1. 理解题意：...
2. 计算原始数据：...
3. 计算新数据：...
4. 得出结论：...
"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)

print(response.choices[0].message.content)
```

* **最佳实践总结**：

    * system 消息定义角色和行为规范

    * 明确要求输出格式（JSON/Markdown/表格）

    * 使用 Few-Shot 示例帮助 AI 理解模式
    
    * 对于复杂任务，要求展示推理过程
    
    
    
    
    
    &emsp;&emsp;**链式思考特别适合以下场景：**
    
    <style>
    .center {
    width: auto;
    display: table;
    margin-left: auto;
    margin-right: auto;
    }
    </style>
    <p align="center"><font face="黑体" size=4>链式思考适用场景</font></p>
    <div class="center">
    
    | 任务类型     | 示例               | CoT 提示词                     |
    | ------------ | ------------------ | ------------------------------ |
    | **数学推理** | 应用题、代数题     | "请列出每一步计算过程"         |
    | **逻辑推理** | 脑筋急转弯、侦探题 | "请逐步分析每个线索"           |
    | **代码调试** | 找出 bug 原因      | "请逐行分析代码逻辑"           |
    | **决策分析** | 多方案对比         | "请列出各方案的优缺点"         |
    | **文本分析** | 长文摘要、观点提取 | "请先总结段落大意，再提炼观点" |
    
    > &emsp;**进阶技巧**：可以在 Few-Shot 示例中同时展示"问题 + 逐步推理 + 答案"的完整流程，让 AI 学会这种思维模式。

#### 异步批处理

---

如果需要同时处理多个问题（如批量翻译、批量摘要），同步逐个调用会非常慢。<font color=red>使用 AsyncOpenAI 客户端配合 asyncio，可以并发执行多个请求</font>，大幅提升吞吐量。

```python
import os
import time
import asyncio
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# 同步客户端
sync_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 异步客户端
async_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 测试问题列表
questions = [
    "什么是Python？",
    "什么是JavaScript？",
    "什么是Go语言？",
    "什么是Rust？",
    "什么是TypeScript？"
]

# 方法1：同步调用（逐个执行）
def sync_batch():
    print("=" * 60)
    print("同步调用（逐个执行）")
    print("=" * 60)
    
    start_time = time.time()
    results = []
    
    for question in questions:
        response = sync_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": question}],
            max_tokens=50
        )
        results.append(response.choices[0].message.content)
    
    elapsed = time.time() - start_time
    print(f"完成 {len(questions)} 个请求")
    print(f"耗时：{elapsed:.2f} 秒\n")
    
    return results, elapsed

# 方法2：异步并发调用
async def ask_question_async(question):
    """异步调用单个问题"""
    response = await async_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}],
        max_tokens=50
    )
    return response.choices[0].message.content

async def async_batch():
    print("=" * 60)
    print("异步并发调用")
    print("=" * 60)
    
    start_time = time.time()
    
    # 使用 asyncio.gather 并发执行所有请求
    results = await asyncio.gather(*[ask_question_async(q) for q in questions])
    
    elapsed = time.time() - start_time
    print(f"完成 {len(questions)} 个请求")
    print(f"耗时：{elapsed:.2f} 秒\n")
    
    return results, elapsed

# 性能对比
print("开始性能测试...\n")

# 同步测试
sync_results, sync_time = sync_batch()

# 异步测试,Jupyter 专用
async_results, async_time = await async_batch()

# 普通python环境使用
# asyncio.run(async_batch())

# 性能提升
improvement = (sync_time - async_time) / sync_time * 100

print("=" * 60)
print("性能对比")
print("=" * 60)
print(f"同步调用耗时：{sync_time:.2f} 秒")
print(f"异步调用耗时：{async_time:.2f} 秒")
print(f"性能提升：{improvement:.1f}%")
print(f"\n异步调用使耗时减少了 {sync_time - async_time:.2f} 秒！")
```

* 在典型网络环境下，5个请求的异步调用可以比同步快 **60-80%**。这是因为：

    *  同步调用：请求1 → 等待 → 请求2 → 等待 → ...（串行）

    * 异步调用：请求1、2、3、4、5 同时发出 → 等待所有响应（并行）

**适用场景**：
* 批量翻译、批量摘要、批量分类

    * 多文档并发处理

    * Web应用中的高并发请求

* **注意事项**：

    * 仍需遵守速率限制（Rate Limit），不要无限并发
    
    * 建议配合信号量（`asyncio.Semaphore`）控制并发数

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>同步 vs 异步性能对比</font></p>
<div class="center">

| 对比维度       | 同步执行           | 异步执行                 |
| -------------- | ------------------ | ------------------------ |
| **总耗时**     | N × 单次耗时       | ≈ 单次耗时               |
| **资源占用**   | 低（单线程阻塞）   | 中（事件循环）           |
| **代码复杂度** | 低（易理解）       | 中（需理解 async/await） |
| **适用场景**   | 少量任务、顺序依赖 | 大量独立任务             |
| **风险**       | 耗时长             | 可能触发速率限制         |

</div>

&emsp;&emsp;通过掌握异步批处理，你的 AI 应用将能够高效处理大规模任务，从"一个一个慢慢来"进化到"批量并发快速完成"。

&emsp;**最佳实践**：对于 100 个以上的大批量任务，建议分批执行（如每批 20 个），避免内存占用过高和网络不稳定的影响。

> &emsp;**重要提示**：虽然我们在本节演示了 Chat Completions API，但 OpenAI 在 2025年还推出了新的 Responses API，提供更多专属功能。不过<font color=red>对于跨平台开发，优先掌握通用的 Chat Completions API</font>，这样你的代码才能在所有模型间自由迁移。

###   Responses API

Responses API 是 OpenAI 2025年推出的新一代 agentic API，
* 主要差异点：

    1. 服务端状态管理 - 通过 previous_response_id 自动维护对话历史

    2. 内置工具支持 - Web搜索、文件搜索、计算机操作等

    3. 事件驱动架构 - 更可预测的流式响应

    4. 简化的 agentic 工作流 - 专为 AI Agent 设计

```python
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

# 初始化客户端
client = OpenAI()  # 确保设置了 OPENAI_API_KEY 环境变量

# ============================================================
# 示例1: Chat Completions API (传统方式)
# 需要手动维护和传递完整的对话历史
# ============================================================
print("=" * 60)
print("【Chat Completions API - 传统方式】")
print("=" * 60)

# 第一轮对话
messages = [{"role": "user", "content": "我叫小明，请记住我的名字"}]
response1 = client.chat.completions.create(
    model="gpt-5-nano",
    messages=messages
)
print(f"用户: {messages[0]['content']}")
print(f"助手: {response1.choices[0].message.content}\n")

# 第二轮对话 - 必须手动维护历史
messages.append({"role": "assistant", "content": response1.choices[0].message.content})
messages.append({"role": "user", "content": "你还记得我叫什么名字吗？"})

response2 = client.chat.completions.create(
    model="gpt-5-nano",
    messages=messages  # 必须传入完整历史
)
print(f"用户: {messages[-1]['content']}")
print(f"助手: {response2.choices[0].message.content}")
print(f"\n⚠️  需手动管理的消息数: {len(messages)}")
```



```python
# ============================================================
# 示例2: Responses API (新方式)
# 服务端自动管理对话状态，通过 previous_response_id 引用
# ============================================================
print("\n" + "=" * 60)
print("【Responses API - 新方式】")
print("=" * 60)

# 第一轮对话 - 开启服务端存储
response1 = client.responses.create(
    model="gpt-5-nano",
    input="我叫小红，请记住我的名字",
    store=True  # 🔑 关键: 启用服务端状态存储
)
print(f"用户: 我叫小红，请记住我的名字")
print(f"助手: {response1.output_text}")
print(f"📦 Response ID: {response1.id}")  # 用于后续引用

# 第二轮对话 - 使用 previous_response_id 自动关联上下文
response2 = client.responses.create(
    model="gpt-5-nano",
    input="你还记得我叫什么名字吗？",
    previous_response_id=response1.id,  # 🔑 关键: 引用之前的响应
    store=True
)
print(f"\n用户: 你还记得我叫什么名字吗？")
print(f"助手: {response2.output_text}")
print(f"\n✅ 无需手动管理消息历史，服务端自动维护!")
```



```python
# ============================================================
# 示例3: Responses API 内置工具 (Web Search)
# Chat Completions API 不支持此功能
# ============================================================
print("\n" + "=" * 60)
print("【Responses API - 内置 Web Search 工具】")
print("=" * 60)

response_search = client.responses.create(
    model="gpt-5-nano",
    input="今天的比特币价格是多少？",
    tools=[{"type": "web_search_preview"}]  # 🔑 内置工具
)
print(f"用户: 今天的比特币价格是多少？")
print(f"助手: {response_search.output_text}")
print(f"\n🔍 Chat Completions API 需要手动实现搜索功能，")
print(f"   Responses API 直接内置 web_search_preview 工具!")
```

**Responses API vs Chat Completions API 核心差异**

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>同步 vs 异步性能对比</font></p>
<div class="center">

| 特性         | Chat Completions API         | Responses API                               |
| :----------- | :--------------------------- | :------------------------------------------ |
| **状态管理** | 客户端手动维护 messages      | 服务端自动管理，使用 `previous_response_id` |
| **对话历史** | 每次请求需传完整历史         | 只需引用响应 ID                             |
| **内置工具** | ❌ 需手动实现                 | ✅ Web Search, File Search, Computer Use     |
| **请求结构** | `messages` 数组              | `input` 字符串                              |
| **响应获取** | `choices[0].message.content` | `output_text`                               |
| **适用场景** | 简单问答                     | Agentic 复杂工作流                          |

<div>

**代码中的三个关键演示：**

1. **Chat Completions** - 需手动维护 messages数组

2. **Responses API** - 使用  store=True  +  previous_response_id自动关联上下文

3. **内置工具** - 直接使用  tools=[{"type": "web_search_preview"}] 进行网络搜索

### 综合实战 

- **LLM Playground 项目展示**

&emsp;&emsp;`LLM Playground` 本质上是一个**大模型调用的可视化界面**。如果说前四章我们学习的是"用代码调用 API"，那么这一章就是"用图形界面调用 API"。它的核心功能是：<font color=red>让任何人都能通过点击和输入，而不是编写代码，来体验和测试各种大模型</font>。

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20260123140533472.png" width=85%></div>

&emsp;&emsp;你可以把它理解为大模型的"万能遥控器"。就像电视遥控器让我们无需了解电路原理就能换台、调音量一样，`LLM Playground` 让我们无需每次都写代码就能切换模型、调整参数、查看结果。在这个界面中，你可以：

- 从右边筛选框中选择 `OpenAI`、`Qwen`、`DeepSeek` 等任意厂商与对应的模型

- 通过滑块实时调整 `Temperature`、`思考等级` 等参数

- 在输入框中输入文本或上传图片，立即看到模型的响应

- 查看完整的对话历史，随时回溯之前的问答

- 对比不同模型在相同输入下的表现差异

&emsp;&emsp;这种可视化界面的价值在于<font color=red>降低了使用门槛、提升了实验效率、增强了可理解性</font>。产品经理可以用它快速验证想法、设计师可以用它测试文案生成、开发者可以用它对比模型性能——所有这些场景都不需要写一行代码。

&emsp;&emsp;在深入功能细节之前，我们先从宏观层面了解这个项目的技术架构。<font color=red>我们的 LLM Playground 采用前后端分离的架构</font>，这是目前 Web 应用的主流设计模式。

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20260123142003301.png" width=60%></div>

&emsp;&emsp;**前端部分**使用 `React` + `TypeScript` + `Shadcn UI` 技术栈。`React` 负责构建用户界面和管理交互逻辑，`TypeScript` 提供类型安全保障，`Shadcn UI` 提供美观且一致的 UI 组件。前端的职责是：渲染界面、接收用户输入、展示模型响应、管理本地状态（如对话历史、参数配置）。

&emsp;&emsp;**后端部分**使用 `FastAPI` + `OpenAI SDK`。`FastAPI` 是一个高性能的 Python Web 框架，特别擅长处理异步请求和流式响应。后端的职责是：接收前端请求、调用各平台的大模型 API、处理响应数据、返回结果给前端。关键的是，<font color=red>后端通过统一的接口封装，让前端无需关心底层是调用 OpenRouter 还是 DeepSeek，只需传入模型名称即可</font>。

&emsp;&emsp;**通信方式**使用 `RESTful API` + `SSE`（Server-Sent Events）。常规的请求-响应使用 RESTful API，而流式响应（如打字机效果）则使用 SSE 技术。这种组合既保证了接口的简洁性，又实现了实时数据推送。

&emsp;&emsp;关于技术选型，你可能会问：为什么用 `FastAPI` 而不是 `Flask`？为什么用 `React` 而不是 `Vue`？这些问题我们会在第6章的 FAQ 中详细讨论。现在只需要知道：<font color=red>这套技术栈的核心优势是开发效率高、性能好、社区活跃、易于扩展</font>。



<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>大模型 API 核心术语对照表</font></p>
<div class="center">

| 术语                                        | 中文名称         | 定义                                                         |
| ------------------------------------------- | ---------------- | ------------------------------------------------------------ |
| **API** (Application Programming Interface) | 应用程序编程接口 | 一组预定义的函数和协议，允许不同软件系统之间进行通信和数据交换。在大模型场景中，API 是我们调用模型能力的标准入口。 |
| **API Key**                                 | API 密钥         | 用于身份验证的唯一字符串，证明调用者有权限访问 API 服务。它类似于"数字钥匙"，需要妥善保管，不能泄露给他人。 |
| **Base URL**                                | 基础地址         | API 服务的根网址，所有具体的 API 请求都会在这个地址基础上构建完整路径。例如 `https://api.openai.com/v1` 就是 OpenAI 的 Base URL。 |
| **Chat Completions**                        | 对话补全         | 大模型 API 中最核心的接口类型，用于实现多轮对话功能。它接收消息列表作为输入，返回模型生成的回复内容。 |
| **Function Calling**                        | 函数调用         | 大模型的一种高级能力，允许模型在对话过程中主动调用外部工具或函数，从而实现查询数据库、调用 API 等复杂操作。 |
| **JSON** (JavaScript Object Notation)       | JSON 格式        | 一种轻量级的数据交换格式，使用键值对结构组织数据。API 请求和响应通常都采用 JSON 格式，因为它易于人类阅读，也便于程序解析。 |
| **LLM** (Large Language Model)              | 大语言模型       | 基于深度学习技术训练的大规模神经网络模型，能够理解和生成自然语言文本。代表性产品包括 GPT-5、Claude、文心一言等。 |
| **Max Tokens**                              | 最大令牌数       | 限制模型单次生成内容的最大长度。这个参数既影响响应的完整性，也直接关系到 API 调用的成本和响应时间。 |
| **Messages**                                | 消息列表         | Chat Completions API 的核心输入参数，是一个包含多条消息的数组。每条消息都有 `role`（角色）和 `content`（内容）两个字段，用于构建完整的对话上下文。 |
| **Model**                                   | 模型名称         | 指定要调用的具体模型版本，例如 `gpt-5`、`gpt-5-nano`。不同模型在能力、速度和成本上存在差异，需要根据实际场景选择。 |
| **Prompt**                                  | 提示词           | 发送给大模型的输入文本，用于引导模型生成期望的输出。高质量的 Prompt 设计是获得理想结果的关键，这也是"提示工程"的核心内容。 |
| **Rate Limit**                              | 速率限制         | API 服务商对调用频率的限制，通常以"每分钟请求数"或"每天令牌数"来衡量。超过限制会导致请求被拒绝，需要合理控制调用频率。 |
| **SDK** (Software Development Kit)          | 软件开发工具包   | 官方或第三方提供的代码库，封装了 API 调用的底层细节，提供更友好的编程接口。例如 `openai` Python 库就是 OpenAI 的官方 SDK。 |
| **Stream**                                  | 流式输出         | 一种实时返回模型生成内容的方式，不需要等待全部内容生成完毕。用户可以逐字逐句看到模型的输出过程，显著提升交互体验。 |
| **System Message**                          | 系统消息         | 消息列表中 `role` 为 `system` 的特殊消息，用于设定模型的行为规则、角色定位或回答风格。它对整个对话的走向有全局性影响。 |
| **Temperature**                             | 温度参数         | 控制模型输出随机性的参数，取值范围通常是 0 到 2。值越低输出越确定和保守，值越高输出越多样和创造性。默认值一般为 1。 |
| **Token**                                   | 令牌             | 大模型处理文本的基本单位，一个 Token 大约对应 0.75 个英文单词或 0.5 个中文字符。API 计费和长度限制都基于 Token 数量而非字符数。 |
| **Usage**                                   | 用量统计         | API 响应中返回的统计信息，包含 `prompt_tokens`（输入令牌数）、`completion_tokens`（输出令牌数）和 `total_tokens`（总令牌数），用于成本核算和性能监控。 |

</div>