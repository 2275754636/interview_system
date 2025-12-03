#!/usr/bin/env python3
# coding: utf-8
"""
API客户端模块 - 大学生五育并举访谈智能体
封装百度千帆API调用，包含重试机制
"""

import json
import os
import time
from typing import Optional, Tuple

import logger
from config import BAIDU_API_CONFIG, KEYS_FILE


class APIClient:
    """百度千帆API客户端"""
    
    def __init__(self):
        self.config = BAIDU_API_CONFIG
        self.client = None
        self.is_available = False
        self._load_keys()
    
    def _load_keys(self) -> Tuple[Optional[str], Optional[str]]:
        """从本地文件加载百度千帆密钥"""
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                access_key = data.get("access_key", "").strip()
                secret_key = data.get("secret_key", "").strip()
                if access_key and secret_key:
                    self.config.access_key = access_key
                    self.config.secret_key = secret_key
                    logger.info(f"已从本地加载百度千帆密钥（文件：{KEYS_FILE}）")
                    return access_key, secret_key
            except Exception as e:
                logger.warning(f"加载密钥失败：{str(e)[:30]}，将重新引导输入")
        return None, None
    
    def save_keys(self, access_key: str, secret_key: str) -> bool:
        """将百度千帆密钥保存到本地文件"""
        try:
            import datetime
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "access_key": access_key,
                    "secret_key": secret_key,
                    "saved_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"密钥已保存到本地文件：{KEYS_FILE}")
            return True
        except Exception as e:
            logger.error(f"保存密钥失败：{str(e)[:30]}")
            return False
    
    def initialize(self, access_key: str = None, secret_key: str = None) -> bool:
        """
        初始化API客户端
        
        Args:
            access_key: 百度千帆 Access Key（可选，优先使用传入的值）
            secret_key: 百度千帆 Secret Key（可选，优先使用传入的值）
            
        Returns:
            是否初始化成功
        """
        try:
            import openai
            from openai import OpenAIError
        except ImportError:
            logger.error("未安装 openai 库，请运行 `pip install openai>=1.0.0` 安装")
            return False
        
        # 使用传入的密钥或已加载的密钥
        ak = access_key or self.config.access_key
        sk = secret_key or self.config.secret_key
        
        if not ak or not sk:
            logger.warning("密钥不完整，无法初始化API客户端")
            return False
        
        try:
            # 初始化百度千帆客户端（兼容OpenAI SDK）
            self.client = openai.OpenAI(
                api_key=ak,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                default_headers={"X-Bce-Signature-Key": sk}
            )
            
            # 轻量测试调用（验证密钥和网络）
            self.client.models.list()
            
            self.is_available = True
            self.config.access_key = ak
            self.config.secret_key = sk
            
            logger.info("百度千帆智能追问功能已启用")
            return True
            
        except Exception as e:
            logger.error(f"百度千帆配置失败：{str(e)}")
            self.is_available = False
            # 配置失败时删除无效密钥文件
            if os.path.exists(KEYS_FILE):
                os.remove(KEYS_FILE)
                logger.warning("已删除无效的本地密钥文件")
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
        
        for attempt in range(self.config.max_retries):
            start_time = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
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
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)  # 指数退避
                    logger.debug(f"等待 {wait_time:.1f}s 后重试...")
                    time.sleep(wait_time)
        
        logger.error(f"API调用失败，已重试{self.config.max_retries}次: {last_error}")
        return None


# ----------------------------
# 全局API客户端实例
# ----------------------------
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """获取全局API客户端实例"""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def initialize_api(access_key: str = None, secret_key: str = None) -> bool:
    """初始化全局API客户端"""
    return get_api_client().initialize(access_key, secret_key)


def generate_followup(answer: str, topic: dict, conversation_log: list = None) -> Optional[str]:
    """生成智能追问（便捷函数）"""
    return get_api_client().generate_followup(answer, topic, conversation_log)


def is_api_available() -> bool:
    """检查API是否可用"""
    return get_api_client().is_available
