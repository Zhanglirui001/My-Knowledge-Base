# Agent基础

----

### 大模型文件结构解析

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>模型文件夹核心文件说明</font></p>
<div class="center">

| 文件名                    | 作用            | 是否必需 | 说明                             |
| ------------------------- | --------------- | -------- | -------------------------------- |
| `config.json`             | 模型架构配置    | ✅ 必需   | 定义层数、隐藏维度、注意力头数等 |
| `tokenizer.json`          | 词表映射        | ✅ 必需   | 将文字转换为数字 ID              |
| `tokenizer_config.json`   | 分词器配置      | ✅ 必需   | 分词规则、特殊 token 定义        |
| `*.safetensors`           | 模型权重        | ✅ 必需   | 存储所有参数（体积最大）         |
| `generation_config.json`  | 生成参数        | 可选     | 默认的 temperature、top_p 等     |
| `special_tokens_map.json` | 特殊 token 映射 | 可选     | PAD、EOS、BOS 等特殊标记         |
| `README.md`               | 模型说明        | 可选     | 使用方法、性能指标等             |



`config.json` 是模型加载时的入口文件，它定义了模型的"物理规格"。当 Transformers 库执行 `from_pretrained()` 时，第一件事就是读取这个文件，根据其中的配置来构建模型骨架。

```json
{
  "architectures": ["Qwen3ForCausalLM"],
  "hidden_size": 4096,
  "num_hidden_layers": 32,
  "num_attention_heads": 32,
  "vocab_size": 151936,
  "max_position_embeddings": 32768
}
```

- **`architectures`**：指定模型类型，告诉加载库应该调用哪个 Python 类来构建模型骨架

- **`hidden_size`**：隐藏层维度，决定模型的"宽度"

- **`num_hidden_layers`**：层数，决定模型的"深度"

- **`num_attention_heads`**：注意力头数量，多头注意力机制的核心参数

- **`vocab_size`**：词表大小，决定模型能"认识"多少个不同的 token

- **`max_position_embeddings`**：最大位置编码，决定模型能处理多长的上下文

> **实战技巧**：如果你想确认下载的模型是否完整（比如层数对不对），或者想手动修改某些配置（如调整上下文窗口限制），第一件事就是查看 `config.json`。



`tokenizer.json` 和 `tokenizer_config.json` 是初学者最容易忽视，却最容易导致问题的部分。<font color=red>计算机不认识"你好"这两个汉字，它只认识数字。</font>Tokenizer（分词器）的作用就是在"人类语言"和"模型语言"之间架起桥梁。

```
用户输入："今天天气真好"
    ↓ tokenizer.encode()
Token IDs：[1234, 567, 890, 234, 567]
    ↓ 送入模型
模型输出：[2345, 678, ...]
    ↓ tokenizer.decode()
生成文本："是的，阳光明媚..."
```

- **`tokenizer.json`**：存储了数万个词汇到 ID 的映射表（Vocabulary）。Qwen3 的词表大小约为 15 万，这意味着它能"认识" 15 万种不同的 token。

- **`tokenizer_config.json`**：定义了分词的规则（如是否在句首加空格）以及特殊 Token 的配置（如 `<|end_of_text|>` 用于标记生成的结束）。

> ⚠️ **常见事故**：混用 Tokenizer 是新手最容易犯的错误之一。比如用旧版 Qwen2.5 的分词器去加载 Qwen3 的模型，虽然代码可能不报错，但因为两个模型的词表不同，同一个 ID 在不同版本中可能代表完全不同的 token，导致模型输出乱码或逻辑崩坏。<font color=red>解决方案：始终确保 Tokenizer 和 Model 来自同一个文件夹。</font>



`.safetensors` 和 `.bin`（或 `pytorch_model.bin`）都是存储模型权重的格式，但它们有本质的区别。<font color=red>现代模型几乎都使用 `.safetensors` 格式，这是有充分理由的。</font>

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>权重文件格式对比</font></p>
<div class="center">

| 特性           | `.bin` (pickle) | `.safetensors` |
| -------------- | --------------- | -------------- |
| **安全性**     | ⚠️ 危险          | ✅ 安全         |
| **加载速度**   | 较慢            | 快 2-3 倍      |
| **内存映射**   | 不支持          | ✅ 支持 (mmap)  |
| **可执行代码** | 可包含          | 不包含         |
| **推荐程度**   | ❌ 不推荐        | ✅ 强烈推荐     |

`.bin` 文件基于 Python 的 `pickle` 序列化模块。`pickle` 的一个"特性"是：它允许在反序列化（加载文件）时执行任意 Python 代码。这意味着，黑客可以在 `.bin` 文件中植入恶意脚本，当你加载模型时，电脑就可能被控制。

`.safetensors` 是由 Hugging Face 推出的新标准，它是纯二进制格式，只存储张量数据，不包含任何可执行代码，从根本上杜绝了安全风险。此外，它还支持内存映射（Memory Mapping），可以直接将文件从硬盘映射到内存，大大缩短加载时间。

> **实战建议**：在下载模型时，<font color=red>优先选择 `.safetensors` 格式的版本</font>。如果只有 `.bin` 格式可用，要确保来源可信（官方仓库或知名发布者）。



如果你下载过 70B 级别的大模型，你会发现权重文件不是一个，而是被分成了多个文件，比如：

```
model-00001-of-00004.safetensors
model-00002-of-00004.safetensors
model-00003-of-00004.safetensors
model-00004-of-00004.safetensors
model.safetensors.index.json
```

**为什么要分片？**

1. **文件系统限制**：某些文件系统（如 FAT32）对单文件大小有 4GB 限制

2. **并行下载**：分片后可以多线程同时下载，加快速度

3. **断点续传**：下载中断后只需重新下载失败的分片

`model.safetensors.index.json` 是分片的"目录"，它记录了每一层权重存储在哪个文件中。加载库会先读取这个索引文件，然后按需加载对应的分片。

> **避坑提醒**：下载大模型时，一定要确保所有分片都下载完整。如果缺少某个分片，模型加载会直接报错。使用 `huggingface-cli download` 或 `snapshot_download()` 可以自动处理分片下载和完整性校验。

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20260212125401138.png" width=60%></div>

`generation_config.json` 是一个可选但重要的文件，它定义了模型生成文本时的默认行为。

```json
{
  "temperature": 0.7,
  "top_p": 0.8,
  "max_new_tokens": 512,
  "do_sample": true,
  "eos_token_id": 151643
}
```

- **`temperature`**：控制随机性，值越高输出越发散，值越低输出越确定

- **`top_p`**：核采样阈值，只从累积概率达到 p 的 token 中采样

- **`max_new_tokens`**：最大生成长度

- **`eos_token_id`**：结束符 ID，模型生成到这个 token 就停止

> 🔥 **踩坑预警**：很多小白抱怨模型"车轱辘话"或者"停不下来"，往往是因为 `generation_config.json` 中的 `eos_token_id` 设置错误，或者与 Tokenizer 中的定义不一致，导致模型不知道何时该停止生成。<font color=red>解决方案：确保 `eos_token_id` 与 `tokenizer_config.json` 中的定义一致。</font>



### 显存计算

学会计算显存需求，是"下载党"进阶为"架构师"的分水岭。在实际工作中，你经常会遇到这样的问题：

- "老板想在公司服务器上跑 Qwen3-14B，我们的 RTX 4090 够不够？"

- "我在 AutoDL 上租 GPU，应该选 24GB 的 4090 还是 40GB 的 A100？"

- "这个模型说支持 128K 上下文，但为什么我聊几轮就显存爆了？"

> 💡 **官方工具推荐**：阿里云 PAI 平台提供了**简易显存估算器**，可以在线计算模型推理和微调所需的显存。支持 Dense 模型和 MoE 模型，覆盖 16-bit/8-bit/4-bit 等多种精度场景。
>
> 工具地址：https://help.aliyun.com/zh/pai/getting-started/estimation-of-the-required-video-memory-for-the-model



