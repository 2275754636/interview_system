#!/usr/bin/env python3
# coding: utf-8
"""
API客户端模块 - 大学生五育并举访谈智能体
支持多种大模型API：DeepSeek、OpenAI、通义千问、智谱AI、百度千帆
统一适配层设计
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, List

import logger
from config import BASE_DIR


# ----------------------------
# API 配置文件路径
# ----------------------------
API_CONFIG_FILE = os.path.join(BASE_DIR, "api_config.json")


# ----------------------------
# API 提供商配置
# ----------------------------
@dataclass
class APIProviderConfig:
    """API提供商配置"""
    name: str                    # 显示名称
    provider_id: str             # 提供商ID
    base_url: str                # API 基础URL
    default_model: str           # 默认模型
    api_key_name: str            # API Key 的名称（用于提示用户）
    need_secret_key: bool = False  # 是否需要 Secret Key（百度千帆需要）
    models: List[str] = None     # 可用模型列表
    website: str = ""            # 官网地址（获取API Key）


# 支持的 API 提供商列表
API_PROVIDERS: Dict[str, APIProviderConfig] = {
    "deepseek": APIProviderConfig(
        name="DeepSeek (深度求索)",
        provider_id="deepseek",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        api_key_name="API Key",
        models=["deepseek-chat"],  # 仅支持 chat 模型，R1 推理模型不适合对话场景
        website="https://platform.deepseek.com/"
    ),
    "openai": APIProviderConfig(
        name="OpenAI (ChatGPT)",
        provider_id="openai",
        base_url="https://api.openai.com/v1",
        default_model="gpt-3.5-turbo",
        api_key_name="API Key",
        models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
        website="https://platform.openai.com/"
    ),
    "qwen": APIProviderConfig(
        name="通义千问 (阿里)",
        provider_id="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-turbo",
        api_key_name="API Key",
        models=["qwen-turbo", "qwen-plus", "qwen-max"],
        website="https://dashscope.console.aliyun.com/"
    ),
    "zhipu": APIProviderConfig(
        name="智谱AI (GLM)",
        provider_id="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4-flash",
        api_key_name="API Key",
        models=["glm-4-flash", "glm-4-air", "glm-4"],
        website="https://open.bigmodel.cn/"
    ),
    "baidu": APIProviderConfig(
        name="百度千帆 (文心一言)",
        provider_id="baidu",
        base_url="https://qianfan.baidubce.com/v2",
        default_model="ernie-3.5-8k",
        api_key_name="Access Key",
        need_secret_key=True,
        models=["ernie-3.5-8k", "ernie-4.0-8k", "ernie-speed-8k"],
        website="https://qianfan.baidubce.com/"
    ),
}


class UnifiedAPIClient:
    """统一 API 客户端 - 支持多种大模型API"""
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self.current_provider: Optional[APIProviderConfig] = None
        self.api_key: Optional[str] = None
        self.secret_key: Optional[str] = None  # 百度千帆专用
        self.model: Optional[str] = None
        self.timeout: int = 15
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        self._lazy_initialized = False  # 标记是否已延迟初始化
        
        # 尝试加载已保存的配置（不验证）
        self._load_config()
    
    def _load_config(self) -> bool:
        """从本地文件加载API配置（不进行网络验证）"""
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
        """
        延迟初始化客户端（首次使用时调用）
        不进行测试调用，直接创建客户端
        """
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
            self._lazy_initialized = True  # 标记已尝试
            return False
    
    def save_config(self) -> bool:
        """保存API配置到本地文件"""
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
            
            # 百度千帆需要保存 secret_key
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
        """清除保存的配置"""
        if os.path.exists(API_CONFIG_FILE):
            os.remove(API_CONFIG_FILE)
            logger.info("已清除API配置")
    
    def get_saved_provider(self) -> Optional[str]:
        """获取已保存的提供商ID"""
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
        """
        初始化API客户端
        
        Args:
            provider_id: 提供商ID
            api_key: API Key
            secret_key: Secret Key（百度千帆专用）
            model: 模型名称（可选）
            
        Returns:
            是否初始化成功
        """
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
            # 根据不同提供商配置客户端
            client_kwargs = {
                "api_key": api_key,
                "base_url": provider.base_url,
                "timeout": self.timeout,
            }
            
            # 百度千帆需要特殊的 header
            if provider_id == "baidu":
                client_kwargs["default_headers"] = {"X-Bce-Signature-Key": secret_key}
            
            self.client = openai.OpenAI(**client_kwargs)
            
            # 测试连接（轻量调用）
            test_model = model or provider.default_model
            self.client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            
            # 配置成功
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
            
            # 配置失败时清除无效配置
            self.clear_config()
            return False
    
    def generate_followup(
        self, 
        answer: str, 
        topic: dict, 
        conversation_log: list = None
    ) -> Optional[str]:
        """
        生成智能追问
        
        Args:
            answer: 用户回答
            topic: 当前话题
            conversation_log: 对话记录（可选）
            
        Returns:
            生成的追问问题，失败返回 None
        """
        # 延迟初始化客户端
        if not self.is_available and not self._lazy_initialized:
            self._lazy_init_client()
        
        if not self.is_available or not self.client:
            return None
        
        valid_answer = answer.strip()
        if len(valid_answer) < 2:
            return None
        
        topic_name = topic.get("name", "")
        scene, edu_type = topic_name.split("-") if "-" in topic_name else ("", "")
        original_question = topic.get("questions", [""])[0]
        
        # 构建完整对话历史（用于上下文理解）
        history_context = ""
        if conversation_log:
            # 只获取当前话题的对话记录
            topic_logs = [log for log in conversation_log if log.get("topic") == topic_name]
            if topic_logs:
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
                    history_context = "\n\n【对话历史】\n" + "\n\n".join(history_parts)
        
        # 根据五育维度设置不同的语气风格
        tone_guide = self._get_tone_by_edu_type(edu_type)
        
        # 正式访谈风格的prompt - 记者采访风格 + 紧扣五育主题
        prompt = f"""你是一位专业的访谈记者，正在对大学生进行关于"五育并举"主题的深度访谈。

