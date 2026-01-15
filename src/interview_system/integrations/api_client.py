#!/usr/bin/env python3
# coding: utf-8
"""
Unified API Client - Multi-provider LLM support
"""

import json
import os
import time
from typing import Optional

import interview_system.common.logger as logger
from interview_system.common.config import BASE_DIR
from interview_system.integrations.api_providers import API_PROVIDERS, APIProviderConfig

API_CONFIG_FILE = os.path.join(BASE_DIR, "api_config.json")

# Token limits
MAX_FOLLOWUP_TOKENS = 120
TEST_CALL_TOKENS = 5


class UnifiedAPIClient:
    """统一 API 客户端"""

    def __init__(self):
        self.client = None
        self.is_available = False
        self.current_provider: Optional[APIProviderConfig] = None
        self.api_key: Optional[str] = None
        self.secret_key: Optional[str] = None
        self.model: Optional[str] = None
        self.timeout: int = 15
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        self._lazy_initialized = False
        self._load_config()

    def _load_config(self) -> bool:
        """Load API config from file (no network validation)"""
        if not os.path.exists(API_CONFIG_FILE):
            return False

        try:
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            provider_id = data.get("provider_id")
            if provider_id and provider_id in API_PROVIDERS:
                self.current_provider = API_PROVIDERS[provider_id]
                self.api_key = data.get("api_key")
                self.secret_key = data.get("secret_key")
                self.model = data.get("model") or self.current_provider.default_model
                logger.info(f"已加载API配置：{self.current_provider.name}")
                return True
        except Exception as e:
            logger.warning(f"加载API配置失败：{e}")

        return False

    def _lazy_init_client(self) -> bool:
        """Lazy init client on first use"""
        if self._lazy_initialized:
            return self.is_available

        if not self.current_provider or not self.api_key:
            return False

        try:
            import openai

            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.current_provider.base_url,
                "timeout": self.timeout,
            }

            if self.current_provider.provider_id == "baidu" and self.secret_key:
                client_kwargs["default_headers"] = {"X-Bce-Signature-Key": self.secret_key}

            self.client = openai.OpenAI(**client_kwargs)
            self.is_available = True
            self._lazy_initialized = True
            logger.info(f"延迟初始化API客户端成功：{self.current_provider.name}")
            return True

        except Exception as e:
            logger.warning(f"延迟初始化API客户端失败：{e}")
            self._lazy_initialized = True
            return False

    def save_config(self) -> bool:
        """Save API config to file"""
        if not self.current_provider or not self.api_key:
            return False

        try:
            import datetime
            data = {
                "provider_id": self.current_provider.provider_id,
                "api_key": self.api_key,
                "model": self.model,
                "saved_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if self.current_provider.need_secret_key and self.secret_key:
                data["secret_key"] = self.secret_key

            with open(API_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"API配置已保存到：{API_CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"保存API配置失败：{e}")
            return False

    def clear_config(self):
        """Clear saved config"""
        if os.path.exists(API_CONFIG_FILE):
            os.remove(API_CONFIG_FILE)
            logger.info("已清除API配置")

    def get_saved_provider(self) -> Optional[str]:
        """Get saved provider ID"""
        if self.current_provider:
            return self.current_provider.provider_id
        return None

    def initialize(
        self,
        provider_id: str,
        api_key: str,
        secret_key: str = None,
        model: str = None
    ) -> bool:
        """Initialize API client with credentials"""
        if provider_id not in API_PROVIDERS:
            logger.error(f"不支持的API提供商：{provider_id}")
            return False

        try:
            import openai
        except ImportError:
            logger.error("未安装 openai 库，请运行 `pip install openai>=1.0.0` 安装")
            return False

        provider = API_PROVIDERS[provider_id]

        if not api_key:
            logger.warning("API Key 不能为空")
            return False

        if provider.need_secret_key and not secret_key:
            logger.warning(f"{provider.name} 需要 Secret Key")
            return False

        try:
            client_kwargs = {
                "api_key": api_key,
                "base_url": provider.base_url,
                "timeout": self.timeout,
            }

            if provider_id == "baidu":
                client_kwargs["default_headers"] = {"X-Bce-Signature-Key": secret_key}

            self.client = openai.OpenAI(**client_kwargs)

            test_model = model or provider.default_model
            self.client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=TEST_CALL_TOKENS
            )

            self.current_provider = provider
            self.api_key = api_key
            self.secret_key = secret_key
            self.model = model or provider.default_model
            self.is_available = True

            logger.info(f"{provider.name} 智能追问功能已启用，模型：{self.model}")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"{provider.name} 配置失败：{error_msg}")
            self.is_available = False
            self.clear_config()
            return False

    def generate_followup(
        self,
        answer: str,
        topic: dict,
        conversation_log: list = None
    ) -> Optional[str]:
        """Generate intelligent followup question"""
        if not self.is_available and not self._lazy_initialized:
            self._lazy_init_client()

        if not self.is_available or not self.client:
            return None

        valid_answer = answer.strip()
        if len(valid_answer) < 2:
            return None

        prompt = self._build_followup_prompt(valid_answer, topic, conversation_log)
        return self._call_with_retry(prompt, topic)

    def _build_followup_prompt(
        self,
        answer: str,
        topic: dict,
        conversation_log: list = None
    ) -> str:
        """Build prompt for followup generation"""
        topic_name = topic.get("name", "")
        scene, edu_type = topic_name.split("-") if "-" in topic_name else ("", "")
        original_question = topic.get("questions", [""])[0]

        history_context = self._build_history_context(conversation_log, topic_name)
        tone_guide = self._get_tone_by_edu_type(edu_type)

        return f"""你是一位专业的访谈记者，正在对大学生进行关于"五育并举"主题的深度访谈。

【访谈主题】{edu_type}（{scene}场景）
【核心问题】{original_question}
{history_context}

【受访者最新回答】
{answer}

【追问要求】
你的追问必须围绕上述【核心问题】展开，紧扣"{edu_type}"主题，从以下角度深入（选择最合适的一个）：

1. 与{edu_type}的关联：这个经历如何体现或影响了{edu_type}方面的发展？
2. 原因与动机：是什么促使做出这个选择或采取这个行动？
3. 影响与改变：这个经历带来了什么收获或改变？

【语气风格】
{tone_guide}

【重要规范】
- 追问必须与【核心问题】相关，不要偏离主题
- 参考【对话历史】避免重复已经问过的内容
- 如果受访者回答偏题，温和地引导回{edu_type}主题
- 每次只问一个具体问题，不要空泛地说"能具体说说吗"
- 采用记者采访的专业风格，正式但亲和

直接输出追问问题，不要任何前缀或解释。"""

    def _build_history_context(self, conversation_log: list, topic_name: str) -> str:
        """Build conversation history context"""
        if not conversation_log:
            return ""

        topic_logs = [log for log in conversation_log if log.get("topic") == topic_name]
        if not topic_logs:
            return ""

        history_parts = []
        for log in topic_logs:
            q_type = log.get("question_type", "")
            q_text = log.get("question", "")
            ans = log.get("answer", "")

            if "核心" in q_type:
                history_parts.append(f"【核心问题】{q_text}\n【回答】{ans}")
            elif "追问" in q_type:
                history_parts.append(f"【追问{len(history_parts)}】{q_text}\n【回答】{ans}")

        if history_parts:
            return "\n\n【对话历史】\n" + "\n\n".join(history_parts)
        return ""

    def _get_tone_by_edu_type(self, edu_type: str) -> str:
        """Get tone guide by education type"""
        tone_map = {
            "德育": "正式而有深度，关注价值观和道德判断。示例：'您认为这个经历对您的价值观产生了怎样的影响？'",
            "智育": "理性而专业，关注学习过程和思维发展。示例：'这种学习方法对您的思维能力有什么具体帮助？'",
            "体育": "务实而积极，关注身体素质和运动习惯。示例：'坚持这项运动对您的身心状态有什么改变？'",
            "美育": "细腻而有感染力，关注审美体验和艺术感悟。示例：'这次艺术体验让您对美有了什么新的认识？'",
            "劳育": "朴实而真诚，关注实践能力和劳动价值。示例：'这次劳动经历让您对动手实践有了什么新的理解？'"
        }
        return tone_map.get(edu_type, "专业而亲和，像记者采访一样")

    def _call_with_retry(self, prompt: str, topic: dict) -> Optional[str]:
        """API call with retry mechanism"""
        last_error = None

        for attempt in range(self.max_retries):
            start_time = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的访谈记者，正在进行大学生五育发展主题访谈。你的追问要紧扣访谈主题，专业而有深度。只输出追问问题本身，不要有任何前缀、解释或多余内容。"},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    max_tokens=MAX_FOLLOWUP_TOKENS,
                    temperature=0.7,
                    n=1
                )

                duration = time.time() - start_time
                return self._extract_followup(response, topic, duration)

            except Exception as e:
                duration = time.time() - start_time
                last_error = str(e)
                logger.log_api_call(
                    "generate_followup",
                    False,
                    duration,
                    f"第{attempt + 1}次尝试失败: {last_error[:50]}"
                )

                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.debug(f"等待 {wait_time:.1f}s 后重试...")
                    time.sleep(wait_time)

        logger.error(f"API调用失败，已重试{self.max_retries}次: {last_error}")
        return None

    def _extract_followup(self, response, topic: dict, duration: float) -> Optional[str]:
        """Extract followup question from API response"""
        if not response or not response.choices:
            logger.log_api_call("generate_followup", True, duration, "API响应无choices")
            return None

        choice = response.choices[0]
        follow_question = ""

        if hasattr(choice, 'message') and choice.message:
            if hasattr(choice.message, 'content') and choice.message.content:
                follow_question = choice.message.content.strip()

            if not follow_question and hasattr(choice.message, 'reasoning_content'):
                follow_question = self._extract_from_reasoning(choice.message.reasoning_content)

        if not follow_question:
            logger.log_api_call("generate_followup", True, duration, "API返回内容为空")
            return None

        follow_question = self._clean_followup(follow_question)

        if not self._validate_followup(follow_question, topic):
            logger.log_api_call("generate_followup", True, duration, f"生成内容不符合要求: {follow_question[:50]}")
            return None

        logger.log_api_call("generate_followup", True, duration)
        logger.debug(f"AI生成追问成功: {follow_question}")
        return follow_question

    def _extract_from_reasoning(self, reasoning: str) -> str:
        """Extract conclusion from reasoning content (DeepSeek R1)"""
        if not reasoning:
            return ""
        lines = reasoning.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) >= 5 and not line.startswith(('<', '【', '```')):
                return line
        return ""

    def _clean_followup(self, text: str) -> str:
        """Clean followup text"""
        prefixes = ["追问：", "追问:", "问：", "问:", "**追问**：", "**追问**:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()

        return text

    def _validate_followup(self, followup: str, topic: dict) -> bool:
        """Validate followup quality"""
        if not followup or len(followup) < 5:
            return False

        preset_follows = topic.get("followups", [])
        original_question = topic.get("questions", [""])[0]

        return followup not in original_question and followup not in preset_follows