**静态显存：模型权重的硬性门槛**

静态显存是指模型权重本身占用的显存，这是一个固定值，由模型参数量和量化精度决定。
$$
\text{静态显存 (GB)} \approx \frac{\text{参数量 (B)} \times \text{每参数比特数}}{8}
$$
让我们用这个公式计算几个常见模型的显存需求：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Dense 模型静态显存估算示例（FP16 精度）</font></p>
<div class="center">

| 模型      | 参数量 | 计算过程    | FP16 显存需求 |
| --------- | ------ | ----------- | ------------- |
| Qwen3-8B  | 8B     | 8 × 2 字节  | **~16GB**     |
| Qwen3-14B | 14B    | 14 × 2 字节 | **~28GB**     |
| Qwen3-32B | 32B    | 32 × 2 字节 | **~64GB**     |

对于 Dense 模型，这个公式非常直观——参数量乘以每个参数的字节数就是显存需求。但对于 MoE 模型，情况要复杂得多，我们在下面单独讨论。

> 💡 **关于量化**：如果你的显存不够运行 FP16 模型，可以使用量化技术（如 INT4）来大幅减少显存需求。我们将在 **第七章：量化技术入门** 中详细讲解量化原理和实战方法。

> **修正系数**：实际显存占用通常要在公式结果上增加 **1-2 GB**，用于 CUDA 内核开销、显存碎片和临时缓冲区。



**MoE 模型的显存陷阱：用总参数量计算，而非激活参数量**

MoE 模型的"总参数量"和"激活参数量"是两个完全不同的数字。<font color=red>在估算显存时，必须使用总参数量，因为所有专家的权重都必须加载到内存中。</font>这是新手最容易犯的错误之一。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>MoE 模型显存估算的常见误区</font></p>
<div class="center">

| 模型            | 总参数量 | 激活参数量 | ❌ 按激活参数算 (FP16) | ✅ 按总参数算 (FP16)  |
| --------------- | -------- | ---------- | --------------------- | -------------------- |
| DeepSeek-V3     | 671B     | 37B        | ~74 GB                | **~1342 GB (1.3TB)** |
| Qwen3-235B-A22B | 235B     | 22B        | ~44 GB                | **~470 GB**          |

从表格可以看出，如果错误地用激活参数量来估算，你会以为 DeepSeek-V3 只需要 74GB 显存，实际上它需要 1.3TB——差了将近 20 倍。这也解释了为什么 MoE 模型的本地部署通常需要借助 CPU 内存（RAM）来存放大量休眠的专家权重，而不是把所有参数都塞进 GPU 显存。

> ⚠️ **常见误区**：看到 DeepSeek-V3 "激活参数 37B"就以为它和 Qwen3-32B 的显存需求差不多。实际上，DeepSeek-V3 的总参数量是 671B，即使使用 INT4 量化也需要约 230GB 的存储空间。<font color=red>MoE 模型的显存/内存需求，永远由总参数量决定。</font>



**动态显存：KV Cache 的隐藏陷阱**

很多初学者发现：模型加载进去了，显存还剩好几 GB，但刚聊了几轮就报错 OOM（显存溢出）。<font color=red>罪魁祸首就是 KV Cache。</font>

**什么是 KV Cache？**

模型在生成第 N 个 token 时，需要"回头看"前 N-1 个 token 的信息。为了不重复计算，模型会把之前所有 token 的 Key 和 Value 向量缓存起来，这就是 KV Cache。

**KV Cache 的增长规律**

KV Cache 的大小与**上下文长度**成线性正比。对话越长，缓存越大，显存占用越多。

**估算公式**（以 FP16 为例）
$$
\text{KV Cache (GB)} \approx \frac{2 \times \text{层数} \times \text{隐藏维度} \times 2 \times \text{上下文长度}}{1024^3}
$$
**实战数据**（以 Llama 4 Scout 70B 为例，FP16）

- 每 1000 个 token 的 KV Cache 约占用 **640 MB**

- 如果想跑满 128K 上下文：128 × 0.64 GB ≈ **82 GB** 仅用于 KV Cache！

这意味着：即便你有两张 RTX 4090（48GB 总显存），虽然能加载 35GB 的 INT4 权重，但剩下的 13GB 只够支撑约 20K token 的上下文，根本跑不满 128K。

> 🔥 **避坑指南**：不要被模型宣传的"支持 128K 上下文"所迷惑。实际能用多长的上下文，取决于你的显存余量。<font color=red>公式：可用上下文长度 ≈ (总显存 - 模型显存) / 每 1K token 的 KV Cache 大小</font>

<div align=center><img src="https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/ZhiJie/20260212125400979.png" width=60%></div>

为了方便快速查阅，这里整理了 2026 年初主流模型的显存需求和推荐硬件配置：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>2026年主流模型显存速查表（FP16 精度）</font></p>
<div class="center">

| 模型名称        | 架构类型 | 总参数量 | 激活参数量 | FP16 显存 | 推荐配置            |
| --------------- | -------- | -------- | ---------- | --------- | ------------------- |
| Qwen3-1.7B      | Dense    | 1.7B     | 1.7B       | ~3.5 GB   | RTX 3060 (12G)      |
| Qwen3-8B        | Dense    | 8B       | 8B         | ~16 GB    | RTX 4060Ti (16G)    |
| Qwen3-14B       | Dense    | 14B      | 14B        | ~28 GB    | A100 40GB           |
| Qwen3-32B       | Dense    | 32B      | 32B        | ~64 GB    | 2× A100 40GB        |
| Qwen3-235B-A22B | **MoE**  | 235B     | 22B        | ~470 GB   | 需 CPU+GPU 混合推理 |
| DeepSeek-V3     | **MoE**  | 671B     | 37B        | ~1342 GB  | 需 CPU+GPU 混合推理 |

从这张表中可以清晰地看到 Dense 和 MoE 两种架构在显存需求上的巨大差异。Dense 模型的总参数量和激活参数量相同，显存估算直接套公式即可；而 MoE 模型的总参数量远大于激活参数量，<font color=red>显存必须按总参数量计算</font>，这也是为什么 MoE 模型几乎都需要借助 CPU 内存进行混合推理。

> ⚠️ **显存不够？** 上表是 FP16 原始精度的显存需求。如果你的显卡显存不足，可以通过**量化技术**（INT4/INT8）将显存需求降低 2-4 倍。详见 Lesson 4。对于 MoE 模型，还可以通过 Expert Offloading 将休眠专家放到 CPU 内存中，详见后续推理框架课程。

**显存不够怎么办？**

如果你的显卡显存不足以运行目标模型的 FP16 版本，有以下几种解决方案：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>显存不足的解决方案</font></p>
<div class="center">

| 方案               | 适用场景      | 优点         | 缺点             |
| ------------------ | ------------- | ------------ | ---------------- |
| **使用量化模型**   | 显存差 2-4 倍 | 效果接近原版 | 需要学习量化知识 |
| **选择更小的模型** | 显存差很多    | 最简单直接   | 能力上限降低     |
| **租用云 GPU**     | 临时需求      | 按需付费     | 长期成本高       |
| **升级硬件**       | 长期需求      | 一劳永逸     | 前期投入大       |

> 💡 **推荐路径**：对于显存不足的情况，最推荐的方案是使用**量化模型**。INT4 量化可以将显存需求降低到原来的 1/4，效果损失通常在 5% 以内。我们将在 **Lesson 4** 中详细讲解量化技术。



### Transformers 加载模型

---

<font color=red>**过渡**</font>：在上一章我们解剖了模型文件夹，知道了 config.json 和 safetensors 的作用。现在，让我们用 Python 代码把这些文件真正"用"起来。我们将使用 Hugging Face 的 `transformers` 库，这是目前最主流的大模型调用工具。

在开始写代码之前，我们需要安装必要的 Python 库。

