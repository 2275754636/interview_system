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
        
        # 尝试加载已保存的配置
        self._load_config()
    
    def _load_config(self) -> bool:
        """从本地文件加载API配置"""
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
        if not self.is_available or not self.client:
            return None
        
        valid_answer = answer.strip()
        if len(valid_answer) < 2:
            return None
        
        topic_name = topic.get("name", "")
        prompt = f"""
        用户回答了{topic_name}的问题，回答是：{valid_answer}
        生成1个口语化追问（≤25字），满足：
        1. 不重复原问题，不使用"能结合具体经历说说吗？"这类通用表述；
        2. 针对回答中的具体细节（如事件、动作、感受）深挖；
        3. 引导用户补充未提及的细节（如困难、他人反应、收获）。
        示例：
        - 回答"小组作业主动统筹拿优秀"→追问"协调分工时队友有抵触吗？"
        - 回答"社区羽毛球赛和陌生人配合"→追问"配合失误时怎么沟通的？"
        """
        
        return self._call_with_retry(prompt, topic)
    
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
                        {"role": "system", "content": "只生成1个追问，简洁有针对性"},
                        {"role": "user", "content": prompt.strip()}
                    ],
                    max_tokens=50,
                    temperature=0.7,
                    n=1
                )
                
                duration = time.time() - start_time
                
                if response and response.choices:
                    follow_question = response.choices[0].message.content.strip()
                    
                    # 校验追问质量
                    preset_follows = topic.get("followups", [])
                    original_question = topic.get("questions", [""])[0]
                    
                    if (follow_question
                            and follow_question not in original_question
                            and follow_question not in preset_follows
                            and len(follow_question) <= 25):
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
