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