```python
# 安装 Hugging Face 核心库
!pip install transformers

# 安装 PyTorch (根据你的 CUDA 版本选择，这里以 CUDA 12.1 为例)
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装加速库（可选但推荐）
!pip install accelerate
```

 **核心代码：加载模型与分词器**

加载一个模型只需要两行核心代码：一行加载**分词器（Tokenizer）**，一行加载**模型（Model）**。

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 1. 设定模型路径（可以是 HuggingFace 上的 ID，也可以是本地路径）
model_path = "./models/Qwen/Qwen2.5-7B-Instruct"  # 如果下载到了本地，替换为本地文件夹路径

# 2. 加载分词器
# trust_remote_code=True 允许加载模型自定义的代码，对于新模型通常需要开启
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

# 3. 加载模型
# device_map="auto" 会自动将模型分配到 GPU（如果显存不够会分到 CPU）
# torch_dtype="auto" 会自动选择精度（通常是 FP16 或 BF16）
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True
)

print(f"模型加载成功！运行在设备：{model.device}")
```

**第一次推理：让模型说话**

模型加载后，我们就可以让它生成文本了。

```python
# 1. 准备输入文本
prompt = "你好，请用一句话介绍你自己。"
messages = [
    {"role": "system", "content": "你是一个有用的 AI 助手。"},
    {"role": "user", "content": prompt}
]

# 2. 应用对话模板（将对话列表转换为模型能看懂的字符串格式）
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 3. 将文本转换为 Token ID（张量）
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# 4. 生成新 Token
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens=512,  # 最多生成 512 个 token
    temperature=0.7      # 控制随机性
)

# 5. 只取新生成的 token（去掉输入的 prompt 部分）
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

