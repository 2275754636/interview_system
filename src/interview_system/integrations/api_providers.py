#!/usr/bin/env python3
# coding: utf-8
"""API Provider Configurations"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class APIProviderConfig:
    """API提供商配置"""
    name: str
    provider_id: str
    base_url: str
    default_model: str
    api_key_name: str
    need_secret_key: bool = False
    models: List[str] = field(default_factory=list)
    website: str = ""


API_PROVIDERS: Dict[str, APIProviderConfig] = {
    "deepseek": APIProviderConfig(
        name="DeepSeek (深度求索)",
        provider_id="deepseek",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        api_key_name="API Key",
        models=["deepseek-chat"],
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
