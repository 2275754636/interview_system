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
        models=["deepseek-chat", "deepseek-reasoner"],
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
            recent_logs = [log for log in conversation_log[-8:] if log.get("topic") == topic_name]
            if recent_logs:
                history_parts = []
                for i, log in enumerate(recent_logs):
                    q_type = log.get("question_type", "")
                    q_text = log.get("question", "")
                    ans = log.get("answer", "")
                    if "核心" in q_type:
                        history_parts.append(f"[第{i+1}轮] 问：{q_text}\n答：{ans}")
                    elif "追问" in q_type:
                        history_parts.append(f"[第{i+1}轮-追问] 问：{q_text}\n答：{ans}")
                if history_parts:
                    history_context = "\n\n对话历史：\n" + "\n\n".join(history_parts)
        
        # 根据五育维度设置不同的语气风格
        tone_guide = self._get_tone_by_edu_type(edu_type)
        
        # 优化后的prompt - 混合过渡语风格 + 话题自适应语气
        prompt = f"""你是一位善于倾听的访谈员，正在和大学生进行轻松的访谈对话。

【当前话题】{topic_name}
【场景】{scene}
【维度】{edu_type}
【原始问题】{original_question}

【用户刚才说】
{valid_answer}
{history_context}

【生成追问的要求】
1. 语气风格：{tone_guide}

2. 过渡语风格（混合使用，随机选一种）：
   - 引用式："你提到XXX，" / "刚才说的XXX挺有意思，"
   - 共情式："听起来..." / "感觉你对这个..."
   - 简洁式：直接追问，不加过渡语

3. 追问内容方向（选择最合适的一个）：
   - 追问具体细节：什么时候、在哪里、和谁一起、怎么做的
   - 追问内心感受：当时心情、现在回想的感觉
   - 追问影响变化：后来怎样了、有什么改变、学到什么
   - 追问他人反应：别人怎么看、有没有得到反馈

4. 禁止事项：
   - 不要使用"能具体说说吗""能展开讲讲吗"这类空泛表述
   - 不要重复用户已经详细说过的内容
   - 不要一次问多个问题
   - 不要太正式或太书面化

直接输出追问内容（一句话），不要任何前缀、解释或引号。"""
        
        return self._call_with_retry(prompt, topic)
    
    def _get_tone_by_edu_type(self, edu_type: str) -> str:
        """
        根据五育维度返回对应的语气风格指导
        
        Args:
            edu_type: 五育维度（德育、智育、体育、美育、劳育）
            
        Returns:
            语气风格指导文本
        """
        tone_map = {
            "德育": "温和认真，像在聊人生道理和价值观，可以稍微正式一点。示例语气：'这个选择背后是怎么想的呢？'",
            "智育": "好奇探索，像在讨论学习方法和知识，带点求知的热情。示例语气：'哇这个方法听起来不错，效果咋样？'",
            "体育": "活泼轻松，像在聊运动和健康，可以更随意一些。示例语气：'那场比赛紧张不？'",
            "美育": "感性细腻，像在聊艺术和美的体验，注重感受的表达。示例语气：'当时是什么触动了你？'",
            "劳育": "朴实接地气，像在聊日常生活和动手经历，很生活化。示例语气：'累不累？值不值？'"
        }
        return tone_map.get(edu_type, "自然随和，像朋友聊天一样")
    
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
                        {"role": "system", "content": "你是一位友善的访谈员，擅长通过追问引导对方分享更多细节和感受。只输出追问内容，不要有任何前缀。"},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    max_tokens=100,
                    temperature=0.8,
                    n=1
                )
                
                duration = time.time() - start_time
                
                if response and response.choices:
                    follow_question = response.choices[0].message.content.strip()
                    
                    # 清理可能的前缀
                    prefixes_to_remove = ["追问：", "追问:", "问：", "问:"]
                    for prefix in prefixes_to_remove:
                        if follow_question.startswith(prefix):
                            follow_question = follow_question[len(prefix):].strip()
                    
                    # 校验追问质量（移除字数限制）
                    preset_follows = topic.get("followups", [])
                    original_question = topic.get("questions", [""])[0]
                    
                    if (follow_question
                            and len(follow_question) >= 5  # 最小长度
                            and follow_question not in original_question
                            and follow_question not in preset_follows):
                        logger.log_api_call("generate_followup", True, duration)
                        return follow_question
                
                logger.log_api_call("generate_followup", True, duration, "生成内容不符合要求")
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