# 6. 解码：将 Token ID 转回文本
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("模型回答：", response)
```

### 量化技术入门

---

<font color=red>**过渡**</font>：在云端跑通了代码是第一步，但要在本地（尤其是显存有限的消费级显卡）上跑大模型，就必须掌握核心'黑科技'——量化。这一章我们将深入底层，理解为什么模型可以变小而不变笨。

**精度与量化基础**

在深入量化技术之前，我们需要先理解一个基础问题：同一个模型，为什么有 FP16、INT8、INT4 这么多版本？它们之间有什么区别？为什么 INT4 版本的文件只有 FP16 版本的四分之一大小，但效果却差不多？

这就是我们这一节要深入探讨的主题：<font color=red>精度（Precision）与量化（Quantization）</font>。这是让消费级显卡（如 RTX 4090）能够运行企业级大模型的关键技术。

**数据精度的物理意义**

计算机中存储小数（浮点数）有不同的格式，占用的空间（显存）也不同。让我们从最基础的概念开始理解。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>常用数据精度对比</font></p>
<div class="center">

| 精度类型 | 位数   | 每参数字节数 | 数值范围     | 典型用途          |
| -------- | ------ | ------------ | ------------ | ----------------- |
| FP32     | 32-bit | 4 字节       | 极大         | 训练（黄金标准）  |
| FP16     | 16-bit | 2 字节       | 较小，易溢出 | 推理（传统）      |
| BF16     | 16-bit | 2 字节       | 与 FP32 相同 | 训练+推理（推荐） |
| INT8     | 8-bit  | 1 字节       | 整数范围     | 量化推理          |
| INT4     | 4-bit  | 0.5 字节     | 整数范围     | 量化推理（主流）  |

- **FP32（单精度）**：深度学习训练的"黄金标准"，精度极高，但一个 70B 模型需要 280GB 显存，远超任何消费级显卡。


- **FP16（半精度）**：推理的传统选择，显存需求减半。但数值范围较小，训练时容易出现数值溢出导致 NaN。


- **BF16（Brain Float 16）**：Google 为 AI 设计的格式，保留了 FP32 的指数位（数值范围相同），截断了尾数位。是 Ampere 架构（RTX 30系）及以后显卡的标配，<font color=red>推荐在支持的硬件上优先使用 BF16</font>。


- **INT8/INT4（整数量化）**：用整数来近似表示浮点数，大幅减少显存占用，是本地部署大模型的关键技术。

> ⚠️ **FP16 vs BF16 的区别**：虽然两者都占 2 字节，但内部结构不同。BF16 保留了与 FP32 相同的指数位宽度，因此数值范围更大，训练时不易溢出；FP16 的尾数位更多，数值精度更高，但动态范围较小。<font color=red>简单记忆：BF16 更适合训练和微调，FP16 更常用于推理。</font>在量化场景中，两者作为"基线精度"的表现几乎一致。

**量化：以"模糊"换"空间"**

量化（Quantization）的本质是：<font color=red>将高精度的浮点数映射为低精度的整数，从而大幅减少显存占用</font>。这就像是把一张 4K 高清图片压缩成缩略图——文件变小了，但主体信息还在。

**量化的数学直觉**

假设模型中某个权重的原始值是 `0.12345678`（FP32，占 4 字节）：

- **FP16 转换**：保留约 4 位有效数字，变成 `0.1235`（占 2 字节）

- **INT8 量化**：映射到 [-128, 127] 的整数范围，可能变成 `31`（占 1 字节）

- **INT4 量化**：映射到 [-8, 7] 的整数范围，可能变成 `2`（占 0.5 字节）

量化后的整数需要配合一个"缩放因子"才能还原近似的原始值。这个过程会损失一些精度，但对于大多数任务来说，这种损失是可以接受的。

让我们用具体数字来感受量化的威力：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>70B 模型在不同精度下的显存需求</font></p>
<div class="center">

| 精度      | 计算公式       | 显存需求  | 可运行硬件        |
| --------- | -------------- | --------- | ----------------- |
| FP32      | 70B × 4 字节   | 280 GB    | 多卡 A100 集群    |
| FP16/BF16 | 70B × 2 字节   | 140 GB    | 4× A100 80GB      |
| INT8      | 70B × 1 字节   | 70 GB     | 2× RTX 4090       |
| **INT4**  | 70B × 0.5 字节 | **35 GB** | **2× RTX 3090** ✅ |

这就是为什么 INT4 量化如此重要：<font color=red>它让原本需要几十万元服务器才能跑的 70B 模型，变成了双卡 3090 就能本地运行</font>。

**INT4 量化的实际表现**

你可能会担心：精度损失这么多，模型效果会不会大打折扣？

答案是：<font color=red>对于大多数应用场景（对话、摘要、代码生成），INT4 量化的效果与 FP16 惊人地接近</font>。

**困惑度（Perplexity）—— 量化质量的核心指标**

Perplexity（简称 PPL）是衡量语言模型**预测下一个 Token 能力**的标准指标。简单来说，它衡量模型对一段文本感到"惊讶"的程度——<font color=red>PPL 越低越好</font>，低 PPL 意味着模型能准确预测接下来的内容，生成的文本更通顺、逻辑更连贯。FP16 原始模型的 PPL 是"金标准"，量化后 PPL 会略微上升。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Qwen3-8B 不同精度困惑度对比</font></p>
<div class="center">

| 精度版本      | 困惑度 | 相对变化 | 主观体验         |
| ------------- | ------ | -------- | ---------------- |
| FP16          | 5.12   | 基准     | 最佳             |
| INT8          | 5.18   | +1.2%    | 几乎无差异       |
| INT4 (Q4_K_M) | 5.38   | +5.1%    | 略有下降，可接受 |
| INT2          | 6.20   | +21.1%   | 明显下降         |

从数据可以看出，INT4 量化只带来约 5% 的困惑度上升，在实际使用中几乎感知不到差异。这就是为什么<font color=red> INT4 是目前本地部署的"甜点"精度</font>——在显存节省和效果保持之间取得了最佳平衡。

**PPL 变化幅度的判断法则**

当你在 Hugging Face 上对比多个量化版本时，可以用以下标准快速判断质量：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>PPL 变化幅度的质量判断标准</font></p>
<div class="center">

| PPL 变化幅度（相对 FP16） | 含义           | 体感                       |
| ------------------------- | -------------- | -------------------------- |
| **增加 1% - 3%**          | ✅ 可视为"无损" | 人类几乎察觉不到差异       |
| **增加 3% - 10%**         | ⚠️ 轻微有损     | 复杂推理任务中可能有感知   |
| **增加 >10%**             | ❌ 严重有损     | 模型开始胡言乱语或丧失逻辑 |

> ⚠️ **PPL 的局限性**：低 PPL 并不代表模型"聪明"。一个模型可以生成很通顺的句子（低 PPL），但在解数学题或遵循复杂指令时完全失败。因此 PPL 只是**必要条件**，不是充分条件。对于编程、数学或强逻辑任务，<font color=red>4-bit 是底线</font>——即使 PPL 看起来还可以，3-bit 模型在 Math/Coding 任务上的准确率通常会大幅下降。



**量化格式详解**

理解了量化的基本原理后，你在下载量化模型时会发现：同样是 INT4 量化，怎么有 GGUF、GPTQ、AWQ 这么多格式？它们有什么区别？应该选哪个？

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>量化格式特性对比</font></p>
<div class="center">

| 格式     | 全称                                 | 核心特点           | 适用场景              | 代表工具  |
| -------- | ------------------------------------ | ------------------ | --------------------- | --------- |
| **GGUF** | GPT-Generated Unified Format         | CPU/GPU 混合推理   | ollama、Mac、显存不足 | llama.cpp |
| **GPTQ** | GPT Quantization                     | 纯 GPU，需校准数据 | vLLM、高吞吐服务      | AutoGPTQ  |
| **AWQ**  | Activation-aware Weight Quantization | 激活感知，效果好   | vLLM、TGI             | AutoAWQ   |



 **GGUF：最灵活的通用格式**

GGUF（GPT-Generated Unified Format）是由 `llama.cpp` 团队开发的量化格式，也是目前最普及的本地部署格式。它的核心优势可以用一句话概括：<font color=red>显存不够，内存来凑。</font>

**核心优势：CPU/GPU 混合卸载**

其他格式（如 AWQ、GPTQ）要求模型完全装入显存，溢出即报错 OOM（Out Of Memory）。而 GGUF 允许将一部分层加载到 GPU（显存），剩余部分留在系统内存（RAM）由 CPU 计算。

> **场景举例**：你有一张 24GB 的 RTX 4090，想运行 70B 的 Q4 模型（约 40GB）。
> - 纯 GPU 方案（AWQ/GPTQ）：直接 OOM，无法运行。
> - GGUF 方案：约 40 层装入显存（24GB），剩余层留在内存。速度从 50 t/s 降至 3-5 t/s，但至少**能跑**。

除了混合推理，GGUF 还有以下优势：

- **单文件部署**：所有信息（权重、配置、分词器）打包在一个 `.gguf` 文件中，下载即用

- **广泛兼容**：`ollama`、LM Studio、`llama.cpp` 等主流工具都原生支持

- **Mac 友好**：充分利用 Apple Silicon 的统一内存架构，在 Mac 上性能表现优异

**K-Quants：混合精度的艺术**

GGUF 的 K-Quants 技术是一种精细的块状量化方案——它的核心洞察是：<font color=red>并非所有权重都同等重要。</font>

以常用的 **Q4_K_M** 为例：注意力机制中的关键权重使用 6-bit 保存，而前馈网络的权重使用 4-bit。这种"好钢用在刀刃上"的策略，使得 Q4_K_M 在体积与传统 Q4_0 几乎相同的情况下，推理质量大幅提升。

你在下载 GGUF 模型时会看到 Q4_K_M、Q5_K_S 这样的命名，以下是各等级的详细对比：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>GGUF 不同量化等级的特性对比</font></p>
<div class="center">

| 量化后缀   | 平均位宽 (bpw) | 质量描述                                  | 适用场景                 | 70B 模型体积 |
| ---------- | -------------- | ----------------------------------------- | ------------------------ | ------------ |
| **Q8_0**   | 8.0            | 无损级，几乎等同 FP16                     | 研究基准、高端工作站     | ~75 GB       |
| **Q5_K_M** | ~5.7           | 质量与体积的最佳平衡（高配）              | 显存充足时首选           | ~50 GB       |
| **Q4_K_M** | ~4.8           | ⭐ **最常用的平衡选择**，保留 98% 推理能力 | **大多数用户的默认选择** | ~42.5 GB     |
| **IQ4_XS** | ~4.3           | 利用重要性矩阵压缩，优于 Q4_K_S           | 极限显存环境的高质量选择 | ~38 GB       |
| **IQ3_M**  | ~3.7           | 质量有可见下降，逻辑任务仍可用            | 单卡 24GB 强跑大模型时   | ~32 GB       |
| **Q2_K**   | ~2.5           | 损失较大，仅应急使用                      | 极端显存限制             | ~22 GB       |

> **术语解释**：**bpw（bits per weight）** 表示平均每个权重参数占用的比特数。例如 Q4_K_M 的 bpw 约 4.8，意味着平均每个参数占 4.8 bit（而非严格的 4 bit），因为加上了缩放因子的存储开销。

**I-Quants 与重要性矩阵（Importance Matrix）**

GGUF 的 I-Quants（如 IQ4_XS、IQ3_M）使用了更进一步的**非均匀量化**策略。它配合校准数据集计算出"重要性矩阵"，为每个权重打"重要性分数"——对重要性高的权重保留更多精度，对不重要的权重更激进地压缩。

效果：IQ4_XS（约 4.25 bpw）能以比 Q4_K_S 更小的体积，达成接近 Q4_K_M 的性能。<font color=red>如果你的显存极度紧张，IQ 系列是比传统 Q 系列更好的选择。</font>

> 🔥 **踩坑预警**：I-Quants 的质量高度依赖校准数据集。如果量化时使用的校准数据是英文 WikiText，而你主要用于中文对话，效果可能不如预期。下载时注意查看模型卡片中的校准数据集信息。



**AWQ 与 GPTQ：GPU 专属格式**

如果你有足够的显存将模型完全装入 GPU，且追求最快的推理速度，AWQ 和 GPTQ 是更好的选择。它们都属于纯 GPU 格式——<font color=red>模型必须完全装入显存，不支持 CPU 卸载，显存溢出直接报错 OOM。</font>

**AWQ（Activation-aware Weight Quantization）—— 激活感知量化**

AWQ 是目前 `vLLM` 等服务端推理引擎的首选格式。它的核心洞察非常精妙：在模型的数十亿个参数中，约有 **1%** 的权重会产生非常大的激活值，这些被称为"显著权重（Salient Weights）"。

AWQ 的策略是：通过缩放因子保护这 1% 关键权重的精度，只压缩剩下的 99%。这就像是一个公司裁员时，核心骨干（1%）不动，只精简非核心岗位（99%）——公司的核心战斗力几乎不受影响。

- **优点**：在同等压缩率下效果更好，指令遵循和代码生成能力保持较好

- **适用场景**：需要高并发吞吐的 API 服务部署（配合 vLLM）、追求极致推理速度的纯 GPU 环境

**GPTQ（GPT Quantization）—— 经典方案**

GPTQ 是早期量化技术的代表方案。它利用海森矩阵（Hessian Matrix，二阶导数信息）来判断哪些权重对输出最敏感，并在量化时对这些敏感权重进行误差补偿。

**与 AWQ 的核心区别**：

- GPTQ 关注"权重本身的数学敏感度"（海森矩阵）

- AWQ 关注"权重在推理时产生的激活大小"（激活感知）

- 在一些评测中，AWQ 在指令遵循和代码生成上略胜一筹，因为它更好地保护了实际推理中最关键的权重

**应用现状**：GPTQ 已逐渐被 AWQ 取代为首选，但在部分旧硬件或 AutoGPTQ 等框架中仍被广泛支持，兼容性较好。



**Weight-Only 量化：为什么只压缩权重？**

在理解了三大格式之后，你可能会产生一个更深层的疑问：为什么这些格式都只量化权重，而不量化激活值？这就是 **Weight-Only 量化**的核心机制。

Weight-Only 量化是指**只压缩模型的权重参数**，而在推理计算时，激活值（输入数据经过层级计算后的中间结果）仍然保持高精度（FP16/BF16）。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Weight-Only 量化的两步机制</font></p>
<div class="center">

| 阶段       | 操作                                                         | 精度           |
| ---------- | ------------------------------------------------------------ | -------------- |
| **存储时** | 权重以低精度保存（如 INT4），大幅减少显存占用和磁盘体积      | INT4（4-bit）  |
| **计算时** | 系统将该层的 INT4 权重**解压缩（Dequantize）**回 FP16，然后与 FP16 的激活值进行矩阵乘法 | FP16（16-bit） |

**为什么这样做反而更快？**

大语言模型推理的主要瓶颈通常不是"算得慢"，而是"读得慢"——瓶颈在**显存带宽**。每生成一个 Token，都需要将模型的全部权重从显存读取到计算单元一次。Weight-Only 量化把权重从 FP16 压缩到 INT4，数据量减少到四分之一，从显存读取数据的时间大幅缩短。因此，Weight-Only 量化<font color=red>既降低了硬件门槛，又往往能提高推理速度</font>。

> 💡 **重要认知**：前面介绍的 GGUF（Q4_K_M 等）、GPTQ 和 AWQ，都属于 Weight-Only 量化。理解了这个机制，你就能明白为什么量化模型"存储小但计算不慢"。

**Calibration（校准）：用小数据集"微调"量化精度**

在量化过程中，并非所有权重都同等重要。盲目地把每个数字都从 FP16 压成 INT4，会导致模型变"傻"。**Calibration（校准）** 就是在量化时，使用少量真实数据（通常 128-512 条文本片段）运行模型，收集统计信息，帮助算法识别<font color=red>哪些权重必须小心保护</font>。

三大格式的校准方法各有不同：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>主流量化格式的校准方法对比</font></p>
<div class="center">

| 量化格式          | 校准方法             | 核心逻辑                                                     |
| ----------------- | -------------------- | ------------------------------------------------------------ |
| **GPTQ**          | 海森矩阵（二阶导数） | 找到对输出误差**最敏感**的权重，量化时对其进行误差补偿       |
| **AWQ**           | 激活感知             | 观察激活值大小，发现约 **1%** 的权重产生巨大激活值，必须保护 |
| **GGUF I-Matrix** | 重要性矩阵           | 为每个权重打"重要性分数"，为重要权重分配更多比特             |

> ⚠️ **校准数据与使用场景不匹配的陷阱**：如果量化时使用的校准数据集（如英文 WikiText）与你实际使用场景（如中文对话）差异过大，量化后的模型可能会在特定任务上表现不佳。自己转换模型时（使用 `llama.cpp` 的 `quantize` 工具），低比特量化务必使用 `--imatrix` 参数并提供与使用场景匹配的校准数据集。



**实战指南：4 步选择量化模型**

掌握了以上所有知识后，我们来把它们串成一个实用的决策流程。当你需要下载和选择量化模型时，按以下 4 步操作：

**步骤一：根据硬件选择量化格式**

你不需要自己训练量化模型，通常是直接下载现成的。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>硬件环境与量化格式匹配指南</font></p>
<div class="center">

| 硬件环境                     | 推荐格式 | 加载工具              | 优势                              |
| ---------------------------- | -------- | --------------------- | --------------------------------- |
| **Apple Mac（M1/M2/M3/M4）** | **GGUF** | LM Studio / ollama    | 利用统一内存架构，速度快          |
| **NVIDIA 显卡（显存充足）**  | **AWQ**  | vLLM / Text-Gen-WebUI | 在同等量化精度下推理速度较快      |
| **NVIDIA 显卡（显存不足）**  | **GGUF** | ollama / LM Studio    | 支持 CPU/GPU 混合运算，虽慢但能跑 |
| **只有 CPU（旧电脑）**       | **GGUF** | llama.cpp             | 极慢，但不受显卡限制              |

**步骤二：通过 PPL 快速筛选版本**

在 Hugging Face 上看到多个量化版本（如 Q4_0、Q4_K_S、Q4_K_M）时，查看作者提供的 PPL 表格：

- 对比 FP16 基线，PPL 增加在 **1%-3%** 以内 → 通常认为"无损"

- PPL 暴增（>10%）逻辑推理中很可能"崩坏"

- **经验**：Q4_K_M 通常比 Q4_0 的 PPL 更低（更好），因为前者使用了更智能的超块结构

**步骤三：关注校准数据集**

- 下载 IQ 系列 GGUF（如 IQ4_XS）或 GPTQ 模型时，注意校准数据集是什么

- 英文 WikiText 校准的模型 → 用于中文任务时可能稍差

- 如果自己量化，低比特务必使用 `--imatrix` 参数并提供匹配的校准数据

**步骤四：超越 PPL 的终极判断**

- **4-bit 是底线**：即使 PPL 看起来还可以，3-bit 模型在 Math/Coding 任务上的准确率通常大幅下降

- **AWQ vs GPTQ**：AWQ 在指令遵循和代码生成上通常略胜一筹

**总结建议**：日常使用首选 **4-bit Weight-Only 量化（Q4_K_M / AWQ）**。这通常能在 PPL 几乎无损的情况下，节省一半以上的显存。只有在显存极其紧张时，才考虑依赖校准优化过的 **3-bit（IQ3）**，并接受其在复杂逻辑任务上变弱的现实。

**格式选择决策树**

```
你的场景是什么？
    │
    ├─→ 显存充足 + 追求速度 → AWQ/GPTQ + vLLM
    │
    ├─→ 显存不足 + 能接受慢速 → GGUF + ollama（CPU 卸载）
    │
    ├─→ Mac 用户 → GGUF + ollama/LM Studio
    │
    └─→ 快速体验 + 一键部署 → GGUF + ollama