【访谈主题】{edu_type}（{scene}场景）
【核心问题】{original_question}
{history_context}

【受访者最新回答】
{valid_answer}

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
        
        return self._call_with_retry(prompt, topic)
    
    def _get_tone_by_edu_type(self, edu_type: str) -> str:
        """
        根据五育维度返回对应的语气风格指导（正式访谈风格）
        
        Args:
            edu_type: 五育维度（德育、智育、体育、美育、劳育）
            
        Returns:
            语气风格指导文本
        """
        tone_map = {
            "德育": "正式而有深度，关注价值观和道德判断。示例：'您认为这个经历对您的价值观产生了怎样的影响？'",
            "智育": "理性而专业，关注学习过程和思维发展。示例：'这种学习方法对您的思维能力有什么具体帮助？'",
            "体育": "务实而积极，关注身体素质和运动习惯。示例：'坚持这项运动对您的身心状态有什么改变？'",
            "美育": "细腻而有感染力，关注审美体验和艺术感悟。示例：'这次艺术体验让您对美有了什么新的认识？'",
            "劳育": "朴实而真诚，关注实践能力和劳动价值。示例：'这次劳动经历让您对动手实践有了什么新的理解？'"
        }
        return tone_map.get(edu_type, "专业而亲和，像记者采访一样")
    
    def _call_with_retry(self, prompt: str, topic: dict) -> Optional[str]:
        """
        带重试机制的API调用
        
        Args:
            prompt: 提示词
            topic: 当前话题
            
        Returns:
            生成的追问问题，失败返回 None
        """
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
                    max_tokens=120,
                    temperature=0.7,
                    n=1
                )
                
                duration = time.time() - start_time
                
                if response and response.choices:
                    choice = response.choices[0]
                    
                    # DeepSeek R1 (reasoner) 模型的输出在 message.content 中
                    # 但有时需要检查 reasoning_content（思考过程）和 content（最终答案）
                    follow_question = ""
                    
                    if hasattr(choice, 'message') and choice.message:
                        # 优先使用 content（最终答案）
                        if hasattr(choice.message, 'content') and choice.message.content:
                            follow_question = choice.message.content.strip()
                        
                        # 如果 content 为空，检查是否有 reasoning_content（DeepSeek R1）
                        if not follow_question and hasattr(choice.message, 'reasoning_content'):
                            reasoning = choice.message.reasoning_content
                            if reasoning:
                                # 从推理内容中提取最后的结论
                                lines = reasoning.strip().split('\n')
                                # 取最后几行非空内容作为追问
                                for line in reversed(lines):
                                    line = line.strip()
                                    if line and len(line) >= 5 and not line.startswith(('<', '【', '```')):
                                        follow_question = line
                                        break
                    
                    if not follow_question:
                        logger.log_api_call("generate_followup", True, duration, "API返回内容为空")
                        return None
                    
                    # 清理可能的前缀和格式
                    prefixes_to_remove = ["追问：", "追问:", "问：", "问:", "**追问**：", "**追问**:"]
                    for prefix in prefixes_to_remove:
                        if follow_question.startswith(prefix):
                            follow_question = follow_question[len(prefix):].strip()
                    
                    # 移除可能的引号包裹
                    if follow_question.startswith('"') and follow_question.endswith('"'):
                        follow_question = follow_question[1:-1].strip()
                    if follow_question.startswith('"') and follow_question.endswith('"'):
                        follow_question = follow_question[1:-1].strip()
                    
                    # 校验追问质量
                    preset_follows = topic.get("followups", [])
                    original_question = topic.get("questions", [""])[0]
                    
                    if (follow_question
                            and len(follow_question) >= 5  # 最小长度
                            and follow_question not in original_question
                            and follow_question not in preset_follows):
                        logger.log_api_call("generate_followup", True, duration)
                        logger.debug(f"AI生成追问成功: {follow_question}")
                        return follow_question
                    
                    logger.log_api_call("generate_followup", True, duration, f"生成内容不符合要求: {follow_question[:50]}")
                    return None
                
                logger.log_api_call("generate_followup", True, duration, "API响应无choices")
                return None
                
            except Exception as e:
                duration = time.time() - start_time
                last_error = str(e)
                logger.log_api_call(
                    "generate_followup", 
                    False, 
                    duration, 
                    f"第{attempt + 1}次尝试失败: {last_error[:50]}"
                )
                
                # 如果还有重试机会，等待后重试
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.debug(f"等待 {wait_time:.1f}s 后重试...")
                    time.sleep(wait_time)
        
        logger.error(f"API调用失败，已重试{self.max_retries}次: {last_error}")
        return None


# ----------------------------
# 全局API客户端实例
# ----------------------------
_api_client: Optional[UnifiedAPIClient] = None


def get_api_client() -> UnifiedAPIClient:
    """获取全局API客户端实例"""
    global _api_client
    if _api_client is None:
        _api_client = UnifiedAPIClient()
    return _api_client


def get_available_providers() -> Dict[str, APIProviderConfig]:
    """获取所有可用的API提供商"""
    return API_PROVIDERS


def initialize_api(
    provider_id: str, 
    api_key: str, 
    secret_key: str = None,
    model: str = None
) -> bool:
    """初始化全局API客户端"""
    return get_api_client().initialize(provider_id, api_key, secret_key, model)


def generate_followup(answer: str, topic: dict, conversation_log: list = None) -> Optional[str]:
    """生成智能追问（便捷函数）"""
    return get_api_client().generate_followup(answer, topic, conversation_log)


def is_api_available() -> bool:
    """检查API是否可用"""
    return get_api_client().is_available


def get_current_provider_name() -> str:
    """获取当前使用的API提供商名称"""
    client = get_api_client()
    if client.current_provider:
        return client.current_provider.name
    return "未配置"
