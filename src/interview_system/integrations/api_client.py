#!/usr/bin/env python3
# coding: utf-8
"""
Unified API Client - Multi-provider LLM support
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import interview_system.common.logger as logger
from interview_system.common.config import BASE_DIR
from interview_system.integrations.api_providers import API_PROVIDERS, APIProviderConfig
from interview_system.integrations.prompt_builder import PromptBuilder
from interview_system.integrations.response_parser import ResponseParser
from interview_system.integrations.prompt_templates import FOLLOWUP_SYSTEM_PROMPT

API_CONFIG_FILE = os.path.join(BASE_DIR, "api_config.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Token limits
MAX_FOLLOWUP_TOKENS = 120
TEST_CALL_TOKENS = 5


def _write_text_atomic(path: str, content: str) -> None:
    target = Path(path)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def migrate_json_to_env() -> bool:
    """Migrate api_config.json to .env file (one-time)"""
    if not os.path.exists(API_CONFIG_FILE):
        return False
    if os.path.exists(ENV_FILE):
        return False

    try:
        with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        env_lines = [
            "# API Configuration (migrated from api_config.json)",
            f"API_PROVIDER={data.get('provider_id', '')}",
            f"API_KEY={data.get('api_key', '')}",
            f"API_MODEL={data.get('model', '')}",
        ]
        if data.get("secret_key"):
            env_lines.append(f"API_SECRET_KEY={data.get('secret_key', '')}")

        _write_text_atomic(ENV_FILE, "\n".join(env_lines) + "\n")

        # Backup old file
        backup_path = API_CONFIG_FILE + ".bak"
        Path(API_CONFIG_FILE).replace(Path(backup_path))
        logger.info(f"已迁移配置到 .env，原文件备份为 {backup_path}")
        return True
    except Exception as e:
        logger.warning(f"迁移配置失败：{e}")
        return False


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
        """Load API config from env vars first, then file (backward compat)"""
        # Priority 1: Environment variables
        provider_id = os.getenv("API_PROVIDER")
        api_key = os.getenv("API_KEY")

        if provider_id and api_key and provider_id in API_PROVIDERS:
            self.current_provider = API_PROVIDERS[provider_id]
            self.api_key = api_key
            self.secret_key = os.getenv("API_SECRET_KEY")
            self.model = os.getenv("API_MODEL") or self.current_provider.default_model
            logger.info(f"已从环境变量加载API配置：{self.current_provider.name}")
            return True

        # Priority 2: JSON file (backward compat)
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
                logger.info(f"已从文件加载API配置：{self.current_provider.name}")
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
                client_kwargs["default_headers"] = {
                    "X-Bce-Signature-Key": self.secret_key
                }

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
        """Save API config to .env file"""
        if not self.current_provider or not self.api_key:
            return False

        try:
            env_lines = []

            # Read existing .env if present
            if os.path.exists(ENV_FILE):
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        # Skip API-related lines (will be rewritten)
                        if not line.strip().startswith(
                            (
                                "API_PROVIDER=",
                                "API_KEY=",
                                "API_MODEL=",
                                "API_SECRET_KEY=",
                            )
                        ):
                            env_lines.append(line.rstrip())

            # Add API config
            env_lines.extend(
                [
                    "",
                    "# API Configuration",
                    f"API_PROVIDER={self.current_provider.provider_id}",
                    f"API_KEY={self.api_key}",
                    f"API_MODEL={self.model}",
                ]
            )

            if self.current_provider.need_secret_key and self.secret_key:
                env_lines.append(f"API_SECRET_KEY={self.secret_key}")

            _write_text_atomic(ENV_FILE, "\n".join(env_lines) + "\n")

            logger.info(f"API配置已保存到：{ENV_FILE}")
            return True
        except Exception as e:
            logger.error(f"保存API配置失败：{e}")
            return False

    def clear_config(self):
        """Clear saved config from both .env and legacy JSON"""
        # Clear legacy JSON
        if os.path.exists(API_CONFIG_FILE):
            os.remove(API_CONFIG_FILE)

        # Clear API vars from .env
        if os.path.exists(ENV_FILE):
            try:
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    lines = [
                        line
                        for line in f
                        if not line.strip().startswith(
                            (
                                "API_PROVIDER=",
                                "API_KEY=",
                                "API_MODEL=",
                                "API_SECRET_KEY=",
                            )
                        )
                    ]
                _write_text_atomic(ENV_FILE, "".join(lines))
            except Exception as e:
                logger.warning(f"清除.env中API配置失败: {e}")

        logger.info("已清除API配置")

    def get_saved_provider(self) -> Optional[str]:
        """Get saved provider ID"""
        if self.current_provider:
            return self.current_provider.provider_id
        return None

    def initialize(
        self, provider_id: str, api_key: str, secret_key: str = None, model: str = None
    ) -> bool:
        """Initialize API client with credentials"""
        provider = self._validate_credentials(provider_id, api_key, secret_key)
        if not provider:
            return False

        client = self._create_client(provider, api_key, secret_key)
        if not client:
            return False

        target_model = model or provider.default_model
        if not self._test_connection(client, target_model, provider.name):
            self.clear_config()
            return False

        self._set_active_state(client, provider, api_key, secret_key, target_model)
        return True

    def _set_active_state(
        self, client, provider, api_key: str, secret_key: str, model: str
    ):
        """Set active client state"""
        self.client = client
        self.current_provider = provider
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self.is_available = True
        logger.info(f"{provider.name} 智能追问功能已启用，模型：{model}")

    def _validate_credentials(self, provider_id: str, api_key: str, secret_key: str):
        """Validate provider and credentials"""
        if provider_id not in API_PROVIDERS:
            logger.error(f"不支持的API提供商：{provider_id}")
            return None

        if not api_key:
            logger.warning("API Key 不能为空")
            return None

        provider = API_PROVIDERS[provider_id]
        if provider.need_secret_key and not secret_key:
            logger.warning(f"{provider.name} 需要 Secret Key")
            return None

        return provider

    def _create_client(self, provider, api_key: str, secret_key: str):
        """Create OpenAI client instance"""
        try:
            import openai
        except ImportError:
            logger.error("未安装 openai 库，请运行 `pip install openai>=1.0.0` 安装")
            return None

        try:
            client_kwargs = {
                "api_key": api_key,
                "base_url": provider.base_url,
                "timeout": self.timeout,
            }

            if provider.provider_id == "baidu" and secret_key:
                client_kwargs["default_headers"] = {"X-Bce-Signature-Key": secret_key}

            return openai.OpenAI(**client_kwargs)
        except Exception as e:
            logger.error(f"创建客户端失败：{e}")
            return None

    def _test_connection(self, client, model: str, provider_name: str) -> bool:
        """Test API connection with a simple call"""
        try:
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=TEST_CALL_TOKENS,
            )
            return True
        except Exception as e:
            logger.error(f"{provider_name} 配置失败：{e}")
            self.is_available = False
            return False

    def generate_followup(
        self, answer: str, topic: dict, conversation_log: list = None
    ) -> Optional[str]:
        """Generate intelligent followup question"""
        if not self.is_available and not self._lazy_initialized:
            self._lazy_init_client()

        if not self.is_available or not self.client:
            return None

        valid_answer = answer.strip()
        if len(valid_answer) < 2:
            return None

        prompt = PromptBuilder.build_followup_prompt(
            valid_answer, topic, conversation_log
        )
        return self._call_with_retry(prompt, topic)

    def _call_with_retry(self, prompt: str, topic: dict) -> Optional[str]:
        """API call with retry mechanism"""
        last_error = None

        for attempt in range(self.max_retries):
            start_time = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": FOLLOWUP_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt.strip()},
                    ],
                    max_tokens=MAX_FOLLOWUP_TOKENS,
                    temperature=0.7,
                    n=1,
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.log_api_call("generate_followup", True, elapsed_ms / 1000)
                logger.info(
                    f"API调用成功: {self.current_provider.name}",
                    extra={
                        "provider": self.current_provider.name,
                        "model": self.model,
                        "elapsed_ms": elapsed_ms,
                    },
                )
                return ResponseParser.extract_followup(
                    response, topic, elapsed_ms / 1000
                )

            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                last_error = str(e)
                logger.log_api_call(
                    "generate_followup",
                    False,
                    elapsed_ms / 1000,
                    f"第{attempt + 1}次尝试失败: {last_error[:50]}",
                )

                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.debug(f"等待 {wait_time:.1f}s 后重试...")
                    time.sleep(wait_time)

        logger.error(f"API调用失败，已重试{self.max_retries}次: {last_error}")
        return None