```



**KV Cache 量化：长上下文的显存救星**

在 Lesson 2 中我们讲过，KV Cache 是显存的"隐形杀手"——模型加载进去了，但聊几轮就 OOM。llama.cpp 提供了一个强大的解决方案：<font color=red>对 KV Cache 本身进行量化</font>，在几乎不损失质量的前提下大幅减少 KV Cache 的显存占用。

**KV Cache 量化参数**

通过 `-ctk`（Cache Type Key）和 `-ctv`（Cache Type Value）参数控制：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>KV Cache 量化类型与显存节省（Llama 3 8B, 128K 上下文）</font></p>
<div class="center">

| KV Cache 类型    | 显存占用（仅 Cache） | 节省比例 | 质量影响             |
| ---------------- | -------------------- | -------- | -------------------- |
| **FP16**（默认） | ~23.3 GB             | 0%       | 基准                 |
| **q8_0**         | ~17.0 GB             | ~27%     | **几乎无损（推荐）** |
| **q4_0**         | ~13.8 GB             | ~40%     | 轻微降级             |

从表格可以看出，仅仅将 KV Cache 从 FP16 切换到 q8_0，就能节省约 27% 的 Cache 显存，而质量损失几乎为零。这意味着在同样的显存条件下，你可以支持更长的上下文，或者为更多并发用户留出空间。

> 💡 **工程建议**：如果你的显存紧张且需要长上下文，启动 llama-server 时务必加上 `--cache-type-k q8_0 --cache-type-v q8_0`。这是<font color=red>性价比最高的显存优化手段</font>，几乎零成本。

**llama-server：搭建本地 API 服务**

学会了模型转换和量化后，最后一步是把量化模型跑起来，搭建一个可以被程序调用的 API 服务。`llama-server` 是 llama.cpp 内置的生产级 HTTP 服务器，<font color=red>兼容 OpenAI API 协议</font>，这意味着你可以用 `openai` Python 库直接调用，无需学习新的 API。

**启动命令与关键参数**

```python
# 注意启动时命令中斜杠后不要有空格！
!./llama-server \
  -m qwen3-8b-q4_k_m.gguf \    # 指定量化模型路径
  -c 8192 \                     # 上下文窗口大小
  -ngl 99 \                     # GPU 层数卸载（99 = 全部放 GPU）
  --host 0.0.0.0 \              # 监听所有 IP
  --port 8080 \                 # 端口
  -np 4 \                       # 并行槽位数
  -cb \                         # 开启连续批处理
  --cache-type-k q8_0 \         # KV Cache Key 量化
  --cache-type-v q8_0           # KV Cache Value 量化


