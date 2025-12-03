# 🎓 大学生五育并举访谈智能体

基于多种大模型API的智能访谈系统，支持多人同时在线访谈。

## ✨ 特性

- 🤖 **智能追问**：支持多种大模型API（DeepSeek、OpenAI、通义千问、智谱AI、百度千帆），根据回答内容生成针对性追问
- 🔄 **API重试机制**：自动重试失败的API调用，支持指数退避策略
- 👥 **多人同时访谈**：支持多用户同时进行访谈，会话隔离
- 📱 **双模式支持**：命令行交互 + Web扫码访问
- 📝 **日志系统**：统一的日志输出，支持文件和控制台
- 💾 **自动导出**：访谈结束时自动保存JSON日志

## 📁 项目结构

```
interview_system/
├── __init__.py          # 包初始化文件
├── config.py            # 配置文件（系统参数）
├── questions.py         # 题目配置（15个访谈话题：3场景×5育）
├── logger.py            # 统一日志模块
├── api_client.py        # 统一API客户端（支持多种大模型）
├── session_manager.py   # 会话管理（支持多人同时访谈）
├── interview_engine.py  # 访谈核心引擎（追问逻辑、评分）
├── web_server.py        # Web服务模块（Gradio界面）
├── main.py              # 主入口文件
├── requirements.txt     # 依赖列表
├── api_config.json      # API配置（自动生成）
├── exports/             # 导出的访谈记录
└── logs/                # 日志文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd interview_system
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 选择模式

- 输入 `1`：命令行交互模式
- 输入 `2`（默认）：Web扫码版，支持手机访问

## 🔧 配置说明

### 支持的 API 提供商

| 提供商 | 默认模型 | 获取API Key |
|--------|----------|-------------|
| **DeepSeek** | deepseek-chat | [platform.deepseek.com](https://platform.deepseek.com/) |
| **OpenAI** | gpt-3.5-turbo | [platform.openai.com](https://platform.openai.com/) |
| **通义千问** | qwen-turbo | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) |
| **智谱AI** | glm-4-flash | [open.bigmodel.cn](https://open.bigmodel.cn/) |
| **百度千帆** | ernie-3.5-8k | [qianfan.baidubce.com](https://qianfan.baidubce.com/) |

### API配置流程

首次运行时，程序会引导你选择API提供商并输入密钥：

```
===== 智能追问 API 配置 =====

支持的 API 提供商：
--------------------------------------------------
  1. DeepSeek (深度求索)
  2. OpenAI (ChatGPT)
  3. 通义千问 (阿里)
  4. 智谱AI (GLM)
  5. 百度千帆 (文心一言)
  0. 跳过配置（使用预设追问）
--------------------------------------------------

请选择 API 提供商 [0-5]:
```

配置成功后会自动保存到 `api_config.json`，下次启动无需重复输入。

### 修改配置参数

编辑 `config.py` 可调整：

```python
# 访谈配置
INTERVIEW_CONFIG = InterviewConfig(
    total_questions=6,          # 每次访谈题目数
    min_answer_length=30,       # 触发追问的最小回答长度
    max_depth_score=3           # 回答深度最高分
)

# Web服务配置
WEB_CONFIG = WebConfig(
    port=7860,                  # 服务端口
    share=True,                 # 是否生成公网链接
    max_sessions=100            # 最大同时会话数
)
```

## 📋 访谈规则

- **题目数量**：每次随机抽取 6 题
- **覆盖要求**：确保覆盖学校、家庭、社区三场景 + 德、智、体、美、劳五育
- **追问机制**：
  - 回答过短（<30字）或跑题：自动追问
  - 回答深度不足：尝试AI智能追问
  - 回答详细且有深度：直接进入下一题

## 💡 使用指令

### 命令行模式

| 指令 | 说明 |
|------|------|
| `跳过` | 跳过当前问题 |
| `导出` | 导出当前访谈日志 |
| `结束` | 结束访谈 |

### Web模式

| 操作 | 说明 |
|------|------|
| 「⏭️ 跳过」按钮 | 跳过当前问题 |
| 「🔄 开始新访谈」按钮 | 重新开始一次访谈 |

> 注：Web模式下访谈结束会自动导出日志到 `exports/` 目录

## 📊 导出格式

访谈记录导出为 JSON 格式，包含：

```json
{
  "session_id": "abc12345",
  "user_name": "访谈者",
  "start_time": "2025-12-03 10:00:00",
  "end_time": "2025-12-03 10:30:00",
  "statistics": {
    "total_logs": 8,
    "scene_distribution": {"学校": 3, "家庭": 2, "社区": 3},
    "edu_distribution": {"德育": 2, "智育": 1, ...},
    "followup_distribution": {"预设追问": 1, "AI智能追问": 2}
  },
  "conversation_log": [
    {
      "timestamp": "2025-12-03 10:05:00",
      "topic": "学校-德育",
      "question_type": "核心问题",
      "question": "你认为自己在大学里学习到的最重要的品德是什么？",
      "answer": "...",
      "depth_score": 2
    }
  ]
}
```

## 🛠️ 开发说明

### 模块依赖关系

```
main.py
  ├── config.py (配置)
  ├── logger.py (日志)
  ├── api_client.py (统一API调用)
  ├── session_manager.py (会话管理)
  │     └── config.py
  ├── interview_engine.py (访谈引擎)
  │     ├── config.py
  │     ├── questions.py
  │     ├── api_client.py
  │     └── session_manager.py
  └── web_server.py (Web服务)
        ├── config.py
        ├── session_manager.py
        └── interview_engine.py
```

### 添加新的API提供商

编辑 `api_client.py`，在 `API_PROVIDERS` 字典中添加：

```python
"new_provider": APIProviderConfig(
    name="新提供商名称",
    provider_id="new_provider",
    base_url="https://api.example.com/v1",  # OpenAI兼容格式
    default_model="model-name",
    api_key_name="API Key",
    models=["model-1", "model-2"],
    website="https://example.com/"
)
```

> 注：大多数国产API都兼容OpenAI接口格式，只需修改 base_url 和模型名称即可。

### 扩展题目

编辑 `questions.py`，按以下格式添加话题：

```python
{
    "name": "场景-育类型",       # 如 "学校-德育"
    "scene": "场景",            # 学校/家庭/社区
    "edu_type": "育类型",       # 德育/智育/体育/美育/劳育
    "intro": "话题介绍",
    "questions": ["核心问题"],
    "scenarios": [],            # 情景（可选）
    "followups": ["预设追问1", "预设追问2"]
}
```

## 📄 License

MIT License