!./llama-server -m /root/autodl-tmp/models/qwen3-0.6b-q4_k_m.gguf -c 8192 -ngl 99 --host 0.0.0.0 --port 8080 -np 4 -cb
!--cache-type-k q8_0 --cache-type-v q8_0
```

关键参数解读：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>llama-server 核心参数说明</font></p>
<div class="center">

| 参数   | 含义              | 建议值                                             |
| ------ | ----------------- | -------------------------------------------------- |
| `-m`   | 模型文件路径      | 你的 .gguf 文件路径                                |
| `-c`   | 上下文窗口总大小  | 根据显存余量设置，8192 是安全起点                  |
| `-ngl` | 卸载到 GPU 的层数 | 99 表示全部放 GPU；显存不足时减小此值              |
| `-np`  | 并行槽位数        | 同时服务的用户数，每个槽位分得 `-c / -np` 的上下文 |
| `-cb`  | 连续批处理        | 建议始终开启，提升多用户并发吞吐量                 |

> ⚠️ **常见误区**：`-np 4` 并不是"让模型变快 4 倍"，而是"同时服务 4 个用户"。每个用户的可用上下文长度 = `-c / -np`。如果 `-c 8192 -np 4`，则每个用户最多使用 2048 tokens 的上下文。

**Python API 调用示例**

由于 `llama-server` 兼容 OpenAI 协议，你可以直接使用 `openai` Python 库进行调用，代码与调用 GPT-3.5/4 几乎完全一致：

```python
from openai import OpenAI

# 指向本地 llama-server
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-no-key-required"  # 本地服务不需要真实 API Key
)

response = client.chat.completions.create(
    model="qwen3-8b",  # 模型名称可随意填写，llama-server 会忽略
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "请用一句话解释什么是量化技术。"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

这段代码通过 `openai` 库向本地的 `llama-server` 发送请求，并以流式方式接收生成的文本。`base_url` 指向本地的 8080 端口，`api_key` 填写任意值即可（本地服务不做鉴权）。

执行后你应该能看到模型逐字输出回答。如果看到了输出，<font color=red>恭喜你——你已经成功搭建了一个完全本地化的、兼容 OpenAI 协议的大模型 API 服务！</font>这意味着你可以用它替代 OpenAI API 接入任何支持 OpenAI 协议的应用（如 LangChain、Open WebUI、SillyTavern 等）。

> 💡 **实战价值**：掌握 llama-server 的部署能力后，你可以为企业搭建完全私有化的大模型服务——数据不出域、零 API 费用、延迟可控。这是企业级 AI 落地中最核心的工程能力之一。

**单模型服务架构与多模型部署**

在使用 `llama-server` 时，有一个非常重要的架构特性需要理解：<font color=red>`llama-server` 是单模型服务——一个端口只服务于一个模型。</font>这与 `ollama`（一个端口可通过 `model` 参数切换模型）或 `vLLM`（支持多模型路由）有本质区别。

```
┌─────────────────────────────────────────────────────┐
│                  llama-server                        │
│                                                      │
│   启动命令：                                          │
│   ./llama-server -m model_A.gguf --port 8080        │
│                                                      │
│   → IP:Port = 0.0.0.0:8080                          │
│   → 服务模型 = model_A.gguf（固定）                   │
│                                                      │
│   所有发到 8080 端口的请求，                           │
│   都会由 model_A 处理，无论 API 中 model 参数填什么    │
└─────────────────────────────────────────────────────┘
```

这意味着 API 请求中的 `model` 参数只是一个标识符，不影响实际使用的模型——端口决定模型，`model` 参数可以填任意字符串。你可以通过 `curl http://localhost:8080/v1/models` 查看当前端口绑定的模型名称。

如果你需要同时运行多个模型，解决方案是启动多个 `llama-server` 实例，分配不同端口：

```python
# 终端 1：模型 A 在 8080 端口
!./llama-server -m model_A.gguf --port 8080

# 终端 2：模型 B 在 8081 端口
!./llama-server -m model_B.gguf --port 8081
```

这种"一端口一模型"的设计虽然看起来不够灵活，但在生产环境中反而是优势——每个模型实例的资源（显存、CPU）完全隔离，不会互相干扰，便于独立监控和扩缩容。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>主流推理服务的模型绑定方式对比</font></p>
<div class="center">

| 服务             | 模型绑定方式                      | 多模型支持    |
| ---------------- | --------------------------------- | ------------- |
| **llama-server** | 一个端口 = 一个模型               | 多实例多端口  |
| **ollama**       | 一个端口，通过 `model` 参数切换   | 自动加载/卸载 |
| **vLLM**         | 支持多模型，通过 `model` 参数路由 | 原生多模型    |



**llama.cpp vs KTransformers：如何选择**

学完了 `llama.cpp` 和 `KTransformers` 两种部署方案后，一个自然的问题是：我应该选哪个？答案取决于你的模型类型和硬件条件。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>llama.cpp 与 KTransformers 全维度对比</font></p>
<div class="center">

| 维度             | llama.cpp               | KTransformers                   |
| ---------------- | ----------------------- | ------------------------------- |
| **安装复杂度**   | 简单（编译即用）        | 较复杂（需 HF + GGUF + SGLang） |
| **操作系统**     | Linux / macOS / Windows | 仅 Linux                        |
| **模型文件**     | 仅需一个 GGUF 文件      | 需要完整 HF 模型 + GGUF 权重    |
| **MoE 优化**     | 无特殊优化              | 专门的热/冷专家分离，效果显著   |
| **CPU 卸载策略** | 按层卸载（被动兜底）    | 按专家卸载（智能分配）          |
| **适用模型**     | 通用（Dense + MoE）     | 主要针对 MoE 模型               |
| **显存需求**     | 取决于 `-ngl` 参数      | 可用 24GB 跑 671B MoE 模型      |

简单来说，选择逻辑如下：

```
你要部署什么模型？
    │
    ├─→ Dense 模型（Qwen3-8B、Llama-3-70B 等）
    │       → 选 llama.cpp（通用、简单、全平台）
    │
    ├─→ MoE 模型 + 显存充足（能装下全部专家）
    │       → 选 llama.cpp（简单够用）
    │
    ├─→ MoE 模型 + 显存不足（如 24GB 跑 671B）
    │       → 选 KTransformers（专业 MoE 优化）
    │
    └─→ Mac 用户
            → 选 llama.cpp（KTransformers 不支持 macOS）
```

值得一提的是，这两个工具并不互斥。在实际工作流中，你完全可以用 `llama.cpp` 快速测试和验证 GGUF 模型，确认效果后再用 `KTransformers` 部署超大 MoE 模型的生产服务。

### 本地推理终极方案——Ollama 与 vLLM

---

<font color=red>**过渡**</font>：掌握了底层工具（llama.cpp）后，我们最后来学习两个'集大成者'：面向开发者的 Ollama（极简）和面向生产环境的 vLLM（极速）。这一章将帮你完成从'跑通模型'到'提供服务'的最后一步。

完成了云端算力的获取后，我们将开始在这台云服务器上部署第一个大模型推理框架——Ollama。Ollama以其极简的设计和开箱即用的体验，成为本地大模型部署的首选工具。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Ollama与vLLM核心对比</font></p>
<div class="center">

| 对比维度       | Ollama                  | vLLM                          |
| -------------- | ----------------------- | ----------------------------- |
| **核心定位**   | 开发者工具、本地实验    | 企业级API服务、高吞吐量       |
| **底层技术**   | llama.cpp (GGUF, mmap)  | PagedAttention (KV Cache优化) |
| **并发能力**   | 适合单用户或少量并发    | 支持数百并发连接              |
| **硬件要求**   | 极低，支持CPU/消费级GPU | 较高，主要针对数据中心级GPU   |
| **部署复杂度** | 极简（一条命令）        | 较复杂，需精细配置            |

> **关于性能基准数据的说明**：
>
> 网络上流传的vLLM与Ollama性能对比数据（如"vLLM 793 TPS vs Ollama 41 TPS"）来源于特定基准测试环境（如2025年8月Red Hat基准测试），**实际性能会因硬件配置、模型大小、并发量等因素显著变化**。
>
> 根据2025年多项基准测试，**在高并发场景下vLLM吞吐量可达Ollama的2-3倍以上**，但在低并发/单用户场景下差距较小。

<font color=red>**简单原则**：如果目的是个人研究、调试Prompt或运行非生产级应用，Ollama是首选；若需对外提供高并发API服务，则应转向vLLM。</font>

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>推理引擎横向对比</font></p>
<div class="center">

| 特性           | Ollama       | vLLM           | TensorRT-LLM |
| -------------- | ------------ | -------------- | ------------ |
| **核心定位**   | 开发者工具   | 高吞吐生产服务 | 极致延迟     |
| **显存管理**   | llama.cpp    | PagedAttention | CUDA内核优化 |
| **吞吐量**     | 低-中等      | **极高**       | 高           |
| **部署复杂度** | **极简**     | 中等           | 复杂         |
| **模型支持**   | 广泛（GGUF） | **最广（HF）** | 需转换格式   |

**选型建议**：
- **个人实验/Prompt调试**：Ollama

- **生产API服务/高并发**：vLLM

- **极致延迟/固定硬件**：TensorRT-LLM

---



**课程总结与项目实战反思**

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>前九章知识点在 Ollama / vLLM 实战中的应用映射</font></p>
<div class="center">

| 章节                          | 核心知识点                          | 在 Ollama 实战中的体现                      | 在 vLLM 实战中的体现                             |
| ----------------------------- | ----------------------------------- | ------------------------------------------- | ------------------------------------------------ |
| **第一章：托管平台**          | Hugging Face / ModelScope 模型检索  | 通过 Modelfile 导入 GGUF 模型               | `huggingface-cli download` 下载 safetensors 权重 |
| **第二章：GitHub**            | 开源项目结构、README 阅读           | 查阅 Ollama 官方文档与 issue                | 查阅 vLLM 参数说明与版本变更                     |
| **第三章：权重与文件结构**    | safetensors、config.json、tokenizer | Ollama 底层使用 GGUF 格式（llama.cpp 转换） | 直接加载 HF 格式的 safetensors + config.json     |
| **第四章：Transformers 加载** | `AutoModelForCausalLM`、pipeline    | 理解 Ollama 封装了哪些底层操作              | vLLM 内部同样基于 HF 模型加载机制                |
| **第五章：AutoDL 云端部署**   | 实例选型、SSH 连接、数据盘挂载      | Ollama 模型存储到 `/root/autodl-tmp/`       | vLLM 模型路径指向数据盘                          |
| **第六章：环境验证**          | `nvidia-smi`、CUDA 版本确认         | 验证 GPU 驱动是否支持 Ollama                | 确认 CUDA/PyTorch 版本与 vLLM 兼容               |
| **第七章：量化技术**          | FP16/INT8/INT4、GGUF 量化等级       | `ollama pull` 默认下载 Q4_K_M 量化版        | vLLM 支持 AWQ/GPTQ 量化模型加载                  |
| **第八章：量化工具链**        | llama.cpp、Unsloth                  | Ollama 底层即 llama.cpp                     | vLLM 使用 AutoAWQ/AutoGPTQ 集成                  |
| **第九章：Ollama 与 vLLM**    | 安装、配置、API 部署、SDK 调用      | 完整部署 + OpenAI 兼容 API                  | 完整部署 + 生产级 API 服务                       |

&emsp;&emsp;一个值得注意的细节是：无论使用 Ollama 还是 vLLM，客户端调用代码的结构完全一致，只需修改两个参数。这得益于两者都实现了 `OpenAI API` 兼容协议：

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Ollama vs vLLM 调用参数对比</font></p>
<div class="center">

| 参数       | Ollama                      | vLLM                       | 说明                                                         |
| ---------- | --------------------------- | -------------------------- | ------------------------------------------------------------ |
| `base_url` | `http://localhost:11434/v1` | `http://localhost:8000/v1` | 端口不同：Ollama 默认 11434，vLLM 默认 8000                  |
| `model`    | `"my-deepseek"`             | `"qwen2.5"`                | Ollama 用模型标签名，vLLM 用 `--served-model-name` 指定的名称 |
| `api_key`  | `"EMPTY"`                   | `"EMPTY"`                  | 本地部署无需真实密钥，填任意非空字符串即可                   |
| SDK 代码   | 完全相同                    | 完全相同                   | `client.chat.completions.create(...)` 调用方式一致           |

&emsp;&emsp;<font color=red>这意味着你的应用代码可以在 Ollama、vLLM、OpenAI 官方 API 之间自由切换，只需修改配置文件中的 `base_url` 和 `model` 两个字段</font>。这种统一接口的设计大大降低了技术选型的切换成本。

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>vLLM 部署高频踩坑与排查方案</font></p>
<div class="center">

| 问题现象                                                     | 根因分析                                                     | 解决方案                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `--served-model-name` 不生效，模型名显示为完整路径           | 多行命令的 `\` 续行符后有不可见的尾随空格，导致 shell 在第一行就截断了命令 | 删除每行 `\` 后的所有空格，或将整条命令写在一行              |
| API 返回 `set_num_threads expects a positive integer`        | 系统环境变量 `OMP_NUM_THREADS` 被设置为无效值（空字符串或非正整数） | 启动前执行 `export OMP_NUM_THREADS=1`                        |
| `completion.choices` 为 `None`，触发 `TypeError: 'NoneType' object is not subscriptable` | API 返回了错误响应但未抛出异常，`choices` 字段为空           | 先 `print(completion)` 查看完整返回体，根据 `error.message` 定位具体原因 |
| `max_model_len` 显示为模型默认值而非指定值                   | 同"续行符空格"问题，`--max-model-len` 参数未被传递           | 检查启动命令的参数完整性，确认 `non-default args` 日志       |
| `CUDA out of memory`                                         | 模型所需显存超过 GPU 可用显存                                | 降低 `--gpu-memory-utilization`（如 0.7）或减小 `--max-model-len`，或换用量化版模型 |
| `Connection refused` 无法连接 8000 端口                      | vLLM 服务未启动成功，或绑定了错误的 host                     | 检查服务端日志，确认 `--host 0.0.0.0` 参数生效               |

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>Ollama 部署高频踩坑与排查方案</font></p>
<div class="center">

| 问题现象                         | 根因分析                                   | 解决方案                                                     |
| -------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| `ollama pull` 下载速度极慢或超时 | 默认从 ollama.com 下载，国内网络不稳定     | 使用镜像源，或手动下载 GGUF 文件后通过 Modelfile 导入        |
| 模型下载到系统盘导致磁盘满       | Ollama 默认存储路径在 `~/.ollama/models`   | 设置 `OLLAMA_MODELS=/root/autodl-tmp/ollama_models` 环境变量 |
| `ollama serve` 报端口被占用      | 11434 端口已有其他进程占用                 | `lsof -i :11434` 查找占用进程，`kill` 后重启                 |
| 模型运行时 GPU 利用率为 0%       | Ollama 未检测到 CUDA 环境，回退到 CPU 推理 | 确认 `nvidia-smi` 正常，重新安装支持 GPU 的 Ollama 版本      |
| 自定义 Modelfile 创建失败        | GGUF 文件路径错误或格式不兼容              | 确认 GGUF 文件完整性，检查 Modelfile 中的 `FROM` 路径是否正确 |
| Open WebUI 连接 Ollama 失败      | Docker 容器无法访问宿主机的 localhost      | 使用 `--add-host=host.docker.internal:host-gateway` 参数，或设置 `OLLAMA_HOST=0.0.0.0` |



<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>大模型应用技术栈分层与本课程定位</font></p>
<div class="center">

| 层级       | 技术内容                       | 代表工具/框架                 | 本课程覆盖 |
| ---------- | ------------------------------ | ----------------------------- | ---------- |
| **模型层** | 模型选型、权重下载、格式理解   | Hugging Face、ModelScope      | ✅ 第1-3章  |
| **量化层** | 模型压缩、精度-性能权衡        | llama.cpp、GPTQ、AWQ          | ✅ 第7-8章  |
| **服务层** | 推理引擎部署、API 服务         | Ollama、vLLM、TGI             | ✅ 第9章    |
| **编排层** | 链式调用、Agent 编排、工具集成 | LangChain、LangGraph、CrewAI  | 🔜 后续课程 |
| **检索层** | 向量存储、文档切分、相似度检索 | FAISS、Chroma、Milvus         | 🔜 RAG 课程 |
| **应用层** | 前端界面、用户交互、产品化     | Open WebUI、Gradio、Streamlit | 🔜 后续课程 |

&emsp;&emsp;从表中可以看到，本课程覆盖了底部三层（模型层 → 量化层 → 服务层），这是整个技术栈的地基。<font color=red>没有稳定的推理服务，上层的 RAG、Agent、前端应用都无从谈起</font>。接下来的学习路径建议是：先掌握 RAG（检索增强生成），再进入 Agent 开发，最后根据业务需求选择前端框架进行产品化。





<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>大模型本地部署核心术语对照表</font></p>
<div class="center">

| 术语                                           | 定义                                                         | 本课程应用场景                                       |
| ---------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| **safetensors**                                | Hugging Face 推出的安全高效模型权重存储格式，支持内存映射加载，避免了 pickle 反序列化的安全风险 | vLLM 加载模型时读取的主要权重格式（第3、9章）        |
| **GGUF** (GPT-Generated Unified Format)        | llama.cpp 生态的统一模型格式，支持多种量化等级，单文件包含权重+元数据 | Ollama 底层使用的模型格式（第8、9章）                |
| **量化** (Quantization)                        | 将模型权重从高精度（FP32/FP16）转换为低精度（INT8/INT4）的技术，以减少显存占用和加速推理 | Ollama 默认 Q4_K_M，vLLM 支持 AWQ/GPTQ（第7章）      |
| **Q4_K_M**                                     | GGUF 格式中的一种 4-bit 量化方案，在精度和压缩率之间取得较好平衡 | Ollama 默认下载的量化等级（第7、9章）                |
| **AWQ** (Activation-aware Weight Quantization) | 基于激活值分布的权重量化方法，在 4-bit 量化下保持较高精度    | vLLM 支持的量化格式之一（第8章）                     |
| **GPTQ** (GPT Quantization)                    | 基于二阶信息的逐层量化方法，是最早广泛使用的 LLM 量化技术之一 | vLLM 支持的量化格式之一（第8章）                     |
| **KV Cache**                                   | 推理过程中缓存已计算的 Key-Value 向量，避免重复计算，是自回归生成的核心加速机制 | vLLM 的 PagedAttention 优化的核心对象（第9章）       |
| **PagedAttention**                             | vLLM 的核心技术，借鉴操作系统虚拟内存的分页机制管理 KV Cache，大幅提升显存利用率 | vLLM 高吞吐量的技术基础（第9章）                     |
| **Continuous Batching**                        | 连续批处理技术，允许新请求在不等待当前批次完成的情况下加入推理队列 | vLLM 高并发能力的关键机制（第9章）                   |
| **Tensor Parallel**                            | 张量并行，将模型的权重矩阵切分到多张 GPU 上并行计算          | vLLM `--tensor-parallel-size` 参数（第9章）          |
| **Modelfile**                                  | Ollama 的模型配置文件，用于定义模型来源、系统提示词、参数等  | 导入自定义 GGUF 模型到 Ollama（第9章）               |
| **OpenAI API 兼容**                            | 指服务端实现了与 OpenAI API 相同的接口协议（`/v1/chat/completions` 等） | Ollama 和 vLLM 都支持，客户端代码可通用（第9、10章） |



### Agent 发展趋势

**从 Prompt 到 Agent**

<style>
.center {
width: auto;
display: table;
margin-left: auto;
margin-right: auto;
}
</style>
<p align="center"><font face="黑体" size=4>大模型应用技术演进四阶段</font></p>
<div class="center">

| 阶段    | 时间      | 核心技术                       | 解决的问题           | 遗留的问题         |
| ------- | --------- | ------------------------------ | -------------------- | ------------------ |
| Stage 1 | 2023.Q1   | 提示工程（Prompt Engineering） | 如何让 LLM 理解任务  | 知识库更新不及时   |
| Stage 2 | 2023.Q3   | 函数调用（Function Calling）   | 如何让 LLM 调用工具  | 大模型幻觉问题     |
| Stage 3 | 2023.Q4   | RAG（检索增强生成）            | 如何注入私有知识     | 只能单步问答       |
| Stage 4 | 2024-2026 | AI Agent（智能体）             | 如何自主完成复杂任务 | 可靠性、成本、安全 |

&emsp;&emsp;**Stage 1：提示工程（Prompt Engineering）**

&emsp;&emsp;2020 年，OpenAI 在 GPT-3 论文中提出了 `In-Context Learning`（上下文学习）的概念。这个发现开启了使用大模型的新方式：通过向模型提供少量标注的"输入-输出对"示例（Few-Shot Learning），在不需要大规模微调的情况下即可显著改善大模型的输出质量。

> 📄 **论文链接**：[Language Models are Few-Shot Learners](https://arxiv.org/pdf/2005.14165)

&emsp;&emsp;这一阶段解决了"如何让 LLM 理解任务"的问题，但遗留了知识库更新不及时的痛点——LLM 的训练数据有截止日期，无法获取实时信息。

&emsp;&emsp;**Stage 2：函数调用（Function Calling）**

&emsp;&emsp;2023 年 6 月，OpenAI 为其 GPT 模型引入了函数调用功能。通过函数调用，我们可以让 LLM 智能地选择工具来回答问题，并以 JSON 格式返回结构化响应。这解决了"如何让 LLM 调用工具"的问题，但大模型幻觉问题依然存在。

&emsp;&emsp;**Stage 3：RAG（Retrieval-Augmented Generation）**

&emsp;&emsp;RAG 通过"检索 + 生成"的方式缓解了幻觉问题：先从知识库中检索相关文档，再让 LLM 基于检索结果生成答案。这在很大程度上约束了 LLM 的输出范围。但传统单轮 RAG pipeline 有一个根本局限：它是"单步"的——用户提问 → 检索一次 → 生成答案，无法处理需要多步推理、多次检索、动态调整策略的复杂任务。

&emsp;&emsp;**Stage 4：AI Agent（智能体）**

&emsp;&emsp;Agent 整合了前三个阶段的能力：利用提示工程激发涌现能力、通过函数调用使用工具、借助 RAG 注入知识，并在此基础上实现了多步迭代、动态规划、自主决策。<font color=red>这就是为什么我们说"提示工程解决了理解问题，函数调用解决了行动问题，RAG 解决了知识问题，Agent 解决了能力问题"。</font>

&emsp;&emsp;从这个演进表可以看出，Agent 不是凭空出现的，而是在前三个阶段的基础上自然演化出来的。理解了这条技术演进脉络，我们才能更深刻地理解 Agent 的价值所在。
